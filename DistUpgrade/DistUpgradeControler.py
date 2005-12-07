#!/usr/bin/python2.4


import apt
import apt_pkg
import sys
import os
import subprocess

from UpdateManager.Common.SimpleGladeApp import SimpleGladeApp
from SoftwareProperties.aptsources import SourcesList, SourceEntry
from gettext import gettext as _


class MyCache(apt.Cache):
    @property
    def requiredDownload(self):
        pm = apt_pkg.GetPackageManager(self._depcache)
        fetcher = apt_pkg.GetAcquire()
        pm.GetArchives(fetcher, self._list, self._records)
        return fetcher.FetchNeeded
    def downloadable(self, pkg, useCandidate=True):
        " check if the given pkg can be downloaded "
        if useCandidate:
            ver = self._depcache.GetCandidateVer(pkg._pkg)
        else:
            ver = pkg._pkg.CurrentVer
        if ver == None:
            return False
        return ver.Downloadable

        

class DistUpgradeControler(object):
    def __init__(self, distUpgradeView):
        self._view = distUpgradeView
        self._view.updateStatus(_("Reading cache"))
        self._cache = MyCache(self._view.getOpCacheProgress())
        # some constants here
        self.fromDist = "hoary"
        self.toDist = "breezy"
        self.origin = "Ubuntu"

    def sanityCheck(self):
        if self._cache._depcache.BrokenCount > 0:
            # FIXME: we more helpful here and offer to actually fix the
            # system
            self._view.error(_("Broken packages"),
                             _("Your system contains broken packages. "
                               "Please fix them first using synaptic or "
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
        for pkg in self._cache:
            if pkg.isInstalled:
                if not self._cache.downloadable(pkg):
                    obsolete_pkgs.add(pkg.name)
        return obsolete_pkgs

    def _getForeignPkgs(self):
        """ get all packages that are installed from a foreign repo
            (and are actually downloadable)
        """
        foreign_pkgs =set()        
        for pkg in self._cache:
            if pkg.isInstalled and self._cache.downloadable(pkg):
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
        #print self.foreign_pkgs
        #print self.obsolete_pkgs

    def doUpdate(self):
        self._cache._list.ReadMainList()
        progress = self._view.getFetchProgress()
        self._cache.update(progress)

    def askDistUpgrade(self):
        # FIXME: add "ubuntu-desktop" (or kubuntu-desktop, edubuntu-desktop)
        #        (if required)
        self._cache.upgrade(True)
        changes = self._cache.getChanges()
        res = self._view.confirmChanges(changes,self._cache.requiredDownload)
        return res

    def doDistUpgrade(self):
        fprogress = self._view.getFetchProgress()
        iprogress = self._view.getInstallProgress()
        self._cache.commit(fprogress,iprogress)

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
        if not self.sanityCheck():
            sys.exit(1)

        # do pre-upgrade stuff (calc list of obsolete pkgs etc)
        self.doPreUpgrade()

        # update sources.list
        self._view.updateStatus(_("Updating repository information"))
        if not self.updateSourcesList():
            sys.exit(1)
        # then update the package index files
        self.doUpdate()

        # then open the cache (again)
        self._view.updateStatus(_("Reading cache"))
        self._cache = MyCache(self._view.getOpCacheProgress())

        # calc the dist-upgrade and see if the removals are ok/expected
        # do the dist-upgrade
        self._view.updateStatus(_("Performing the upgrade"))
        if not self.askDistUpgrade():
            sys.exit(1)
        self.doDistUpgrade()
            
        # do post-upgrade stuff
        self.doPostUpgrade()

        # done, ask for reboot
        if self.askForReboot():
            subprocess.call(["reboot"])
        
    def run(self):
        self.breezyUpgrade()


if __name__ == "__main__":
    view = GtkDistUpgradeView()
    app = DistUpgradeControler(view)
    app.run()
