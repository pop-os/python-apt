
class OpProgress:
    def __init__(self):
        pass
    def Update(self, percent):
        pass
    def Done(self):
        pass

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
