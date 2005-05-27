import apt

if __name__ == "__main__":
    progress = apt.progress.OpTextProgress()
    cache = apt.Cache(progress)
    print "Packages count: %s" % len(cache.keys())
    for key in cache.keys():
        p = cache[key]
        if p == None or p.Name() == None or p.Name == "" or p._pkg == None:
            print "Something strange is going on" 
