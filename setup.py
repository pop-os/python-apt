#! /usr/bin/env python
# $Id: setup.py,v 1.2 2002/01/08 07:13:21 jgg Exp $

from distutils.core import setup, Extension
from distutils.sysconfig import parse_makefile
from DistUtilsExtra.command import *
import glob
import os
import os.path
import pydoc
import shutil
import string
import sys

def build_docs(dir="html", modules=["apt","aptsources"]):
    htmldir = os.path.join(os.getcwd(), dir)
    for d in modules:
        for (dirpath, dirnames, filenames) in os.walk(d):
            pydoc.writedoc(dirpath.replace("/","."))
            for file in filenames:
                if not file.endswith(".py"):
                    continue
                if file in ["__init__.py"]:
                    continue
                pydoc.writedoc(dirpath.replace("/",".")+"."+file.split(".py")[0])
    if not os.path.exists(htmldir):
        os.mkdir(htmldir)
    for f in glob.glob("*.html"):
        shutil.move(f, htmldir)
    return True

# The apt_pkg module
files = map(lambda source: "python/"+source,
            string.split(parse_makefile("python/makefile")["APT_PKG_SRC"]))
apt_pkg = Extension("apt_pkg", files, libraries=["apt-pkg"]);

# The apt_inst module
files = map(lambda source: "python/"+source,
            string.split(parse_makefile("python/makefile")["APT_INST_SRC"]))
apt_inst = Extension("apt_inst", files, libraries=["apt-pkg","apt-inst"]);

# Replace the leading _ that is used in the templates for translation
templates = []
if not os.path.exists("build/data/templates/"):
    os.makedirs("build/data/templates")
for template in glob.glob('data/templates/*.info.in'):
    source = open(template, "r")
    build = open(os.path.join("build", template[:-3]), "w")
    lines = source.readlines()
    for line in lines:
        build.write(line.lstrip("_"))
    source.close()
    build.close()

# build doc
if sys.argv[1] == "build":
    build_docs()

setup(name="python-apt", 
      version="0.6.17",
      description="Python bindings for APT",
      author="APT Development Team",
      author_email="deity@lists.debian.org",
      ext_modules=[apt_pkg,apt_inst],
      packages=['apt', 'apt.gtk', 'aptsources'],
      data_files = [('share/python-apt/templates',
                    glob.glob('build/data/templates/*.info')),
                    ('share/python-apt/templates',
                    glob.glob('data/templates/*.mirrors'))],
      cmdclass = { "build" : build_extra.build_extra,
                   "build_i18n" :  build_i18n.build_i18n },
      license = 'GNU GPL',
      platforms = 'posix'
      )
