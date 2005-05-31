import apt_pkg
from apt import Package
from UserDict import UserDict

class Cache(object):
    def __init__(self, progress=None):
        self.open(progress)

    def open(self, progress):
        self._cache = apt_pkg.GetCache(progress)
        self._depcache = apt_pkg.GetDepCache(self._cache)
        self._records = apt_pkg.GetPkgRecords(self._cache)
        self._dict = {}

        # build the packages dict
        for pkg in self._cache.Packages:
            # drop stuff with no versions (cruft)
            if len(pkg.VersionList) > 0:
                self._dict[pkg.Name] = Package(self._cache, self._depcache, self._records, pkg)

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

    def Upgrade(self, DistUpgrade=False):
        self._depcache.Upgrade(DistUpgrade)

    def Commit(self, fprogress, iprogress):
        self._depcache.Commit(fprogress, iprogress)


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
    
    def AddFilter(self, filter):
        for pkg in self._dict.keys():
            if filter.apply(self._dict[pkg]):
                self._filtered[pkg] = 1
                
if __name__ == "__main__":
    print "Cache self test"
    apt_pkg.init()
    c = Cache()
    print c.has_key("aptitude")
    p = c["aptitude"]
    print p.Name()
    print len(c)

    for pkg in c.keys():
        x= c[pkg].Name()


    c = FilteredCache()
    c.Upgrade()
    c.AddFilter(MarkedChangesFilter())
    for pkg in c.keys():
        print c[pkg].Name()
    
