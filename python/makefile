# -*- make -*-
BASE=..
SUBDIR=python

# Bring in the default rules
include ../buildlib/defaults.mak

# The apt_pkg module
MODULE=apt_pkg
SLIBS = -lapt-pkg 
LIB_MAKES = apt-pkg/makefile
SOURCE = apt_pkgmodule.cc configuration.cc generic.cc tag.cc string.cc \
         cache.cc pkgrecords.cc
include $(PYTHON_H)

# The apt_int module.. 
MODULE=apt_inst
SLIBS = -lapt-inst -lapt-pkg
LIB_MAKES = apt-inst/makefile
SOURCE = apt_instmodule.cc tar.cc generic.cc
include $(PYTHON_H)
