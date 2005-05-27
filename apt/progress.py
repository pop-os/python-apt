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
