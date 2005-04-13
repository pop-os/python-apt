#!/usr/bin/python

import apt_pkg
import sys


def get_source_pkg(pkg, records, depcache):
	# FIXME: use candidate version here
	version = depcache.GetCandidateVer(pkg)
	file, index = version.FileList.pop(0)
	records.Lookup((file, index))
	if records.SourcePkg != "":
		srcpkg = records.SourcePkg
	else:
		srcpkg = pkg.Name
	return srcpkg

# main
apt_pkg.init()
cache = apt_pkg.GetCache()
depcache = apt_pkg.GetDepCache(cache)
depcache.Init()
records = apt_pkg.GetPkgRecords(cache)
srcrecords = apt_pkg.GetPkgSrcRecords()

# base package that we use for build-depends calculation
if len(sys.argv) < 2:
	print "need a pkgname as argument"
base = cache[sys.argv[1]]
all_build_depends = set()

depends = base.CurrentVer.DependsList
for dep in depends["Depends"]:
	pkg = dep[0].TargetPkg
	srcpkg_name = get_source_pkg(pkg, records, depcache)
	srcrec = srcrecords.Lookup(srcpkg_name)
	if srcrec:
		#print srcrecords.Package
		#print srcrecords.Binaries
		bd = srcrecords.BuildDepends
		#print "%s: %s " % (srcpkg_name, bd)
		for b in bd:
			all_build_depends.add(b[0])
			

print "\n".join(all_build_depends)
