#!/usr/bin/env python
from distutils.core import setup
import glob, os, commands, sys
from DistUtilsExtra.distutils_extra import build_extra, build_l10n

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

setup(
    name = 'python-aptsources',
    version = '0.0.1',
    description = 'Abstratcion of the sources.list',
    packages = ['AptSources'],
    data_files = [('share/python-aptsources/templates',
                  glob.glob('build/data/templates/*.info'))],
    license = 'GNU GPL',
    platforms = 'posix',
    cmdclass = { "build" : build_extra,
                 "build_l10n" :  build_l10n }
)
