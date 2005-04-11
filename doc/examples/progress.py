import apt_pkg
import sys
import time
import string

class OpProgress:
    def __init__(self):
        self.last = 0.0

    def Update(self, percent):
        if (self.last + 1.0) <= percent:
            sys.stdout.write("\rProgress: %i.2          " % (percent))
            self.last = percent
        if percent >= 100:
            self.last = 0.0

    def Done(self):
        self.last = 0.0
        print "\rDone                      "


class FetchProgress:
    def __init__(self):
        pass
    
    def Start(self):
        pass
    
    def Stop(self):
        pass
    
    def UpdateStatus(self, uri, descr, shortDescr, status):
        print "UpdateStatus: '%s' '%s' '%s' '%i'" % (uri,descr,shortDescr, status)
    def Pulse(self):
        print "Pulse: CPS: %s/s; Bytes: %s/%s; Item: %s/%s" % (apt_pkg.SizeToStr(self.CurrentCPS), apt_pkg.SizeToStr(self.CurrentBytes), apt_pkg.SizeToStr(self.TotalBytes), self.CurrentItems, self.TotalItems)

    def MediaChange(self, medium, drive):
	print "Please insert medium %s in drive %s" % (medium, drive)
	sys.stdin.readline()
        #return False


class InstallProgress:
    def __init__(self):
        pass
    def StartUpdate(self):
        print "StartUpdate"
    def FinishUpdate(self):
        print "FinishUpdate"
    def UpdateInterface(self):
        # usefull to e.g. redraw a GUI
        time.sleep(0.1)


class CdromProgress:
    def __init__(self):
        pass
    # update is called regularly so that the gui can be redrawn
    def Update(self, text, step):
        # check if we actually have some text to display
        if text != "":
            print "Update: %s %s" % (string.strip(text), step)
    def AskCdromName(self):
        print "Please enter cd-name: ",
        cd_name = sys.stdin.readline()
        return (True, string.strip(cd_name))
    def ChangeCdrom(self):
        print "Please insert cdrom and press <ENTER>"
        answer =  sys.stdin.readline()
        return True
