#!/usr/bin/python
# example how to deal with the depcache

import apt_pkg

apt_pkg.init()
cache = apt_pkg.GetCache()
print cache.PackageCount

iter = cache["base-config"]
print iter

depcache = apt_pkg.GetDepCache(cache)
depcache.Init()
print depcache
print depcache.InstCount

ver= depcache.GetCandidateVer(iter)
print ver
