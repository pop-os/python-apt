#!/usr/bin/python
# example how to deal with the depcache

import apt_pkg
import sys, os
import copy

from progress import CdromProgress


# init
apt_pkg.init()

cdrom = apt_pkg.GetCdrom()
print cdrom

progress = CdromProgress()
apt_pkg.Config.Set("APT::CDROM::Rename", "True")

cdrom.Add(progress)

print "Exiting"
sys.exit(0)




