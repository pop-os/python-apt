#!/usr/bin/python
# example how to install in a custom terminal widget

import apt_pkg
import sys, os
import copy

import pygtk
pygtk.require('2.0')
import gtk
import vte
import time

from progress import OpProgress, FetchProgress, InstallProgress

class TermInstallProgress(InstallProgress):
    def UpdateInterface(self):
        while gtk.events_pending():
            gtk.main_iteration()
    def FinishUpdate(self):
	    sys.stdin.readline()

# init
apt_pkg.init()

progress = OpProgress()
cache = apt_pkg.GetCache(progress)
print "Available packages: %s " % cache.PackageCount

# get depcache
depcache = apt_pkg.GetDepCache(cache)
depcache.ReadPinFile()
depcache.Init(progress)

# do something
fprogress = FetchProgress()
iprogress = TermInstallProgress()


window = gtk.Window(gtk.WINDOW_TOPLEVEL)
window.show()
term = vte.Terminal()
term.show()
window.add(term)
# can be used to set a custom fork method (like vte.Terminal.forkpty)
# see also gnome bug: #169201
iprogress.fork = term.forkpty

# show the interface
while gtk.events_pending():
	gtk.main_iteration()
  

iter = cache["3dchess"]
print "\n%s"%iter

# install or remove, the importend thing is to keep us busy :)
if iter.CurrentVer == None:
	depcache.MarkInstall(iter)
else:
	depcache.MarkDelete(iter)
depcache.Commit(fprogress, iprogress)

print "Exiting"
sys.exit(0)



