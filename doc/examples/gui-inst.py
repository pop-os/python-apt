#!/usr/bin/python
# example how to install in a custom terminal widget
# see also gnome bug: #169201

import apt_pkg
import sys, os
import copy

import pygtk
pygtk.require('2.0')
import gtk
import vte
import time

from progress import OpProgress, FetchProgress, InstallProgress

class GuiFetchProgress(gtk.Window, FetchProgress):
    def __init__(self):
	gtk.Window.__init__(self)
	self.vbox = gtk.VBox()
	self.vbox.show()
	self.add(self.vbox)
	self.progress = gtk.ProgressBar()
	self.progress.show()
	self.label = gtk.Label()
	self.label.show()
	self.vbox.pack_start(self.progress)
	self.vbox.pack_start(self.label)
	self.resize(300,100)
    def Start(self):
	self.progress.set_fraction(0)
        self.show()
    def Stop(self):
	self.hide()
    def Pulse(self):
	self.label.set_text("Speed: %s/s" % apt_pkg.SizeToStr(self.CurrentCPS))
	self.progress.set_fraction(self.CurrentBytes/self.TotalBytes)
	while gtk.events_pending():
		gtk.main_iteration()

class TermInstallProgress(InstallProgress, gtk.Window):
    def __init__(self):
	gtk.Window.__init__(self)
	self.show()
	self.term = vte.Terminal()
	self.term.show()
	self.add(self.term)
    def Start(self):
	self.progress.set_fraction(0)
        self.show()
    def Stop(self):
	self.hide()
    def UpdateInterface(self):
        while gtk.events_pending():
            gtk.main_iteration()
    def FinishUpdate(self):
	sys.stdin.readline()
    def fork(self):
	return self.term.forkpty()


# init
apt_pkg.init()

progress = OpProgress()
cache = apt_pkg.GetCache(progress)
print "Available packages: %s " % cache.PackageCount


# get depcache
depcache = apt_pkg.GetDepCache(cache)
depcache.ReadPinFile()
depcache.Init(progress)

# update the cache
fprogress = GuiFetchProgress()
iprogress = TermInstallProgress()

# update the cache
#cache.Update(fprogress)
#cache = apt_pkg.GetCache(progress)
#depcache = apt_pkg.GetDepCache(cache)
#depcache.ReadPinFile()
#depcache.Init(progress)


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



