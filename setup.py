#! /usr/bin/env python
# $Id: setup.py,v 1.1 2002/01/08 06:42:46 jgg Exp $

from distutils.core import setup, Extension

# The apt_pkg module
files = ["apt_pkgmodule.cc","configuration.cc","generic.cc","tag.cc",
         "cache.cc","string.cc","pkgrecords.cc"]
for i in range(0,len(files)):
    files[i] = "python/"+ files[i];
apt_pkg = Extension("apt_pkg", files,
		libraries=["apt-pkg"]);

# The apt_inst module
files = ["apt_instmodule.cc","tar.cc","generic.cc"];
for i in range(0,len(files)):
    files[i] = "python/"+ files[i];
apt_inst = Extension("apt_inst", files,
		libraries=["apt-pkg","apt-inst"]);
		
setup(name="python-apt", 
      version="0.5.4",
      description="Python bindings for APT",
      author="APT Development Team",
      author_email="deity@lists.debian.org",
      ext_modules=[apt_pkg,apt_inst])
      
