# DistUpgradeViewText.py 
#  
#  Copyright (c) 2004-2006 Canonical
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
import logging
import time
import subprocess

import apt
import apt_pkg
import os

from apt.progress import InstallProgress
from DistUpgradeView import DistUpgradeView, FuzzyTimeToStr, estimatedDownloadTime

import gettext
from gettext import gettext as _

class TextCdromProgressAdapter(apt.progress.CdromProgress):
    """ Report the cdrom add progress  """
    def update(self, text, step):
        """ update is called regularly so that the gui can be redrawn """
        if text:
          print "%s (%f)" % (text, step/float(self.totalSteps)*100)
    def askCdromName(self):
        return (False, "")
    def changeCdrom(self):
        return False


class DistUpgradeViewText(DistUpgradeView):
    " text frontend of the distUpgrade tool "
    def __init__(self, datadir=None):
        if not datadir:
          localedir=os.path.join(os.getcwd(),"mo")
        else:
          localedir="/usr/share/locale/update-manager"

        try:
          gettext.bindtextdomain("update-manager", localedir)
          gettext.textdomain("update-manager")
        except Exception, e:
          logging.warning("Error setting locales (%s)" % e)
        
        self.last_step = 0 # keep a record of the latest step
        self._opCacheProgress = apt.progress.OpTextProgress()
        self._fetchProgress = apt.progress.TextFetchProgress()
        self._cdromProgress = TextCdromProgressAdapter()
        self._installProgress = apt.progress.InstallProgress()
        sys.excepthook = self._handleException

    def _handleException(self, type, value, tb):
      import traceback
      lines = traceback.format_exception(type, value, tb)
      logging.error("not handled expection:\n%s" % "\n".join(lines))
      self.error(_("A fatal error occured"),
                 _("Please report this as a bug and include the "
                   "files /var/log/dist-upgrade/main.log and "
                   "/var/log/dist-upgrade/apt.log "
                   "in your report. The upgrade aborts now.\n"
                   "Your original sources.list was saved in "
                   "/etc/apt/sources.list.distUpgrade."),
                 "\n".join(lines))
      sys.exit(1)

    def getFetchProgress(self):
        return self._fetchProgress
    def getInstallProgress(self, cache):
        self._installProgress._cache = cache
        return self._installProgress
    def getOpCacheProgress(self):
        return self._opCacheProgress
    def getCdromProgress(self):
        return self._cdromProgress
    def updateStatus(self, msg):
      print msg
    def abort(self):
      print _("Aborting")
    def setStep(self, step):
      self.last_step = step
    def information(self, summary, msg, extended_msg=None):
      print summary
      print msg
      if extended_msg:
        print extended_msg
    def error(self, summary, msg, extended_msg=None):
      print summary
      print msg
      if extended_msg:
        print extended_msg
      return False
    def confirmChanges(self, summary, changes, downloadSize, actions=None):
      DistUpgradeView.confirmChanges(self, summary, changes, downloadSize, actions)
      pkgs_remove = len(self.toRemove)
      pkgs_inst = len(self.toInstall)
      pkgs_upgrade = len(self.toUpgrade)
      msg = ""

      if pkgs_remove > 0:
        # FIXME: make those two seperate lines to make it clear
        #        that the "%" applies to the result of ngettext
        msg += gettext.ngettext("%d package is going to be removed.",
                                "%d packages are going to be removed.",
                                pkgs_remove) % pkgs_remove
        msg += " "
        if pkgs_inst > 0:
          msg += gettext.ngettext("%d new package is going to be "
                                  "installed.",
                                  "%d new packages are going to be "
                                  "installed.",pkgs_inst) % pkgs_inst
          msg += " "
        if pkgs_upgrade > 0:
          msg += gettext.ngettext("%d package is going to be upgraded.",
                                  "%d packages are going to be upgraded.",
                                  pkgs_upgrade) % pkgs_upgrade
          msg +=" "
        if downloadSize > 0:
          msg += _("\n\nYou have to download a total of %s. ") %\
                 apt_pkg.SizeToStr(downloadSize)
          msg += estimatedDownloadTime(downloadSize)
          msg += "."
        if (pkgs_upgrade + pkgs_inst + pkgs_remove) > 100:
          msg += "\n\n%s" % _("Fetching and installing the upgrade can take several hours and "\
                              "cannot be canceled at any time later.")

      # Show an error if no actions are planned
      if (pkgs_upgrade + pkgs_inst + pkgs_remove) < 1:
        # FIXME: this should go into DistUpgradeController
        summary = _("Your system is up-to-date")
        msg = _("There are no upgrades available for your system. "
                "The upgrade will now be canceled.")
        self.error(summary, msg)
        return False

      return self.askYesNoQuestion(summary, msg)

    def askYesNoQuestion(self, summary, msg):
      print summary
      print msg
      print _("Continue [Yn] "),
      res = sys.stdin.readline()
      if res.strip().lower().startswith("y"):
        return True
      return False
    
    def confirmRestart(self):
      return self.askYesNoQuestion(_("Restart required"),
                                   _("To fully ugprade, please restart"))


if __name__ == "__main__":
  
  view = DistUpgradeViewText()
  view.confirmChanges("xx",[], 100)
  sys.exit(0)

  fp = apt.progress.TextFetchProgress()
  ip = apt.progress.InstallProgress()

  cache = apt.Cache()
  for pkg in sys.argv[1:]:
    cache[pkg].markInstall()
  cache.commit(fp,ip)
  
  #sys.exit(0)
  view.getTerminal().call(["dpkg","--configure","-a"])
  #view.getTerminal().call(["ls","-R","/usr"])
  view.error("short","long",
             "asfds afsdj af asdf asdf asf dsa fadsf asdf as fasf sextended\n"
             "asfds afsdj af asdf asdf asf dsa fadsf asdf as fasf sextended\n"
             "asfds afsdj af asdf asdf asf dsa fadsf asdf as fasf sextended\n"
             "asfds afsdj af asdf asdf asf dsa fadsf asdf as fasf sextended\n"
             "asfds afsdj af asdf asdf asf dsa fadsf asdf as fasf sextended\n"
             "asfds afsdj af asdf asdf asf dsa fadsf asdf as fasf sextended\n"
             "asfds afsdj af asdf asdf asf dsa fadsf asdf as fasf sextended\n"
             )
  view.confirmChanges("xx",[], 100)
  print view.askYesNoQuestion("hello", "Icecream?")
