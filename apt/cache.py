import apt_pkg
from apt import Package
from apt.progress import OpTextProgress
from UserDict import UserDict

class Cache(object):
    def __init__(self, progress=None):
        self.Open(progress)

    def Open(self, progress):
        self._cache = apt_pkg.GetCache(progress)
        self._depcache = apt_pkg.GetDepCache(self._cache)
        self._records = apt_pkg.GetPkgRecords(self._cache)
        self._dict = {}

        # build the packages dict
        if progress != None:
            progress.Op = "Building data structures"
        i=last=0
        size=len(self._cache.Packages)
        for pkg in self._cache.Packages:
            if progress != None and last+100 < i:
                progress.Update(i/float(size)*100)
                last=i
            # drop stuff with no versions (cruft)
            if len(pkg.VersionList) > 0:
                self._dict[pkg.Name] = Package(self._cache, self._depcache,
                                               self._records, self, pkg)
            i += 1
        if progress != None:
            progress.Done()
        
    def __getitem__(self, key):
        return self._dict[key]

    def has_key(self, key):
        try:
            self._dict[key]
        except KeyError:
            return False
        return True

    def __len__(self):
        return len(self._dict)

    def keys(self):
        return self._dict.keys()

    def GetChanges(self):
        changes = [] 
        for name in self._dict.keys():
            p = self._dict[name]
            if p.MarkedUpgrade() or p.MarkedInstall() or p.MarkedDelete() or \
               p.MarkedDowngrade() or p.MarkedReinstall():
                changes.append(p)
        return changes

    def Upgrade(self, DistUpgrade=False):
        self._depcache.Upgrade(DistUpgrade)

    def Commit(self, fprogress, iprogress):
        self._depcache.Commit(fprogress, iprogress)

    def CacheChange(self):
        " called internally if the cache changes, emit a signal then "
        pass

# ----------------------------- experimental interface
class Filter(object):
    def apply(self, pkg):
        return True

class MarkedChangesFilter(Filter):
    def apply(self, pkg):
        if pkg.MarkedInstall() or pkg.MarkedDelete() or pkg.MarkedUpgrade():
            return True
        else:
            return False

class FilteredCache(Cache):
    def __init__(self, progress=None):
        Cache.__init__(self, progress)
        self._filtered = {}
        self._filters = []
    def __len__(self):
        return len(self._filtered)
    
    def __getitem__(self, key):
        return self._dict[key]

    def keys(self):
        return self._filtered.keys()

    def has_key(self, key):
        try:
            self._filtered[key]
        except KeyError:
            return False
        return True

    def reapplyFilter(self):
        for pkg in self._dict.keys():
            for f in self._filters:
                if f.apply(self._dict[pkg]):
                    self._filtered[pkg] = 1
        
    
    def AddFilter(self, filter):
        self._filters.append(filter)
        self.reapplyFilter()

    def CacheChange(self):
        " called internally if the cache changes, emit a signal then "
        reapplyFilter()

                
if __name__ == "__main__":
    print "Cache self test"
    apt_pkg.init()
    c = Cache(OpTextProgress())
    print c.has_key("aptitude")
    p = c["aptitude"]
    print p.Name()
    print len(c)

    for pkg in c.keys():
        x= c[pkg].Name()

    c.Upgrade()
    for p in c.GetChanges():
        print p.Name()

    print "Testing filtered cache"
    c = FilteredCache()
    c.Upgrade()
    c.AddFilter(MarkedChangesFilter())
    for pkg in c.keys():
        print c[pkg].Name()
    
