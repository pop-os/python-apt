
import warnings
warnings.filterwarnings("ignore", "apt API not stable yet", FutureWarning)
import apt
import apt_pkg
import os
import re
import logging
from gettext import gettext as _
from DistUpgradeConfigParser import DistUpgradeConfig
from DistUpgradeView import FuzzyTimeToStr

class MyCache(apt.Cache):
    # init
    def __init__(self, config, progress=None):
        apt.Cache.__init__(self, progress)
        self.to_install = []
        self.to_remove = []

        self.config = config
        self.metapkgs = self.config.getlist("Distro","MetaPkgs")

        # a list of regexp that are not allowed to be removed
        self.removal_blacklist = config.getListFromFile("Distro","RemovalBlacklistFile")

    # properties
    @property
    def requiredDownload(self):
        """ get the size of the packages that are required to download """
        pm = apt_pkg.GetPackageManager(self._depcache)
        fetcher = apt_pkg.GetAcquire()
        pm.GetArchives(fetcher, self._list, self._records)
        return fetcher.FetchNeeded
    @property
    def additionalRequiredSpace(self):
        """ get the size of the additonal required space on the fs """
        return self._depcache.UsrSize
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

    def clear(self):
        self._depcache.Init()

    def restore_snapshot(self):
        """ restore a snapshot """
        self.clear()
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

    def keepInstalledRule(self):
        """ run after the dist-upgrade to ensure that certain
            packages are kept installed """
        def keepInstalled(self, pkgname, reason):
            if (self.has_key(pkgname)
                and self[pkgname].isInstalled
                and self[pkgname].markedDelete):
                self.markInstall(pkgname, reason)
                
        # first the global list
        for pkgname in self.config.getlist("Distro","KeepInstalledPkgs"):
            keepInstalled(self, pkgname, "Distro KeepInstalledPkgs rule")
        # the the per-metapkg rules
        for key in self.metapkgs:
            if self.has_key(key) and (self[key].isInstalled or
                                      self[key].markedInstall):
                for pkgname in self.config.getlist(key,"KeepInstalledPkgs"):
                    keepInstalled(self, pkgname, "%s KeepInstalledPkgs rule" % key)
        # now the keepInstalledSection code
        for section in self.config.getlist("Distro","KeepInstalledSection"):
            for pkg in self:
                if pkg.markedDelete and pkg.section == section:
                    keepInstalled(self, pkg.name, "Distro KeepInstalledSection rule: %s" % section)
        # the the per-metapkg rules
        for key in self.metapkgs:
            if self.has_key(key) and (self[key].isInstalled or
                                      self[key].markedInstall):
                for section in self.config.getlist(key,"KeepInstalledSection"):
                    for pkg in self:
                        if pkg.markedDelete and pkg.section == section:
                            keepInstalled(self, pkg.name, "%s KeepInstalledSection rule: %s" % (key, section))
        

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

        # get the distro-specific quirks handler and run it
        quirksFuncName = "%sQuirks" % self.config.get("Sources","To")
        func = getattr(self, quirksFuncName, None)
        if func is not None:
            func()

    def edgyQuirks(self):
        """ this function works around quirks in the dapper->edgy upgrade """
        logging.debug("running edgyQuirks handler")
        for pkg in self:
            # deal with the python2.4-$foo -> python-$foo transition
            if (pkg.name.startswith("python2.4-") and
                pkg.isInstalled and
                not pkg.markedUpgrade):
                basepkg = "python-"+pkg.name[len("python2.4-"):]
                if (self.has_key(basepkg) and not self[basepkg].markedInstall):
                    try:
                        self.markInstall(basepkg,
                                         "python2.4->python upgrade rule")
                    except SystemError, e:
                        logging.debug("Failed to apply python2.4->python install: %s (%s)" % (basepkg, e))
            # xserver-xorg-input-$foo gives us trouble during the upgrade too
            if (pkg.name.startswith("xserver-xorg-input-") and
                pkg.isInstalled and
                not pkg.markedUpgrade):
                try:
                    self.markInstall(pkg.name, "xserver-xorg-input fixup rule")
                except SystemError, e:
                    logging.debug("Failed to apply fixup: %s (%s)" % (pkg.name, e))
            
        # deal with held-backs that are unneeded
        for pkgname in ["hpijs", "bzr", "tomboy"]:
            if (self.has_key(pkgname) and self[pkgname].isInstalled and
                not self[pkgname].markedUpgrade):
                try:
                    self.markInstall(pkgname,"%s quirk upgrade rule" % pkgname)
                except SystemError, e:
                    logging.debug("Failed to apply %s install (%s)" % (pkgname,e))
        # libgl1-mesa-dri from xgl.compiz.info (and friends) breaks the
	# upgrade, work around this here by downgrading the package
        if self.has_key("libgl1-mesa-dri"):
            pkg = self["libgl1-mesa-dri"]
            # the version from the compiz repo has a "6.5.1+cvs20060824" ver
            if (pkg.candidateVersion == pkg.installedVersion and
                "+cvs2006" in pkg.candidateVersion):
                for ver in pkg._pkg.VersionList:
                    # the "officual" edgy version has "6.5.1~20060817-0ubuntu3"
                    if "~2006" in ver.VerStr:
			# ensure that it is from a trusted repo
			for (VerFileIter, index) in ver.FileList:
				indexfile = self._list.FindIndex(VerFileIter)
				if indexfile and indexfile.IsTrusted:
					logging.info("Forcing downgrade of libgl1-mesa-dri for xgl.compz.info installs")
		                        self._depcache.SetCandidateVer(pkg._pkg, ver)
					break
                                    
        # deal with general if $foo is installed, install $bar
        for (fr, to) in [("xserver-xorg-driver-all","xserver-xorg-video-all")]:
            if self.has_key(fr) and self.has_key(to):
                if self[fr].isInstalled and not self[to].markedInstall:
                    try:
                        self.markInstall(to,"%s->%s quirk upgrade rule" % (fr, to))
                    except SystemError, e:
                        logging.debug("Failed to apply %s->%s install (%s)" % (fr, to, e))
                    
                    
                                  
    def dapperQuirks(self):
        """ this function works around quirks in the breezy->dapper upgrade """
        logging.debug("running dapperQuirks handler")
        if (self.has_key("nvidia-glx") and self["nvidia-glx"].isInstalled and
            self.has_key("nvidia-settings") and self["nvidia-settings"].isInstalled):
            logging.debug("nvidia-settings and nvidia-glx is installed")
            self.markRemove("nvidia-settings")
            self.markInstall("nvidia-glx")

    def distUpgrade(self, view):
        try:
            # upgrade (and make sure this way that the cache is ok)
            self.upgrade(True)

            # see if our KeepInstalled rules are honored
            self.keepInstalledRule()

            # and if we have some special rules
            self.postUpgradeRule()

            # then see if meta-pkgs are missing
            if not self._installMetaPkgs(view):
                raise SystemError, _("Can't upgrade required meta-packages")

            # see if it all makes sense
            if not self._verifyChanges():
                raise SystemError, _("A essential package would have to be removed")
        except SystemError, e:
            # FIXME: change the text to something more useful
            view.error(_("Could not calculate the upgrade"),
                       _("A unresolvable problem occurred while "
                         "calculating the upgrade.\n\n"
                         "Please report this bug against the 'update-manager' "
                         "package and include the files in /var/log/dist-upgrade/ "
                         "in the bugreport."))
            logging.error("Dist-upgrade failed: '%s'", e)
            return False

        # check the trust of the packages that are going to change
        untrusted = []
        for pkg in self.getChanges():
            if pkg.markedDelete:
                continue
            # special case because of a bug in pkg.candidateOrigin
            if pkg.markedDowngrade:
                for ver in pkg._pkg.VersionList:
                    # version is lower than installed one
                    if apt_pkg.VersionCompare(ver.VerStr, pkg.installedVersion) < 0:
                        for (verFileIter,index) in ver.FileList:
                            if not origin.trusted:
                                untrusted.append(pkg.name)
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
        removeEssentialOk = self.config.getlist("Distro","RemoveEssentialOk")
        for pkg in self.getChanges():
            if pkg.markedDelete and self._inRemovalBlacklist(pkg.name):
                logging.debug("The package '%s' is marked for removal but it's in the removal blacklist", pkg.name)
                return False
            if pkg.markedDelete and (pkg._pkg.Essential == True and
                                     not pkg.name in removeEssentialOk):
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
                    except SystemError, e:
                        logging.error("failed to mark '%s' for install (%s)" % (key,e))
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
                        "ubuntu you are running.\n "
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
        try:
            self[pkgname].markDelete()
            for pkg in self.getChanges():
                if pkg.name not in remove_candidates or \
                       pkg.name in foreign_pkgs or \
                       self._inRemovalBlacklist(pkg.name):
                    self.restore_snapshot()
                    return False
        except (SystemError,KeyError),e:
            logging.warning("_tryMarkObsoleteForRemoval failed for '%s' (%s)" % (pkgname,e))
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

if __name__ == "__main__":
	import DistUpgradeConfigParser
	c = MyCache(DistUpgradeConfigParser.DistUpgradeConfig("."))
	c.clear()
