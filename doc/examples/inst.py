#!/usr/bin/python
# example how to deal with the depcache

import apt_pkg
import sys
import copy

from progress import OpProgress, FetchProgress


# init
apt_pkg.init()

progress = OpProgress()
cache = apt_pkg.GetCache(progress)
print "Available packages: %s " % cache.PackageCount

# get depcache
depcache = apt_pkg.GetDepCache(cache)
depcache.ReadPinFile()
depcache.Init(progress)

# do something
fprogress = FetchProgress()
iprogress = "lala"
iter = cache["base-config"]
print "\n%s"%iter

# install or remove, the importend thing is to keep us busy :)
if iter.CurrentVer == None:
	depcache.MarkInstall(iter)
else:
	depcache.MarkDelete(iter)
depcache.Commit(fprogress, iprogress)

print "Exiting"
sys.exit(0)













iter = cache["base-config"]
print "example package iter: %s" % iter

# get depcache
print "\n\n depcache"
depcache = apt_pkg.GetDepCache(cache, progress)
depcache.ReadPinFile()
print "got a depcache: %s " % depcache
print "Marked for install: %s " % depcache.InstCount

print "\n\n Reinit"
depcache.Init(progress)

#sys.exit()


# get a canidate version
ver= depcache.GetCandidateVer(iter)
print "Candidate version: %s " % ver

print "\n\nQuerry interface"
print "%s.IsUpgradable(): %s" % (iter.Name, depcache.IsUpgradable(iter))

print "\nMarking interface"
print "Marking '%s' for install" % iter.Name
depcache.MarkInstall(iter)
print "Install count: %s " % depcache.InstCount
print "%s.MarkedInstall(): %s" % (iter.Name, depcache.MarkedInstall(iter))
print "%s.MarkedUpgrade(): %s" % (iter.Name, depcache.MarkedUpgrade(iter))
print "%s.MarkedDelete(): %s" % (iter.Name, depcache.MarkedDelete(iter))

print "Marking %s for delete" % iter.Name
depcache.MarkDelete(iter)
print "DelCount: %s " % depcache.DelCount
print "%s.MarkedDelete(): %s" % (iter.Name, depcache.MarkedDelete(iter))


iter = cache["3dchess"]
print "\nMarking '%s' for install" % iter.Name
depcache.MarkInstall(iter)
print "Install count: %s " % depcache.InstCount
print "%s.MarkedInstall(): %s" % (iter.Name, depcache.MarkedInstall(iter))
print "%s.MarkedUpgrade(): %s" % (iter.Name, depcache.MarkedUpgrade(iter))
print "%s.MarkedDelete(): %s" % (iter.Name, depcache.MarkedDelete(iter))

print "Marking %s for keep" % iter.Name
depcache.MarkKeep(iter)
print "Install: %s " % depcache.InstCount

iter = cache["3dwm-server"]
print "\nMarking '%s' for install" % iter.Name
depcache.MarkInstall(iter)
print "Install: %s " % depcache.InstCount
print "Broken count: %s" % depcache.BrokenCount
print "FixBroken() "
depcache.FixBroken()
print "Broken count: %s" % depcache.BrokenCount

print "\nPerforming Upgrade"
depcache.Upgrade()
print "Keep: %s " % depcache.KeepCount
print "Install: %s " % depcache.InstCount
print "Delete: %s " % depcache.DelCount
print "UsrSize: %s " % apt_pkg.SizeToStr(depcache.UsrSize)
print "DebSize: %s " % apt_pkg.SizeToStr(depcache.DebSize)

for pkg in cache.Packages:
    if pkg.CurrentVer != None and not depcache.MarkedInstall(pkg) and depcache.IsUpgradable(pkg):
        print "Upgrade didn't upgrade (kept): %s" % pkg.Name


print "\nPerforming DistUpgrade"
depcache.Upgrade(True)
print "Keep: %s " % depcache.KeepCount
print "Install: %s " % depcache.InstCount
print "Delete: %s " % depcache.DelCount
print "UsrSize: %s " % apt_pkg.SizeToStr(depcache.UsrSize)
print "DebSize: %s " % apt_pkg.SizeToStr(depcache.DebSize)

# overview about what would happen
for pkg in cache.Packages:
    if depcache.MarkedInstall(pkg):
        if pkg.CurrentVer != None:
            print "Marked upgrade: %s " % pkg.Name
        else:
            print "Marked install: %s" % pkg.Name
    elif depcache.MarkedDelete(pkg):
        print "Marked delete: %s" % pkg.Name
    elif depcache.MarkedKeep(pkg):
        print "Marked keep: %s" % pkg.Name
