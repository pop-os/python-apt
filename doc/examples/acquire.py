import apt_pkg

apt_pkg.init()

cache = apt_pkg.GetCache()
depcache = apt_pkg.GetDepCache(cache)

recs = apt_pkg.GetPkgRecords(cache)
list = apt_pkg.GetPkgSourceList()
list.ReadMainList()

pkg = cache["3ddesktop"]
depcache.MarkInstall(pkg)

fetcher = apt_pkg.GetAcquire()
pm = apt_pkg.GetPackageManager(depcache)

print pm
print fetcher

pm.GetArchives(fetcher,list,recs)

fetcher.Run()

