import apt

if __name__ == "__main__":
    progress = apt.progress.OpTextProgress()
    cache = apt.Cache(progress)
    print cache
    for name in cache.keys():
        pkg = cache[name]
        if pkg.IsUpgradable():
            pkg.MarkInstall()
    for pkg in cache.GetChanges():
        print pkg.Name()
    print "Broken: %s " % cache._depcache.BrokenCount
    
