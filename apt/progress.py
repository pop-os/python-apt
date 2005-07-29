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
    """ Abstract class to implement reporting on cache opening """
    def __init__(self):
        pass
    def Update(self, percent):
        pass
    def Done(self):
        pass

class OpTextProgress(OpProgress):
    """ A simple text based cache open reporting class """
    def __init__(self):
        OpProgress.__init__(self)
    def Update(self, percent):
        sys.stdout.write("\r%s: %.2i  " % (self.Op,percent))
        sys.stdout.flush()
    def Done(self):
        sys.stdout.write("\r%s: Done\n" % self.Op)



class FetchProgress:
    def __init__(self):
        pass
    
    def Start(self):
        pass
    
    def Stop(self):
        pass
    
    def UpdateStatus(self, uri, descr, shortDescr, status):
        pass

    def Pulse(self):
        pass

    def MediaChange(self, medium, drive):
        pass

class InstallProgress:
    def __init__(self):
        pass
    def StartUpdate(self):
        pass
    def FinishUpdate(self):
        pass
    def UpdateInterface(self):
        pass


class CdromProgress:
    def __init__(self):
        pass
    def Update(self, text, step):
        """ update is called regularly so that the gui can be redrawn """
        pass
    def AskCdromName(self):
        pass
    def ChangeCdrom(self):
        pass

# module test code
if __name__ == "__main__":
    import apt_pkg
    apt_pkg.init()
    progress = OpTextProgress()
    cache = apt_pkg.GetCache(progress)
    depcache = apt_pkg.GetDepCache(cache)
    depcache.Init(progress)
