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
        # turn on debuging
        apt.Config.Set("Debug::pkgProblemResolver","true")
        fd = os.open(os.path.expanduser("~/dist-upgrade-apt.log", os.O_RDWR|os.O_CREAT)
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

class DistUpgradeControler(object):
    def __init__(self, distUpgradeView):
        self._view = distUpgradeView
        self._view.updateStatus(_("Reading cache"))
        self.cache = None

        # some constants here
        self.fromDist = "hoary"
        self.toDist = "breezy"
        self.origin = "Ubuntu"

        # a list of missing pkg names in the current install that neesd to
        # be added before the dist-upgrade (e.g. missing ubuntu-desktop)
        self.missing_pkgs = []

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
                    try:
                        self.cache[key].markInstall()
                        self.missing_pkgs.append(key)
                        break
                    except SystemError:
                        pass
        # check if we actually found one
        if not metaPkgInstalled():
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
        sources = SourcesList()

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
        for entry in sources:
            # check if it's a mirror (or offical site)
            for mirror in valid_mirrors:
                if sources.is_mirror(mirror,entry.uri):
                    if entry.dist in toDists:
                        # so the sources.list is already set to the new
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
            # FIXME: offer to write a new sources.list entry
            return self._view.error(_("No valid entry found"),
                                    _("While scaning your repository "
                                      "information no valid entry for "
                                      "the upgrade was found.\n"))
        
        # write (well, backup first ;) !
        backup_ext = ".distUpgrade"
        sources.backup(backup_ext)
        sources.save()

        # re-check if the written sources are valid, if not revert and
        # bail out
        try:
            sourceslist = apt_pkg.GetPkgSourceList()
            sourceslist.ReadMainList()
        except SystemError:
            sources.restoreBackup(backup_ext)
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

    def doPreUpgrade(self):
        # FIXME: check out what packages are downloadable etc to
        # compare the list after the update again
        self.obsolete_pkgs = self._getObsoletesPkgs()
        self.foreign_pkgs = self._getForeignPkgs()
        logging.debug("Foreign: %s" % " ".join(self.foreign_pkgs))
        logging.debug("Obsolete: %s" % " ".join(self.obsolete_pkgs))

    def doUpdate(self):
        self.cache._list.ReadMainList()
        progress = self._view.getFetchProgress()
        self.cache.update(progress)

    def askDistUpgrade(self):
        try:
            # upgrade (and make sure this way that the cache is ok)
            self.cache.upgrade(True)
            # then add missing pkgs (like {ubuntu,kubuntu,edubuntu}-desktop)
            for pkg in self.missing_pkgs:
                logging.debug("Installing missing pkg: %s" % pkg)
                self.cache[pkg].markInstall()
        except SystemError:
            # FIXME: change the text to something more useful
            return self._view.error(_("Could not calculate the upgrade"),
                                    _("A unresolvable problem occured while "
                                      "calculating the upgrade. Please report "
                                      "this as a bug. "))
        changes = self.cache.getChanges()
        # debuging output
        logging.debug("About to apply the following changes")
        for pkg in caches:
            if cache[pkg].markedInstall: logging.debug("Inst: %s" % pkg.name)
            elif cache[pkg].markedUpgrade: logging.debug("Up: %s" % pkg.name)
            elif cache[pkg].markedDelete: logging.debug("Del: %s" % pkg.name)
        # ask the user if he wants to do the changes
        res = self._view.confirmChanges(changes,self.cache.requiredDownload)
        return res

    def doDistUpgrade(self):
        fprogress = self._view.getFetchProgress()
        iprogress = self._view.getInstallProgress()
        self.cache.commit(fprogress,iprogress)

    def doPostUpgrade(self):
        # FIXME: check out what packages are cruft now
        # use self.{foreign,obsolete}_pkgs here and see what changed
        pass

    def askForReboot(self):
        return self._view.askYesNoQuestion(_("Reboot required"),
                                           _("The upgrade is finished now. "
                                             "A reboot is required to "
                                             "now, do you want to do this "
                                             "now?"))
    
    # this is the core
    def breezyUpgrade(self):
        # sanity check (check for ubuntu-desktop, brokenCache etc)
        self._view.updateStatus(_("Checking the system"))
        self._view.setStep(1)
        self.openCache()
        if not self.sanityCheck():
            sys.exit(1)

        # do pre-upgrade stuff (calc list of obsolete pkgs etc)
        self.doPreUpgrade()

        # update sources.list
        self._view.setStep(2)
        self._view.updateStatus(_("Updating repository information"))
        if not self.updateSourcesList():
            sys.exit(1)
        # then update the package index files
        self.doUpdate()

        # then open the cache (again)
        self._view.updateStatus(_("Reading cache"))
        self.openCache()

        # calc the dist-upgrade and see if the removals are ok/expected
        # do the dist-upgrade
        self._view.setStep(3)
        self._view.updateStatus(_("Performing the upgrade"))
        if not self.askDistUpgrade():
            sys.exit(1)
        self.doDistUpgrade()
            
        # do post-upgrade stuff
        self._view.setStep(4)
        self.doPostUpgrade()

        # done, ask for reboot
        if self.askForReboot():
            subprocess.call(["reboot"])
        
    def run(self):
        self.breezyUpgrade()


