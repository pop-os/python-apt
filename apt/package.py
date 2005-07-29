# package.py - apt package abstraction
#  
#  Copyright (c) 2005 Canonical
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

import apt_pkg, string
import random

class Package(object):

    def __init__(self, cache, depcache, records, pcache, pkgiter):
        """ Init the Package object """
        self._cache = cache             # low level cache
        self._depcache = depcache
        self._records = records
        self._pkg = pkgiter
        self._pcache = pcache           # python cache in cache.py
        pass

    # helper
    def _LookupRecord(self, UseCandidate=True):
        """ internal helper that moves the Records to the right
            position, must be called before _records is accessed """
        if UseCandidate:
            ver = self._depcache.GetCandidateVer(self._pkg)
        else:
            ver = self._pkg.CurrentVer

        # check if we found a version
        if ver == None:
            print "No version for: %s (Candiate: %s)" % (self._pkg.Name, UseCandidate)
            return False
        
        if ver.FileList == None:
            print "No FileList for: %s " % self._pkg.Name()
            return False
        file, index = ver.FileList.pop(0)
        self._records.Lookup((file,index))
        return True

    # basic information
    def Name(self):
        """ return the name of the package """
        return self._pkg.Name

    def ID(self):
        """ return a uniq ID for the pkg, can be used to store
            additional information about the pkg """
        return self._pkg.ID

    def InstalledVersion(self):
        """ return the installed version as string """
        ver = self._pkg.CurrentVer
        if ver != None:
            return ver.VerStr
        else:
            return None
        
    def CandidateVersion(self):
        """ return the candidate version as string """
        ver = self._depcache.GetCandidateVer(self._pkg)
        if ver != None:
            return ver.VerStr
        else:
            return None

    def SourcePackageName(self):
        """ return the source package name as string """
        self._LookupRecord()
        src = self._records.SourcePkg
        if src != "":
            return src
        else:
            return self._pkg.Name

    def Section(self):
        """ return the section of the package"""
        return self._pkg.Section
    
    def Priority(self, UseCandidate=True):
        """ return the priority """
        if UseCandidate:
            ver = self._depcache.GetCandidateVer(self._pkg)
        else:
            ver = self._pkg.CurrentVer
        if ver:
            return ver.PriorityStr
        else:
            return None
    
    def Summary(self):
        """ return the short description (one-line summary) """
        self._LookupRecord()
        return self._records.ShortDesc

    def Description(self, format=False):
        """ return the long description """
        self._LookupRecord()
        if format:
            desc = ""
            for line in string.split(self._records.LongDesc, "\n"):
                tmp = string.strip(line)
                if tmp == ".":
                    desc += "\n"
                else:
                    desc += tmp + "\n"
            return desc
        else:
            return self._records.LongDesc

    # depcache state
    def MarkedInstall(self):
        return self._depcache.MarkedInstall(self._pkg)
    def MarkedUpgrade(self):
        return self._depcache.MarkedUpgrade(self._pkg)
    def MarkedDelete(self):
        return self._depcache.MarkedDelete(self._pkg)
    def MarkedKeep(self):
        return self._depcache.MarkedKeep(self._pkg)
    def MarkedDowngrade(self):
        return self._depcache.MarkedDowngrade(self._pkg)
    def MarkedReinstall(self):
        return self._depcache.MarkedReinstall(self._pkg)
    def IsInstalled(self):
        return (self._pkg.CurrentVer != None)
    def IsUpgradable(self):
        return self.IsInstalled() and self._depcache.IsUpgradable(self._pkg)

    # depcache action
    def MarkKeep(self):
        self._pcache.CachePreChange()
        self._depcache.MarkKeep(self._pkg)
        self._pcache.CachePostChange()
    def MarkDelete(self, autoFix=True):
        self._pcache.CachePreChange()
        self._depcache.MarkDelete(self._pkg)
        # try to fix broken stuffsta
        if autoFix and self._depcache.BrokenCount > 0:
            Fix = apt_pkg.GetPkgProblemResolver(self._depcache)
            Fix.Clear(self._pkg)
            Fix.Protect(self._pkg)
            Fix.Remove(self._pkg)
            Fix.InstallProtect()
            Fix.Resolve()
        self._pcache.CachePostChange()
    def MarkInstall(self, autoFix=True):
        self._pcache.CachePreChange()
        self._depcache.MarkInstall(self._pkg)
        # try to fix broken stuff
        if autoFix and self._depcache.BrokenCount > 0:
            fixer = apt_pkg.GetPkgProblemResolver(self._depcache)
            fixer.Clear(self._pkg)
            fixer.Protect(self._pkg)
            fixer.Resolve(True)
        self._pcache.CachePostChange()
    def MarkUpgrade(self):
        if self.IsUpgradable():
            self.MarkInstall()
        # FIXME: we may want to throw a exception here
        sys.stderr.write("MarkUpgrade() called on a non-upgrable pkg")
        
    # size
    def PackageSize(self, UseCandidate=True):
        if UseCandidate:
            ver = self._depcache.GetCandidateVer(self._pkg)
        else:
            ver = self._pkg.GetCurrentVer
        return ver.Size

    def InstalledSize(self, UseCandidate=True):
        if UseCandidate:
            ver = self._depcache.GetCandidateVer(self._pkg)
        else:
            ver = self._pkg.GetCurrentVer
        return ver.InstalledSize

    def Commit(self, fprogress, iprogress):
        self._depcache.Commit(fprogress, iprogress)

# self-test
if __name__ == "__main__":
    print "Self-test for the Package modul"
    apt_pkg.init()
    cache = apt_pkg.GetCache()
    depcache = apt_pkg.GetDepCache(cache)
    records = apt_pkg.GetPkgRecords(cache)

    iter = cache["apt-utils"]
    pkg = Package(cache, depcache, records, None, iter)
    print "Name: %s " % pkg.Name()
    print "Installed: %s " % pkg.InstalledVersion()
    print "Candidate: %s " % pkg.CandidateVersion()
    print "SourcePkg: %s " % pkg.SourcePackageName()
    print "Section: %s " % pkg.Section()
    print "Priority (Candidate): %s " % pkg.Priority()
    print "Priority (Installed): %s " % pkg.Priority(False)
    print "Summary: %s" % pkg.Summary()
    print "Description:\n%s" % pkg.Description()
    print "Description (formated) :\n%s" % pkg.Description(True)
    print "InstalledSize: %s " % pkg.InstalledSize()
    print "PackageSize: %s " % pkg.PackageSize()

    # now test install/remove
    import apt
    progress = apt.progress.OpTextProgress()
    cache = apt.Cache(progress)
    for i in [True, False]:
        print "Running install on random upgradable pkgs with AutoFix: %s " % i
        for name in cache.keys():
            pkg = cache[name]
            if pkg.IsUpgradable():
                if random.randint(0,1) == 1:
                    pkg.MarkInstall(i)
        print "Broken: %s " % cache._depcache.BrokenCount
        print "InstCount: %s " % cache._depcache.InstCount

    print
    # get a new cache
    for i in [True, False]:
        print "Randomly remove some packages with AutoFix: %s" % i
        cache = apt.Cache(progress)
        for name in cache.keys():
            if random.randint(0,1) == 1:
                try:
                    cache[name].MarkDelete(i)
                except SystemError:
                    print "Error trying to remove: %s " % name
        print "Broken: %s " % cache._depcache.BrokenCount
        print "DelCount: %s " % cache._depcache.DelCount
