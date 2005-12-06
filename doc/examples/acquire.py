import apt
import apt_pkg
import os
import sys

apt_pkg.init()

#apt_pkg.Config.Set("Debug::pkgDPkgPM","1");
#apt_pkg.Config.Set("Debug::pkgPackageManager","1");
#apt_pkg.Config.Set("Debug::pkgDPkgProgressReporting","1");

cache = apt_pkg.GetCache()
depcache = apt_pkg.GetDepCache(cache)

recs = apt_pkg.GetPkgRecords(cache)
list = apt_pkg.GetPkgSourceList()
list.ReadMainList()

# show the amount fetch needed for a dist-upgrade 
depcache.Upgrade(True)
progress = apt.progress.TextFetchProgress()
fetcher = apt_pkg.GetAcquire(progress)
pm = apt_pkg.GetPackageManager(depcache)
pm.GetArchives(fetcher,list,recs)
print "%s (%s)" % (apt_pkg.SizeToStr(fetcher.FetchNeeded), fetcher.FetchNeeded)

for pkg in cache.Packages:
    depcache.MarkKeep(pkg)

try:
    os.mkdir("/tmp/pyapt-test")
    os.mkdir("/tmp/pyapt-test/partial")
except OSError:
    pass
apt_pkg.Config.Set("Dir::Cache::archives","/tmp/pyapt-test")

pkg = cache["3ddesktop"]
depcache.MarkInstall(pkg)

progress = apt.progress.TextFetchProgress()
fetcher = apt_pkg.GetAcquire(progress)
#fetcher = apt_pkg.GetAcquire()
pm = apt_pkg.GetPackageManager(depcache)

print pm
print fetcher

af = apt_pkg.GetPkgAcqFile(fetcher,
                           uri="ftp://ftp.debian.org/debian/dists/README",
                           descr="sample descr",
                           destFile="/tmp/lala2")
fetcher.Run()
sys.exit(1)

pm.GetArchives(fetcher,list,recs)

for item in fetcher.Items:
    print item
    if item.Status == item.StatError:
        print "Some error ocured: '%s'" % item.ErrorText
    if item.Complete == False:
        print "No error, still nothing downloaded (%s)" % item.ErrorText
    print
                                                         

res = fetcher.Run()
print "fetcher.Run() returned: %s" % res

print "now runing pm.DoInstall()"
res = pm.DoInstall(1)
print "pm.DoInstall() returned: %s"% res



