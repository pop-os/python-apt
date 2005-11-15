#!/usr/bin/env python

from distutils.core import setup
import glob
import os

GETTEXT_NAME="update-manager"
I18NFILES = []
for filepath in glob.glob("po/mo/*/LC_MESSAGES/*.mo"):
    lang = filepath[len("po/mo/"):]
    targetpath = os.path.dirname(os.path.join("share/locale",lang))
    I18NFILES.append((targetpath, [filepath]))

# HACK: make sure that the mo files are generated and up-to-date
os.system("cd po; make update-po")
# do the same for the desktop files
os.system("cd date; make")
# and channels
os.system("cd channels; make")
    
setup(name='update-manager',
      version='0.1',
      packages=['SoftwareProperties','UpdateManager','UpdateManagerCommon'],
      scripts=['gnome-software-properties','src/update-manager'],
      data_files=[('share/update-manager/glade',
                   glob.glob("data/*.glade")),
                  ('share/update-manager/channels',
                   glob.glob("channels/*")),
                  ('share/applications',
                   ["data/update-manager.desktop",
                    "data/gnome-software-properties.desktop"]),
                  ('share/pixmaps',
                   ["data/update-manager.png"])]+I18NFILES,
      )


