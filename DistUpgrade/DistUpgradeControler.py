# DistUpgradeControler.py 
#  
#  Copyright (c) 2004,2005 Canonical
#  
#  Author: Michael Vogt <michael.vogt@ubuntu.com>
# 
#  This program is free software; you can redistribute it and/or 
#  modify it under the terms of the GNU General Public License as 
#  published by the Free Software Foundation; either version 2 of the
#  License, or (at your option) any later version.
# 
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
# 
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
#  USA


import apt
import apt_pkg
import sys
import os
import subprocess
import logging
import re
import statvfs
from DistUpgradeConfigParser import DistUpgradeConfig

from SoftwareProperties.aptsources import SourcesList, SourceEntry
from gettext import gettext as _
from DistUpgradeCache import MyCache

            

class DistUpgradeControler(object):
    def __init__(self, distUpgradeView):
        self._view = distUpgradeView
        self._view.updateStatus(_("Reading cache"))
        self.cache = None

        self.config = DistUpgradeConfig()
        self.sources_backup_ext = "."+self.config.get("Files","BackupExt")
        
        # some constants here
        self.fromDist = self.config.get("Sources","From")
        self.toDist = self.config.get("Sources","To")
        self.origin = self.config.get("Sources","ValidOrigin")

        # forced obsoletes
        self.forced_obsoletes = self.config.getlist("Distro","ForcedObsoletes")

    def openCache(self):
        self.cache = MyCache(self._view.getOpCacheProgress())


    def updateSourcesList(self):
        self.sources = SourcesList()

        # this must map, i.e. second in "from" must be the second in "to"
        # (but they can be different, so in theory we could exchange
        #  component names here)
        fromDists = [self.fromDist,
                     self.fromDist+"-security",
                     self.fromDist+"-updates",
                     self.fromDist+"-backports"
                    ]
        toDists = [self.toDist,
                   self.toDist+"-security",
                   self.toDist+"-updates",
                   self.toDist+"-backports"
                   ]

        # list of valid mirrors that we can add
        valid_mirrors = self.config.getlist("Sources","ValidMirrors")

        # look over the stuff we have
        foundToDist = False
        for entry in self.sources:
            # check if it's a mirror (or offical site)
            validMirror = False
            for mirror in valid_mirrors:
                if self.sources.is_mirror(mirror,entry.uri):
                    validMirror = True
                    if entry.dist in toDists:
                        # so the self.sources.list is already set to the new
                        # distro
                        foundToDist = True
                    elif entry.dist in fromDists:
                        foundToDist = True
                        entry.dist = toDists[fromDists.index(entry.dist)]
                    else:
                        # disable all entries that are official but don't
                        # point to the "from" dist
                        entry.disabled = True
                    # it can only be one valid mirror, so we can break here
                    break
            # disable anything that is not from a official mirror
            if not validMirror:
                entry.disabled = True

        if not foundToDist:
            # FIXME: offer to write a new self.sources.list entry
            return self._view.error(_("No valid entry found"),
                                    _("While scaning your repository "
                                      "information no valid entry for "
                                      "the upgrade was found.\n"))
        
        # write (well, backup first ;) !
        self.sources.backup(self.sources_backup_ext)
        self.sources.save()

        # re-check if the written self.sources are valid, if not revert and
        # bail out
        # TODO: check if some main packages are still available or if we
        #       accidently shot them, if not, maybe offer to write a standard
        #       sources.list?
        try:
            sourceslist = apt_pkg.GetPkgSourceList()
            sourceslist.ReadMainList()
        except SystemError:
            self._view.error(_("Repository information invalid"),
                             _("Upgrading the repository information "
                               "resulted in a invalid file. Please "
                               "report this as a bug."))
            return False
        return True

    def _logChanges(self):
        # debuging output
        logging.debug("About to apply the following changes")
        inst = []
        up = []
        rm = []
        for pkg in self.cache:
            if pkg.markedInstall: inst.append(pkg.name)
            elif pkg.markedUpgrade: up.append(pkg.name)
            elif pkg.markedDelete: rm.append(pkg.name)
        logging.debug("Remove: %s" % " ".join(rm))
        logging.debug("Install: %s" % " ".join(inst))
        logging.debug("Upgrade: %s" % " ".join(up))

    def doPreUpdate(self):
        # FIXME: check out what packages are downloadable etc to
        # compare the list after the update again
        self.obsolete_pkgs = self.cache._getObsoletesPkgs()
        self.foreign_pkgs = self.cache._getForeignPkgs(self.origin, self.fromDist, self.toDist)
        logging.debug("Foreign: %s" % " ".join(self.foreign_pkgs))
        logging.debug("Obsolete: %s" % " ".join(self.obsolete_pkgs))

    def doUpdate(self):
        self.cache._list.ReadMainList()
        progress = self._view.getFetchProgress()
        # FIXME: retry here too? just like the DoDistUpgrade?
        #        also remove all files from the lists partial dir!
        currentRetry = 0
        maxRetries = int(self.config.get("Network","MaxRetries"))
        while currentRetry < maxRetries:
            try:
                res = self.cache.update(progress)
            except IOError, e:
                logging.error("IOError in cache.update(): '%s'. Retrying (currentRetry: %s)" % (e,currentRetry))
                currentRetry += 1
                continue
            # no exception, so all was fine, we are done
            return True
                
        self._view.error(_("Error during update"),
                         _("A problem occured during the update. "
                           "This is usually some sort of network "
                           "problem, please check your network "
                           "connection and retry."), "%s" % e)
        return False


    def askDistUpgrade(self):
        if not self.cache.distUpgrade(self._view):
            return False
        changes = self.cache.getChanges()
        # log the changes for debuging
        self._logChanges()
        # ask the user if he wants to do the changes
        archivedir = apt_pkg.Config.FindDir("Dir::Cache::archives")
        st = os.statvfs(archivedir)
        free = st[statvfs.F_BAVAIL]*st[statvfs.F_FRSIZE]
        if self.cache.requiredDownload > free:
            free_at_least = apt_pkg.SizeToStr(self.cache.requiredDownload-free)
            self._view.error(_("Not enough free disk space"),
                             _("The upgrade aborts now. "
                               "Please free at least %s of disk space. "
                               "Empty your trash and remove temporary "
                               "packages of former installations using "
                               "'sudo apt-get clean'." % free_at_least ))
            return False
        res = self._view.confirmChanges(_("Do you want to start the upgrade?"),
                                        changes,
                                        self.cache.requiredDownload)
        return res

    def doDistUpgrade(self):
        currentRetry = 0
        fprogress = self._view.getFetchProgress()
        iprogress = self._view.getInstallProgress()
        # retry the fetching in case of errors
        maxRetries = int(self.config.get("Network","MaxRetries"))
        while currentRetry < maxRetries:
            try:
                res = self.cache.commit(fprogress,iprogress)
            except SystemError, e:
                # installing the packages failed, can't be retried
                self._view.error(_("Could not install the upgrades"),
                                 _("The upgrade aborts now. Your system "
                                   "can be in an unusable state. Please "
                                   "try 'sudo apt-get install -f' or Synaptic "
                                   "to fix your system."), "%s" % e)
                return False
            except IOError, e:
                # fetch failed, will be retried
                logging.error("IOError in cache.commit(): '%s'. Retrying (currentTry: %s)" % (e,currentRetry))
                currentRetry += 1
                continue
            # no exception, so all was fine, we are done
            return True
        
        # maximum fetch-retries reached without a successful commit
        logging.debug("giving up on fetching after maximum retries")
        self._view.error(_("Could not download the upgrades"),
                         _("The upgrade aborts now. Please check your "\
                           "internet connection or "\
                           "installation media and try again. "),
                           "%s" % e)
        # abort here because we want our sources.list back
        self.abort()



    def doPostUpgrade(self):
        self.openCache()
        # check out what packages are cruft now
        # use self.{foreign,obsolete}_pkgs here and see what changed
        now_obsolete = self.cache._getObsoletesPkgs()
        now_foreign = self.cache._getForeignPkgs(self.origin, self.fromDist, self.toDist)
        logging.debug("Obsolete: %s" % " ".join(now_obsolete))
        logging.debug("Foreign: %s" % " ".join(now_foreign))

        # now get the meta-pkg specific obsoletes and purges
        for pkg in self.config.getlist("Distro","MetaPkgs"):
            if self.cache.has_key(pkg) and self.cache[pkg].isInstalled:
                self.forced_obsoletes.extend(self.config.getlist(pkg,"ForcedObsoletes"))
        logging.debug("forced_obsoletes: %s", self.forced_obsoletes)

                
       
        # mark packages that are now obsolete (and where not obsolete
        # before) to be deleted. make sure to not delete any foreign
        # (that is, not from ubuntu) packages
        remove_candidates = now_obsolete - self.obsolete_pkgs
        remove_candidates |= set(self.forced_obsoletes)
        logging.debug("remove_candidates: '%s'" % remove_candidates)
        logging.debug("Start checking for obsolete pkgs")
        for pkgname in remove_candidates:
            if pkgname not in self.foreign_pkgs:
                if not self.cache._tryMarkObsoleteForRemoval(pkgname, remove_candidates, self.foreign_pkgs):
                    logging.debug("'%s' scheduled for remove but not in remove_candiates, skipping", pkgname)
        logging.debug("Finish checking for obsolete pkgs")

        # get changes
        changes = self.cache.getChanges()
        logging.debug("The following packages are remove candidates: %s" % " ".join([pkg.name for pkg in changes]))
        summary = _("Remove obsolete packages?")
        actions = [_("_Skip This Step"), _("_Remove")]
        # FIXME Add an explanation about what obsolete pacages are
        #explanation = _("")
        if len(changes) > 0 and \
               self._view.confirmChanges(summary, changes, 0, actions):
            fprogress = self._view.getFetchProgress()
            iprogress = self._view.getInstallProgress()
            try:
                res = self.cache.commit(fprogress,iprogress)
            except (SystemError, IOError), e:
                self._view.error(_("Error during commit"),
                                 _("Some problem occured during the clean-up. "
                                   "Please see the below message for more "
                                   "information. "),
                                   "%s" % e)
            
    def abort(self):
        """ abort the upgrade, cleanup (as much as possible) """
        self.sources.restoreBackup(self.sources_backup_ext)
        sys.exit(1)

    
    # this is the core
    def dapperUpgrade(self):
        # sanity check (check for ubuntu-desktop, brokenCache etc)
        self._view.updateStatus(_("Checking package manager"))
        self._view.setStep(1)
        self.openCache()
        
        if not self.cache.sanityCheck(self._view):
            abort(1)

        # run a "apt-get update" now
        if not self.doUpdate():
            self.abort()

        # do pre-upgrade stuff (calc list of obsolete pkgs etc)
        self.doPreUpdate()

        # update sources.list
        self._view.setStep(2)
        self._view.updateStatus(_("Updating repository information"))
        if not self.updateSourcesList():
            self.abort()
        # then update the package index files
        if not self.doUpdate():
            self.abort()

        # then open the cache (again)
        self._view.updateStatus(_("Checking package manager"))
        self.openCache()

        # calc the dist-upgrade and see if the removals are ok/expected
        # do the dist-upgrade
        self._view.setStep(3)
        self._view.updateStatus(_("Asking for confirmation"))
        if not self.askDistUpgrade():
            self.abort()

        self._view.updateStatus(_("Upgrading"))            
        if not self.doDistUpgrade():
            # don't abort here, because it would restore the sources.list
            sys.exit(1) 
            
        # do post-upgrade stuff
        self._view.setStep(4)
        self._view.updateStatus(_("Searching for obsolete software"))
        self.doPostUpgrade()

        # done, ask for reboot
        self._view.setStep(5)
        self._view.updateStatus(_("System upgrade is complete."))            
        # FIXME should we look into /var/run/reboot-required here?
        if self._view.confirmRestart():
            subprocess.call(["reboot"])
        
    def run(self):
        self.dapperUpgrade()


