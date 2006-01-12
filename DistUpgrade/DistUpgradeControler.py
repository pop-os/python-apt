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

from UpdateManager.Common.SimpleGladeApp import SimpleGladeApp
from SoftwareProperties.aptsources import SourcesList, SourceEntry
from gettext import gettext as _


class MyCache(apt.Cache):
    # init
    def __init__(self, progress=None):
        apt.Cache.__init__(self, progress)
        self.to_install = []
        self.to_remove = []
        # turn on debuging
        apt_pkg.Config.Set("Debug::pkgProblemResolver","true")
        fd = os.open(os.path.expanduser("~/dist-upgrade-apt.log"), os.O_RDWR|os.O_CREAT|os.O_TRUNC)
        os.dup2(fd,1)
        os.dup2(fd,2)
        
    # properties
    @property
    def requiredDownload(self):
        pm = apt_pkg.GetPackageManager(self._depcache)
        fetcher = apt_pkg.GetAcquire()
        pm.GetArchives(fetcher, self._list, self._records)
        return fetcher.FetchNeeded
    @property
    def isBroken(self):
        return self._depcache.BrokenCount > 0

    # methods
    def downloadable(self, pkg, useCandidate=True):
        " check if the given pkg can be downloaded "
        if useCandidate:
            ver = self._depcache.GetCandidateVer(pkg._pkg)
        else:
            ver = pkg._pkg.CurrentVer
        if ver == None:
            return False
        return ver.Downloadable
    def fixBroken(self):
        """ try to fix broken dependencies on the system, may throw
            SystemError when it can't"""
        return self._depcache.FixBroken()
    def create_snapshot(self):
        """ create a snapshot of the current changes """
        self.to_install = []
        self.to_remove = []
        for pkg in self.getChanges():
            if pkg.markedInstall or pkg.markedUpgrade:
                self.to_install.append(pkg.name)
            if pkg.markedDelete:
                self.to_remove.append(pkg.name)
    def restore_snapshot(self):
        """ restore a snapshot """
        for pkg in self:
            pkg.markKeep()
        for name in self.to_remove:
            pkg = self[name]
            pkg.markDelete()
        for name in self.to_install:
            pkg = self[name]
            pkg.markInstall()
            

