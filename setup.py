#! /usr/bin/env python
# $Id: setup.py,v 1.2 2002/01/08 07:13:21 jgg Exp $

from distutils.core import setup, Extension
from distutils.sysconfig import parse_makefile
import string, glob


# The apt_pkg module
files = map(lambda source: "python/"+source,
            string.split(parse_makefile("python/makefile")["APT_PKG_SRC"]))
apt_pkg = Extension("apt_pkg", files, libraries=["apt-pkg"]);

# The apt_inst module
files = map(lambda source: "python/"+source,
            string.split(parse_makefile("python/makefile")["APT_INST_SRC"]))
apt_inst = Extension("apt_inst", files, libraries=["apt-pkg","apt-inst"]);


setup(name="python-apt", 
      version="0.6.17",
      description="Python bindings for APT",
      author="APT Development Team",
      author_email="deity@lists.debian.org",
      ext_modules=[apt_pkg,apt_inst],
      packages=['apt']
      )
      
