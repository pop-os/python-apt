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

import apt
import logging
import time
from DistUpgradeView import DistUpgradeView

class NonInteractiveInstallProgress(apt.progress.InstallProgress):
    def error(self, pkg, errormsg):
        logging.error("got a error from dpkg for pkg: '%s': '%s'" % (pkg, errormsg))
    def conffile(self, current, new):
        logging.debug("got a conffile-prompt from dpkg for file: '%s'" % current)
    def updateInterface(self):
	apt.progress.InstallProgress.updateInterface(self)
	time.sleep(0.001)

class DistUpgradeViewNonInteractive(DistUpgradeView):
    " non-interactive version of the upgrade view "
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
        return NonInteractiveInstallProgress()
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
        DistUpgradeView.confirmChanges(self, summary, changes, downloadSize)
	logging.debug("toinstall: '%s'" % self.toInstall)
        logging.debug("toupgrade: '%s'" % self.toUpgrade)
        logging.debug("toremove: '%s'" % self.toRemove)
        return True
    def askYesNoQuestion(self, summary, msg):
        " ask a Yes/No question and return True on 'Yes' "
        return True
    def confirmRestart(self):
        " generic ask about the restart, can be overriden "
        return False
    def error(self, summary, msg, extended_msg=None):
        " display a error "
        logging.error("%s %s (%s)" % (summary, msg, extended_msg))
    