class DistUpgradeControler(object):
    def __init__(self, distUpgradeView):
        self._view = distUpgradeView
        self._view.updateStatus(_("Reading cache"))
        self.cache = None

        # some constants here
        self.fromDist = "hoary"
        self.toDist = "breezy"
        #self.fromDist = "breezy"
        #self.toDist = "dapper"
        
        self.origin = "Ubuntu"

        # a list of missing pkg names in the current install that neesd to
        # be added before the dist-upgrade (e.g. missing ubuntu-desktop)
        self.missing_pkgs = []

        # a list of regexp that are not allowed to be removed
        self.removal_blacklist = []
        for line in open("removal_blacklist.txt").readlines():
            line = line.strip()
            if not line == "" or line.startswith("#"):
                self.removal_blacklist.append(line)

    def openCache(self):
        self.cache = MyCache(self._view.getOpCacheProgress())

    def sanityCheck(self):
        if self.cache.isBroken:
            try:
                logging.debug("Have broken pkgs, trying to fix them")
                self.cache.fixBroken()
            except SystemError:
                self._view.error(_("Broken packages"),
                                 _("Your system contains broken packages "
                                   "that couldn't be fixed with this "
                                   "software. "
                                   "Please fix them first using synaptic or "
                                   "apt-get before proceeding."))
                return False

        # now check for ubuntu-base
        if not self.cache.has_key("ubuntu-base") or \
               not self.cache["ubuntu-base"].isInstalled:
            self.missing_pkgs.append("ubuntu-base")

        # now check for ubuntu-desktop, kubuntu-desktop, edubuntu-desktop
        metapkgs = {"ubuntu-desktop": ["gdm","gnome-panel", "ubuntu-artwork"],
                    "kubuntu-desktop": ["kdm", "kicker",
                                        "kubuntu-artwork-usplash"],
                    "edubuntu-desktop": ["edubuntu-artwork", "tuxpaint"]
                    }
        # helper
        def metaPkgInstalled():
            metapkg_found = False
            for key in metapkgs:
                if self.cache.has_key(key) and (self.cache[key].isInstalled or self.cache[key].markedInstall):
                    metapkg_found=True
            return metapkg_found
        # check if we have a meta-pkg, if not, try to guess which one to pick
        if not metaPkgInstalled():
            logging.debug("no {ubuntu,edubuntu,kubuntu}-desktop pkg installed")
            for key in metapkgs:
                deps_found = True
                for pkg in metapkgs[key]:
                    deps_found &= self.cache.has_key(pkg) and self.cache[pkg].isInstalled
                if deps_found:
                    logging.debug("guessing '%s' as missing meta-pkg" % key)
                    self.missing_pkgs.append(key)
        # check if we actually found one
        if not metaPkgInstalled() and len(self.missing_pkgs) == 0:
            # FIXME: provide a list
            self._view.error(_("Can't guess meta-package"),
                                 _("Your system does not contain a "
                                   "ubuntu-desktop, kubuntu-desktop or "
                                   "edubuntu-desktop package and it was not "
                                   "possible to detect which version of "
                                   "ubuntu you are runing.\n "
                                   "Please install one of the packages "
                                   "above first using synaptic or "
                                   "apt-get before proceeding."))
            return False
            
        # FIXME: check for ubuntu-desktop, kubuntu-dekstop, edubuntu-desktop
        return True

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

    def _getObsoletesPkgs(self):
        " get all package names that are not downloadable "
        obsolete_pkgs =set()        
        for pkg in self.cache:
            if pkg.isInstalled:
                if not self.cache.downloadable(pkg):
                    obsolete_pkgs.add(pkg.name)
        return obsolete_pkgs

    def _getForeignPkgs(self):
        """ get all packages that are installed from a foreign repo
            (and are actually downloadable)
        """
        foreign_pkgs =set()        
        for pkg in self.cache:
            if pkg.isInstalled and self.cache.downloadable(pkg):
                # assume it is foreign and see if it is from the 
                # official archive
                foreign=True
                for origin in pkg.candidateOrigin:
                    if self.fromDist in origin.archive and \
                           origin.origin == self.origin:
                        foreign = False
                    if self.toDist in origin.archive and \
                           origin.origin == self.origin:
                        foreign = False
                if foreign:
                    foreign_pkgs.add(pkg.name)
        return foreign_pkgs

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
        self.obsolete_pkgs = self._getObsoletesPkgs()
        self.foreign_pkgs = self._getForeignPkgs()
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
        try:
            # upgrade (and make sure this way that the cache is ok)
            self.cache.upgrade(True)
            # then add missing pkgs (like {ubuntu,kubuntu,edubuntu}-desktop)
            for pkg in self.missing_pkgs:
                logging.debug("Installing missing pkg: %s" % pkg)
                self.cache[pkg].markInstall()
        except SystemError, e:
            # FIXME: change the text to something more useful
            self._view.error(_("Could not calculate the upgrade"),
                             _("A unresolvable problem occured while "
                               "calculating the upgrade. Please report "
                               "this as a bug. "))
            logging.debug("Dist-upgrade failed: '%s'", e)
            return False
        
        # now do some sanity checking, 
        try:
            #are all missing_pkgs really installed?
            for pkgname in self.missing_pkgs:
                pkg = self.cache[pkgname]
                if not (pkg.markedInstall or pkg.markedUpgrade):
                    logging.error("Missing pkg '%s' not installed after upgrade" % pkgname)
                    raise AssertionError
            # do we still have ubuntu-base?
            pkg = self.cache["ubuntu-base"]
            if not (pkg.markedInstall or pkg.markedUpgrade or pkg.markedKeep):
                logging.error("No ubuntu-base installed after upgrade")
                raise AssertionError
            # one desktop package?
            found = False
            for n in ["ubuntu-desktop","kubuntu-desktop","edubuntu-desktop"]:
                pkg = self.cache[n]
                if pkg.markedKeep or pkg.markedInstall or pkg.markedUpgrade:
                    found = True
            if not found:
                logging.error("No dekstop pkg installed after upgrade")
                raise AssertionError
        except AssertionError:
            self._view.error(_("Could not calculate the upgrade"),
                             _("After calculation the upgrade one of the "
                               "essential packages can't be upgraded or "
                               "installed. Please report this as a bug. "))
            return False
                
        changes = self.cache.getChanges()
        # log the changes for debuging
        self._logChanges()
        # ask the user if he wants to do the changes
        res = self._view.confirmChanges(_("Perform Upgrade?"),changes,
                                        self.cache.requiredDownload)
        return res

    def doDistUpgrade(self):
        fprogress = self._view.getFetchProgress()
        iprogress = self._view.getInstallProgress()
        try:
            res = self.cache.commit(fprogress,iprogress)
        except IOError, e:
            self._view.error(_("Error during commit"),
                             _("Some problem occured during the upgrade. "
                               "This is mostly a network problem, please "
                               "check the network and try again. "),
                             "%s" % e)
            return False
        return True

    def _inRemovalBlacklist(self, pkgname):
        for expr in self.removal_blacklist:
            if re.compile(expr).match(pkgname):
                return True
        return False

    def _tryMarkObsoleteForRemoval(self, pkgname, remove_candidates):
        # this is a delete candidate, only actually delete,
        # if it dosn't remove other packages depending on it
        # that are not obsolete as well
        self.cache.create_snapshot()
        self.cache[pkgname].markDelete()
        for pkg in self.cache.getChanges():
            if pkg.name not in remove_candidates or \
                   pkg.name in self.foreign_pkgs or \
                   pkg.name in self._inRemovalBlacklist(pkg.name):
                self.cache.restore_snapshot()
                return False
        return True

    def doPostUpgrade(self):
        self.openCache()
        # check out what packages are cruft now
        # use self.{foreign,obsolete}_pkgs here and see what changed
        now_obsolete = self._getObsoletesPkgs()
        now_foreign = self._getForeignPkgs()
        logging.debug("Obsolete: %s" % " ".join(now_obsolete))
        logging.debug("Foreign: %s" % " ".join(now_foreign))
        
        # mark packages that are now obsolete (and where not obsolete
        # before) to be deleted. make sure to not delete any foreign
        # (that is, not from ubuntu) packages
        remove_candidates = now_obsolete - self.obsolete_pkgs
        logging.debug("Start checking for obsolete pkgs")
        for pkgname in remove_candidates:
            if pkgname not in self.foreign_pkgs:
                if not self._tryMarkObsoleteForRemoval(pkgname,
                                                       remove_candidates):
                    logging.debug("'%s' scheduled for remove but not in remove_candiates, skipping", pkg.name)
        logging.debug("Finish checking for obsolete pkgs")
        changes = self.cache.getChanges()
        if len(changes) > 0 and \
               self._view.confirmChanges(_("Remove obsolete Packages?"),
                                         changes, 0):
            fprogress = self._view.getFetchProgress()
            iprogress = self._view.getInstallProgress()
            self.cache.commit(fprogress,iprogress)
            
    def askForReboot(self):
        return self._view.askYesNoQuestion(_("Reboot required"),
                                           _("The upgrade is finished now. "
                                             "A reboot is required to "
                                             "now, do you want to do this "
                                             "now?"))

    def abort(self):
        """ abort the upgrade, cleanup (as much as possible) """
        self.sources.restoreBackup(self.sources_backup_ext)
        sys.exit(1)

    
    # this is the core
    def breezyUpgrade(self):
        # sanity check (check for ubuntu-desktop, brokenCache etc)
        self._view.updateStatus(_("Checking the system"))
        self._view.setStep(1)
        self.openCache()
        if not self.sanityCheck():
            sys.exit(1)

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
        self._view.updateStatus(_("Reading cache"))
        self.openCache()

        # calc the dist-upgrade and see if the removals are ok/expected
        # do the dist-upgrade
        self._view.setStep(3)
        self._view.updateStatus(_("Performing the upgrade"))
        if not self.askDistUpgrade():
            self.abort()
            
        if not self.doDistUpgrade():
            self.abort()
            
        # do post-upgrade stuff
        self._view.setStep(4)
        self.doPostUpgrade()

        # done, ask for reboot
        if self.askForReboot():
            subprocess.call(["reboot"])
        
    def run(self):
        self.breezyUpgrade()


