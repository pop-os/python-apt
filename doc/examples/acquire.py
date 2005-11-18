import apt
import apt_pkg
import os

apt_pkg.init()

cache = apt_pkg.GetCache()
depcache = apt_pkg.GetDepCache(cache)

recs = apt_pkg.GetPkgRecords(cache)
list = apt_pkg.GetPkgSourceList()
list.ReadMainList()

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

pm.GetArchives(fetcher,list,recs)

for item in fetcher.Items:
    print "%s -> %s:\n Status: %s Complete: %s IsTrusted: %s" % (item.DescURI,
                                                                 item.DestFile,
                                                                 item.Status,
                                                                 item.Complete,
                                                                 item.IsTrusted)
    print
                                                         

res = fetcher.Run()
print "fetcher.Run() returned: %s" % res

