#!/usr/bin/python
# example how to deal with the depcache

import apt_pkg

class TextProgress:
    def __init__(self):
        self.last = 1
    def show(self,Percent):
        if self.last < Percent:
            print "\r%.2f            "  % Percent,
            self.last = Percent+0.1
        if Percent >= 100:
            print "\r100.0         "
            self.last = 0

def Update(Percent, data):
    # data is a TextProgress class
    progress = data           
    progress.show(Percent)


apt_pkg.init()

progress = TextProgress()
cache = apt_pkg.GetCache(Update, progress)
print cache.PackageCount

iter = cache["base-config"]
print iter

depcache = apt_pkg.GetDepCache(cache, Update, progress)
print depcache
print depcache.InstCount

ver= depcache.GetCandidateVer(iter)
print ver
