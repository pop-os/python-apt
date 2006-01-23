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

from UpdateManager.Common.SimpleGladeApp import SimpleGladeApp
from SoftwareProperties.aptsources import SourcesList, SourceEntry
from gettext import gettext as _
from DistUpgradeCache import MyCache

            

class DistUpgradeControler(object):
    def __init__(self, distUpgradeView):
        self._view = distUpgradeView
        self._view.updateStatus(_("Reading cache"))
        self.cache = None

        # some constants here
        #self.fromDist = "hoary"
        #self.toDist = "breezy"
        self.fromDist = "breezy"
        self.toDist = "dapper"
       
        self.origin = "Ubuntu"

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
        valid_mirrors = ["http://archive.ubuntu.com/ubuntu",
                         "http://security.ubuntu.com/ubuntu"]

        # look over the stuff we have
        foundToDist = False
        for entry in self.sources:
            # check if it's a mirror (or offical site)
            for mirror in valid_mirrors:
                if self.sources.is_mirror(mirror,entry.uri):
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
                else:
                    # disable non-official entries that point to dist
                    if entry.dist == self.fromDist:
                        entry.disabled = True

        if not foundToDist:
            # FIXME: offer to write a new self.sources.list entry
            return self._view.error(_("No valid entry found"),
                                    _("While scaning your repository "
                                      "information no valid entry for "
                                      "the upgrade was found.\n"))
        
        # write (well, backup first ;) !
        self.sources_backup_ext = ".distUpgrade"
        self.sources.backup(self.sources_backup_ext)
        self.sources.save()

        # re-check if the written self.sources are valid, if not revert and
        # bail out
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
        try:
            res = self.cache.update(progress)
        except IOError, e:
            self._view.error(_("Error during update"),
                             _("A problem occured during the update. "
                               "This is usually some sort of network "
                               "problem, please check your network "
                               "connection and retry."),
                             "%s" % e)
            return False
        return True

    def askDistUpgrade(self):
        if not self.cache.distUpgrade(self._view):
            return False
        changes = self.cache.getChanges()
        # log the changes for debuging
        self._logChanges()
        # ask the user if he wants to do the changes
        archivedir = apt_pkg.Config.FindDir("Dir::Cache::archives ")
        st = os.statvfs(archivedir)
        free = st[statvfs.F_BAVAIL]*st[statvfs.F_FRSIZE]
        if self.cache.requiredDownload > free:
            self._view.error(_("Not enough free space"),
                             _("There is not enough free space on your "
                               "system to download the required pacakges. "
                               "Please free some space before trying again "
                               "with e.g. 'sudo apt-get clean'"))
            return False                             
        res = self._view.confirmChanges(_("Perform Upgrade?"),changes,
                                        self.cache.requiredDownload)
        return res

    def doDistUpgrade(self):
        fprogress = self._view.getFetchProgress()
        iprogress = self._view.getInstallProgress()
        try:
            res = self.cache.commit(fprogress,iprogress)
        except (SystemError, IOError), e:
            self._view.error(_("Error during commit"),
                             _("Some problem occured during the upgrade. "
                               "This is mostly a network problem, please "
                               "check the network and try again. "),
                             "%s" % e)
            return False
        return True


    def doPostUpgrade(self):
        self.openCache()
        # check out what packages are cruft now
        # use self.{foreign,obsolete}_pkgs here and see what changed
        now_obsolete = self.cache._getObsoletesPkgs()
        now_foreign = self.cache._getForeignPkgs(self.origin, self.fromDist, self.toDist)
        logging.debug("Obsolete: %s" % " ".join(now_obsolete))
        logging.debug("Foreign: %s" % " ".join(now_foreign))
        
        # mark packages that are now obsolete (and where not obsolete
        # before) to be deleted. make sure to not delete any foreign
        # (that is, not from ubuntu) packages
        remove_candidates = now_obsolete - self.obsolete_pkgs
        logging.debug("Start checking for obsolete pkgs")
        for pkgname in remove_candidates:
            if pkgname not in self.foreign_pkgs:
                if not self.cache._tryMarkObsoleteForRemoval(pkgname, remove_candidates, self.foreign_pkgs):
                    logging.debug("'%s' scheduled for remove but not in remove_candiates, skipping", pkgname)
        logging.debug("Finish checking for obsolete pkgs")
        changes = self.cache.getChanges()
        if len(changes) > 0 and \
               self._view.confirmChanges(_("Remove obsolete Packages?"),
                                         changes, 0):
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
            self.cache.commit(fprogress,iprogress)
            
    def abort(self):
        """ abort the upgrade, cleanup (as much as possible) """
        self.sources.restoreBackup(self.sources_backup_ext)
        sys.exit(1)

    
    # this is the core
    def dapperUpgrade(self):
        # sanity check (check for ubuntu-desktop, brokenCache etc)
        self._view.updateStatus(_("Checking update system"))
        self._view.setStep(1)
        self.openCache()
        if not self.cache.sanityCheck(self._view):
            abort(1)

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
        self._view.updateStatus(_("Checking update system"))
        self.openCache()

        # calc the dist-upgrade and see if the removals are ok/expected
        # do the dist-upgrade
        self._view.setStep(3)
        self._view.updateStatus(_("Asking for confirmation"))
        if not self.askDistUpgrade():
            self.abort()

        self._view.updateStatus(_("Performing the upgrade"))            
        if not self.doDistUpgrade():
            self.abort()
            
        # do post-upgrade stuff
        self._view.setStep(4)
        self.doPostUpgrade()

        # done, ask for reboot
        if self._view.confirmRestart():
            subprocess.call(["reboot"])
        
    def run(self):
        self.dapperUpgrade()


