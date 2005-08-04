# Progress.py - progress reporting classes
#  
#  Copyright (c) 2005 Canonical
#  
#  Author: Michael Vogt <michael.vogt@ubuntu.com>
# 
#  This program is free software; you can redistribute it and/or 
#  modify it under the terms of the GNU General Public License as 
#  published by the Free Software Foundation; either version 2 of the
#  License, or (at your option) any later version.
# 
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
# 
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
#  USA

import sys

class OpProgress:
    """ Abstract class to implement reporting on cache opening
        Subclass this class to implement simple Operation progress reporting
    """
    def __init__(self):
        pass
    def update(self, percent):
        pass
    def done(self):
        pass

class OpTextProgress(OpProgress):
    """ A simple text based cache open reporting class """
    def __init__(self):
        OpProgress.__init__(self)
    def update(self, percent):
        sys.stdout.write("\r%s: %.2i  " % (self.subOp,percent))
        sys.stdout.flush()
    def done(self):
        sys.stdout.write("\r%s: Done\n" % self.op)



class FetchProgress:
    """ Report the download/fetching progress
        Subclass this class to implement fetch progress reporting
    """
    def __init__(self):
        pass
    
    def start(self):
        pass
    
    def stop(self):
        pass
    
    def updateStatus(self, uri, descr, shortDescr, status):
        pass

    def pulse(self):
        """ called periodically (to update the gui) """
        return True

    def mediaChange(self, medium, drive):
        pass



class InstallProgress:
    """ Report the install progress
        Subclass this class to implement install progress reporting
    """
    def __init__(self):
        pass
    def startUpdate(self):
        pass
    def finishUpdate(self):
        pass
    def updateInterface(self):
        pass


class CdromProgress:
    """ Report the cdrom add progress
        Subclass this class to implement cdrom add progress reporting
    """
    def __init__(self):
        pass
    def update(self, text, step):
        """ update is called regularly so that the gui can be redrawn """
        pass
    def askCdromName(self):
        pass
    def changeCdrom(self):
        pass

# module test code
if __name__ == "__main__":
    import apt_pkg
    apt_pkg.init()
    progress = OpTextProgress()
    cache = apt_pkg.GetCache(progress)
    depcache = apt_pkg.GetDepCache(cache)
    depcache.Init(progress)
