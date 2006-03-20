#!/usr/bin/env python

from distutils.core import setup
import glob
import os

GETTEXT_NAME="update-manager"
HELPFILES = []
print "Setting up help files..."
for filepath in glob.glob("help/*"):
    lang = filepath[len("help/"):]
    print " Language: %s" % lang
    path_xml = "share/gnome/help/update-manager/" + lang
    path_figures = "share/gnome/help/update-manager/" + lang + "/figures/"
    HELPFILES.append((path_xml, (glob.glob("%s/*.xml" % filepath))))
    HELPFILES.append((path_figures, (glob.glob("%s/figures/*.png" % \
                                                filepath))))
HELPFILES.append(('share/omf/update-manager', glob.glob("help/*/*.omf")))

I18NFILES = []
for filepath in glob.glob("po/mo/*/LC_MESSAGES/*.mo"):
    lang = filepath[len("po/mo/"):]
    targetpath = os.path.dirname(os.path.join("share/locale",lang))
    I18NFILES.append((targetpath, [filepath]))

os.system("intltool-merge -d po data/update-manager.schemas.in"\
           " build/update-manager.schemas")


# HACK: make sure that the mo files are generated and up-to-date
os.system("cd po; make update-po")
# do the same for the desktop files
os.system("cd data; make")
# and channels
os.system("cd channels; make")
    
setup(name='update-manager',
      version='0.42.2',
      packages=[
                'SoftwareProperties',
                'UpdateManager',
                'UpdateManager.Common'
                ],
      scripts=[
               'gnome-software-properties',
               'update-manager'
               ],
      data_files=[
                  ('share/update-manager/glade',
                     glob.glob("data/*.glade")+
		      ["data/update-manager-logo.png",
                       "data/update-manager.png"]
                  ),
                  ('share/update-manager/channels',
                     glob.glob("channels/*")
                  ),
                  ('share/applications',
                     ["data/update-manager.desktop",
                      "data/gnome-software-properties.desktop"]
                  ),
                  ('share/gconf/schemas',
                  glob.glob("build/*.schemas")
                  ),
                  ('share/pixmaps',
                   ["data/update-manager.png"]
	          ),
                  ] + I18NFILES + HELPFILES,
      )


