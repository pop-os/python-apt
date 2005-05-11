import apt_pkg, string

class Package(object):

    def __init__(self, cache, depcache, records, pkgiter):
        """ Init the Package object """
        self._cache = cache
        self._depcache = depcache
        self._records = records
        self._pkg = pkgiter
        pass

    # helper
    def _LookupRecord(self, UseCandidate=True):
        """ internal helper that moves the Records to the right
            position, must be called before _records is accessed """
        if UseCandidate:
            ver = self._depcache.GetCandidateVer(self._pkg)
        else:
            ver = self._pkg.CurrentVer
        file, index = ver.FileList.pop(0)
        self._records.Lookup((file,index))


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
    def IsInstalled(self):
        return (self._pkg.CurrentVer != None)
    def IsUpgradable(self):
        return IsInstalled() and self._depcache.IsUpgradable(self._pkg)

    # depcache action
    def MarkKeep(self):
        return self._depcache.MarkKeep(self._pkg)
    def MarkDelete(self):
        return self._depcache.MarkDelete(self._pkg)
    def MarkInstall(self):
        return self._depcache.MarkInstall(self._pkg)

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
    pkg = Package(cache, depcache, records, iter)
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
