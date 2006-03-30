# DistUpgradeView.py 
#  
#  Copyright (c) 2004,2005 Canonical
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

class DumbTerminal(object):
    def run(self, cmd):
        " expects a command in the subprocess style (as a list) "
        subprocess.call(cmd)
        

class DistUpgradeView(object):
    " abstraction for the upgrade view "
    def __init__(self):
        pass
    def getOpCacheProgress(self):
        " return a OpProgress() subclass for the given graphic"
        return apt.progress.OpProgress()
    def getFetchProgress(self):
        " return a fetch progress object "
        return apt.progress.FetchProgress()
    def getInstallProgress(self):
        " return a install progress object "
        return apt.progress.InstallProgress()
    def getTerminal(self):
        return DumbTerminal()
    def updateStatus(self, msg):
        """ update the current status of the distUpgrade based
            on the current view
        """
        pass
    def setStep(self, step):
        """ we have 5 steps current for a upgrade:
        1. Analyzing the system
        2. Updating repository information
        3. Performing the upgrade
        4. Post upgrade stuff
        5. Complete
        """
        pass
    def confirmChanges(self, summary, changes, downloadSize):
        """ display the list of changed packages (apt.Package) and
            return if the user confirms them
        """
        self.toInstall = []
        self.toUpgrade = []
        self.toRemove = []
        for pkg in changes:
            if pkg.markedInstall: self.toInstall.append(pkg.name)
            elif pkg.markedUpgrade: self.toUpgrade.append(pkg.name)
            elif pkg.markedDelete: self.toRemove.append(pkg.name)
        # no downgrades, re-installs 
        assert(len(self.toInstall)+len(self.toUpgrade)+len(self.toRemove) == len(changes))
    def askYesNoQuestion(self, summary, msg):
        " ask a Yes/No question and return True on 'Yes' "
        pass
    def confirmRestart(self):
        " generic ask about the restart, can be overriden "
        summary = _("Reboot required")
        msg =  _("The upgrade is finished and "
                 "a reboot is required. "
                 "Do you want to do this "
                 "now?")
        return self.askYesNoQuestion(summary, msg)
    def error(self, summary, msg, extended_msg=None):
        " display a error "
        pass
    
