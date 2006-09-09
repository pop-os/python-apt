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

ICONS = []
for size in glob.glob("data/icons/*"):
    for category in glob.glob("%s/*" % size):
        icons = []
        for icon in glob.glob("%s/*" % category):
            icons.append(icon)
        ICONS.append(("share/icons/hicolor/%s/%s" % \
                      (os.path.basename(size), \
                       os.path.basename(category)), \
                       icons))
print ICONS


for template in glob.glob("data/channels/*.info.in"):
    os.system("sed s/^_// data/channels/%s"
              " > build/%s" % (os.path.basename(template),
                  os.path.basename(template)[:-3]))
os.system("intltool-merge -d po data/mime/apt.xml.in"\
           " build/apt.xml")
os.system("intltool-merge -d po data/update-manager.schemas.in"\
           " build/update-manager.schemas")


# HACK: make sure that the mo files are generated and up-to-date
os.system("cd po; make update-po")
# do the same for the desktop files
os.system("cd data; make")
# and channels
os.system("cd data/channels; make")
    
setup(name='update-manager',
      version='0.42.2',
      packages=[
                'SoftwareProperties',
                'UpdateManager',
                'UpdateManager.Common',
                'DistUpgrade'
                ],
      scripts=[
               'software-properties',
               'update-manager'
               ],
      data_files=[
                  ('share/update-manager/glade',
                   glob.glob("data/glade/*.glade")+
                   glob.glob("DistUpgrade/*.glade")
                  ),
                  ('share/update-manager/',
                   glob.glob("DistUpgrade/*.cfg")+
                   glob.glob("DistUpgrade/*.cfg")
                  ),
                  ('share/doc/update-manager',
                     glob.glob("data/channels/README.channels")
                  ),
                  ('share/update-manager/channels',
                     glob.glob("build/*.info")
                  ),
                  ('share/applications',
                     ["data/update-manager.desktop",
                      "data/software-properties.desktop"]
                  ),
                  ('share/gconf/schemas',
                  glob.glob("build/*.schemas")
                  ),
                  ('share/mime/packages',
                   ["build/apt.xml"]
                  )
                  ] + I18NFILES + HELPFILES + ICONS,
      )
