#!/usr/bin/python
import apt_pkg
import re

apt_pkg.InitConfig()
apt_pkg.InitSystem()
apt_cache = apt_pkg.GetCache()
# wrong
apt_depcache = apt_pkg.GetCache(apt_cache)
# correct: apt_depcache = apt_pkg.GetDepCache(apt_cache)
re.compile('a')
