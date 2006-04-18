
import apt
import apt_pkg
import os
import re
import logging
from gettext import gettext as _
from DistUpgradeConfigParser import DistUpgradeConfig

class MyCache(apt.Cache):
    # init
    def __init__(self, progress=None):
        apt.Cache.__init__(self, progress)
        self.to_install = []
        self.to_remove = []

        self.config = DistUpgradeConfig()
        self.metapkgs = self.config.getlist("Distro","MetaPkgs")

        # turn on debuging
        apt_pkg.Config.Set("Debug::pkgProblemResolver","true")
        fd = os.open("/var/log/dist-upgrade-apt.log", os.O_RDWR|os.O_CREAT|os.O_TRUNC)
        os.dup2(fd,1)
        os.dup2(fd,2)

        # a list of regexp that are not allowed to be removed
        self.removal_blacklist = []
        for line in open("removal_blacklist.txt").readlines():
            line = line.strip()
            if not line == "" or line.startswith("#"):
                self.removal_blacklist.append(line)

    # properties
    @property
    def requiredDownload(self):
        """ get the size of the packages that are required to download """
        pm = apt_pkg.GetPackageManager(self._depcache)
        fetcher = apt_pkg.GetAcquire()
        pm.GetArchives(fetcher, self._list, self._records)
        return fetcher.FetchNeeded
    @property
    def isBroken(self):
        """ is the cache broken """
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

    def sanityCheck(self, view):
        """ check if the cache is ok and if the required metapkgs
            are installed
        """
        if self.isBroken:
            try:
                logging.debug("Have broken pkgs, trying to fix them")
                self.fixBroken()
            except SystemError:
                view.error(_("Broken packages"),
                                 _("Your system contains broken packages "
                                   "that couldn't be fixed with this "
                                   "software. "
                                   "Please fix them first using synaptic or "
                                   "apt-get before proceeding."))
                return False
        return True

    def markInstall(self, pkg, reason=""):
        logging.debug("Installing '%s' (%s)" % (pkg, reason))
        if self.has_key(pkg):
            self[pkg].markInstall()
    def markRemove(self, pkg, reason=""):
        logging.debug("Removing '%s' (%s)" % (pkg, reason))
        if self.has_key(pkg):
            self[pkg].markDelete()
    def markPurge(self, pkg, reason=""):
        logging.debug("Purging '%s' (%s)" % (pkg, reason))
        if self.has_key(pkg):
            self._depcache.MarkDelete(self[pkg]._pkg,True)

    def postUpgradeRule(self):
        " run after the upgrade was done in the cache "
        for (rule, action) in [("Install", self.markInstall),
                               ("Remove", self.markRemove),
                               ("Purge", self.markPurge)]:
            # first the global list
            for pkg in self.config.getlist("Distro","PostUpgrade%s" % rule):
                action(pkg, "Distro PostUpgrade%s rule" % rule)
            for key in self.metapkgs:
                if self.has_key(key) and (self[key].isInstalled or
                                          self[key].markedInstall):
                    for pkg in self.config.getlist(key,"PostUpgrade%s" % rule):
                        action(pkg, "%s PostUpgrade%s rule" % (key, rule))

    def distUpgrade(self, view):
        try:
            # upgrade (and make sure this way that the cache is ok)
            self.upgrade(True)

            # then see if meta-pkgs are missing
            if not self._installMetaPkgs(view):
                raise SystemError, _("Can't upgrade required meta-packages")

            # and if we have some special rules
            self.postUpgradeRule()

            # see if it all makes sense
            if not self._verifyChanges():
                raise SystemError, _("A essential package would have to be removed")
        except SystemError, e:
            # FIXME: change the text to something more useful
            view.error(_("Could not calculate the upgrade"),
                       _("A unresolvable problem occured while "
                         "calculating the upgrade. Please report "
                         "this as a bug. "))
            logging.error("Dist-upgrade failed: '%s'", e)
            return False

        # check the trust of the packages that are going to change
        untrusted = []
        for pkg in self.getChanges():
            if pkg.markedDelete:
                continue
            origins = pkg.candidateOrigin
            trusted = False
            for origin in origins:
                #print origin
                trusted |= origin.trusted
            if not trusted:
                untrusted.append(pkg.name)
        if len(untrusted) > 0:
            untrusted.sort()
            logging.error("Unauthenticated packages found: '%s'" % \
                          " ".join(untrusted))
            # FIXME: maybe ask a question here? instead of failing?
            view.error(_("Error authenticating some packages"),
                       _("It was not possible to authenticate some "
                         "packages. This may be a transient network problem. "
                         "You may want to try again later. See below for a "
                         "list of unauthenticated packages."),
                       "\n".join(untrusted))
            return False
        return True

    def _verifyChanges(self):
        """ this function tests if the current changes don't violate
            our constrains (blacklisted removals etc)
        """
        for pkg in self.getChanges():
            if pkg.markedDelete and self._inRemovalBlacklist(pkg.name):
                logging.debug("The package '%s' is marked for removal but it's in the removal blacklist", pkg.name)
                return False
            if pkg.markedDelete and pkg._pkg.Essential == True:
                logging.debug("The package '%s' is marked for removal but it's a ESSENTIAL package", pkg.name)
                return False
        return True

    def _installMetaPkgs(self, view):
        # helper for this func
        def metaPkgInstalled():
            metapkg_found = False
            for key in metapkgs:
                if self.has_key(key):
                    pkg = self[key]
                    if (pkg.isInstalled and not pkg.markedDelete) \
                           or self[key].markedInstall:
                        metapkg_found=True
            return metapkg_found

        # now check for ubuntu-desktop, kubuntu-desktop, edubuntu-desktop
        metapkgs = self.config.getlist("Distro","MetaPkgs")

        # we never go without ubuntu-base
        for pkg in self.config.getlist("Distro","BaseMetaPkgs"):
            self[pkg].markInstall()

        # every meta-pkg that is installed currently, will be marked
        # install (that result in a upgrade and removes a markDelete)
        for key in metapkgs:
            try:
                if self.has_key(key) and self[key].isInstalled:
                    logging.debug("Marking '%s' for upgrade" % key)
                    self[key].markUpgrade()
            except SystemError, e:
                logging.debug("Can't mark '%s' for upgrade (%s)" % (key,e))
                return False
        # check if we have a meta-pkg, if not, try to guess which one to pick
        if not metaPkgInstalled():
            logging.debug("no {ubuntu,edubuntu,kubuntu}-desktop pkg installed")
            for key in metapkgs:
                deps_found = True
                for pkg in self.config.getlist(key,"KeyDependencies"):
                    deps_found &= self.has_key(pkg) and self[pkg].isInstalled
                if deps_found:
                    logging.debug("guessing '%s' as missing meta-pkg" % key)
                    try:
                        self[key].markInstall()
                    except SystemError:
                        logging.error("failed to mark '%s' for install" % key)
                        view.error(_("Can't install '%s'" % key),
                                   _("It was impossible to install a "
                                     "required package. Please report "
                                     "this as a bug. "))
                        return False
        # check if we actually found one
        if not metaPkgInstalled():
            # FIXME: provide a list
            view.error(_("Can't guess meta-package"),
                       _("Your system does not contain a "
                         "ubuntu-desktop, kubuntu-desktop or "
                         "edubuntu-desktop package and it was not "
                         "possible to detect which version of "
                        "ubuntu you are runing.\n "
                         "Please install one of the packages "
                         "above first using synaptic or "
                         "apt-get before proceeding."))
            return False
        return True

    def _inRemovalBlacklist(self, pkgname):
        for expr in self.removal_blacklist:
            if re.compile(expr).match(pkgname):
                return True
        return False

    def _tryMarkObsoleteForRemoval(self, pkgname, remove_candidates, foreign_pkgs):
        # this is a delete candidate, only actually delete,
        # if it dosn't remove other packages depending on it
        # that are not obsolete as well
        self.create_snapshot()
        self[pkgname].markDelete()
        for pkg in self.getChanges():
            if pkg.name not in remove_candidates or \
                   pkg.name in foreign_pkgs or \
                   self._inRemovalBlacklist(pkg.name):
                self.restore_snapshot()
                return False
        return True
    
    def _getObsoletesPkgs(self):
        " get all package names that are not downloadable "
        obsolete_pkgs =set()        
        for pkg in self:
            if pkg.isInstalled:
                if not self.downloadable(pkg):
                    obsolete_pkgs.add(pkg.name)
        return obsolete_pkgs

    def _getForeignPkgs(self, allowed_origin, fromDist, toDist):
        """ get all packages that are installed from a foreign repo
            (and are actually downloadable)
        """
        foreign_pkgs=set()        
        for pkg in self:
            if pkg.isInstalled and self.downloadable(pkg):
                # assume it is foreign and see if it is from the 
                # official archive
                foreign=True
                for origin in pkg.candidateOrigin:
                    if fromDist in origin.archive and \
                           origin.origin == allowed_origin:
                        foreign = False
                    if toDist in origin.archive and \
                           origin.origin == allowed_origin:
                        foreign = False
                if foreign:
                    foreign_pkgs.add(pkg.name)
        return foreign_pkgs
