#!/usr/bin/python

import apt_pkg

apt_pkg.init()

sources = apt_pkg.GetPkgSrcRecords()
while sources.Lookup('hello'):
	print sources.Package, sources.Version, sources.Maintainer, sources.Section, `sources.Binaries`
