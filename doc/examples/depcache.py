#!/usr/bin/python
# example how to deal with the depcache

import apt_pkg

def Update(Percent, data):
    pass

apt_pkg.init()
cache = apt_pkg.GetCache()
print cache.PackageCount

iter = cache["base-config"]
print iter

depcache = apt_pkg.GetDepCache(cache)
depcache.SetProgressCallback(Update, None)
depcache.Init()
print depcache
print depcache.InstCount

ver= depcache.GetCandidateVer(iter)
print ver
