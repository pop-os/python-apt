# DistUpgradeFetcher.py 
#  
#  Copyright (c) 2006 Canonical
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

import pygtk
pygtk.require('2.0')
import gtk
import os
import apt_pkg
import tarfile
import urllib2
import tempfile
import shutil
import GnuPGInterface
from gettext import gettext as _

import GtkProgress
from ReleaseNotesViewer import ReleaseNotesViewer
from Common.utils import *

class DistUpgradeFetcher(object):

    def __init__(self, parent, new_dist):
        self.parent = parent
        self.window_main = parent.window_main
        self.new_dist = new_dist

    def showReleaseNotes(self):
      # FIXME: care about i18n! (append -$lang or something)
      if self.new_dist.releaseNotesURI != None:
          uri = self.new_dist.releaseNotesURI
          self.window_main.set_sensitive(False)
          self.window_main.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
          while gtk.events_pending():
              gtk.main_iteration()

          # download/display the release notes
          # FIXME: add some progress reporting here
          res = gtk.RESPONSE_CANCEL
          try:
              release_notes = urllib2.urlopen(uri)
              notes = release_notes.read()
              textview_release_notes = ReleaseNotesViewer(notes)
              textview_release_notes.show()
              self.parent.scrolled_notes.add(textview_release_notes)
              self.parent.dialog_release_notes.set_transient_for(self.window_main)
              res = self.parent.dialog_release_notes.run()
              self.parent.dialog_release_notes.hide()
          except urllib2.HTTPError:
              primary = "<span weight=\"bold\" size=\"larger\">%s</span>" % \
                        _("Could not find the release notes")
              secondary = _("The server may be overloaded. ")
              dialog = gtk.MessageDialog(self.window_main,gtk.DIALOG_MODAL,
                                         gtk.MESSAGE_ERROR,gtk.BUTTONS_CLOSE,"")
              dialog.set_title("")
              dialog.set_markup(primary);
              dialog.format_secondary_text(secondary);
              dialog.run()
              dialog.destroy()
          except IOError:
              primary = "<span weight=\"bold\" size=\"larger\">%s</span>" % \
                        _("Could not download the release notes")
              secondary = _("Please check your internet connection.")
              dialog = gtk.MessageDialog(self.window_main,gtk.DIALOG_MODAL,
                                         gtk.MESSAGE_ERROR,gtk.BUTTONS_CLOSE,"")
              dialog.set_title("")
              dialog.set_markup(primary);
              dialog.format_secondary_text(secondary);
              dialog.run()
              dialog.destroy()
          self.window_main.set_sensitive(True)
          self.window_main.window.set_cursor(None)
          # user clicked cancel
          if res == gtk.RESPONSE_CANCEL:
              return False
      return True

    def authenticate(self):
        if self.new_dist.upgradeToolSig:
            f = self.tmpdir+"/"+os.path.basename(self.new_dist.upgradeTool)
            sig = self.tmpdir+"/"+os.path.basename(self.new_dist.upgradeToolSig)
            print "authenticate '%s' against '%s' " % (f,sig)
            if not self.gpgauthenticate(f, sig):
                return False

        # we may return False here by default if we want to make a sig
        # mandatory
        return True

    def gpgauthenticate(self, file, signature,
                        keyring='/etc/apt/trusted.gpg'):
        """ authenticated a file against a given signature, if no keyring
            is given use the apt default keyring
        """
        gpg = GnuPGInterface.GnuPG()
        gpg.options.extra_args = ['--no-options',
                                  '--no-default-keyring',
                                  '--keyring', keyring]
        proc = gpg.run(['--verify', signature, file],
                       create_fhs=['status','logger','stderr'])
        gpgres = proc.handles['status'].read()
        try:
            proc.wait()
        except IOError,e:
            # gnupg returned a problem (non-zero exit)
            print "exception from gpg: %s" % e
            return False
        if "VALIDSIG" in gpgres:
            return True
        print "invalid result from gpg:"
        print gpgres
        return False

    def extractDistUpgrader(self):
          # extract the tarbal
          print "extracting '%s'" % (self.tmpdir+"/"+os.path.basename(self.uri))
          tar = tarfile.open(self.tmpdir+"/"+os.path.basename(self.uri),"r")
          for tarinfo in tar:
              tar.extract(tarinfo)
          tar.close()
          return True

    def verifyDistUprader(self):
        # FIXME: check a internal dependency file to make sure
        #        that the script will run correctly
          
        # see if we have a script file that we can run
        self.script = script = "%s/%s" % (self.tmpdir, self.new_dist.name)
        if not os.path.exists(script):
            # no script file found in extracted tarbal
            primary = "<span weight=\"bold\" size=\"larger\">%s</span>" % \
                      _("Could not run the upgrade tool")
            secondary = _("This is most likely a bug in the upgrade tool. "
                          "Please report it as a bug")
            dialog = gtk.MessageDialog(self.window_main,gtk.DIALOG_MODAL,
                                       gtk.MESSAGE_ERROR,gtk.BUTTONS_CLOSE,"")
            dialog.set_title("")
            dialog.set_markup(primary);
            dialog.format_secondary_text(secondary);
            dialog.run()
            dialog.destroy()
            return False
        return True

    def fetchDistUpgrader(self):
        # now download the tarball with the upgrade script
        self.tmpdir = tmpdir = tempfile.mkdtemp()
        os.chdir(tmpdir)

        # turn debugging on here (if required)
        #apt_pkg.Config.Set("Debug::Acquire::http","1")

        progress = GtkProgress.GtkFetchProgress(self.parent,
                                                _("Downloading the upgrade "
                                                  "tool"),
                                                _("The upgrade tool will "
                                                  "guide you through the "
                                                  "upgrade process."))
        fetcher = apt_pkg.GetAcquire(progress)

        if self.new_dist.upgradeToolSig != None:
            uri = self.new_dist.upgradeToolSig
            af = apt_pkg.GetPkgAcqFile(fetcher,uri, descr=_("Upgrade tool signature"))
        if self.new_dist.upgradeTool != None:
            self.uri = self.new_dist.upgradeTool
            af = apt_pkg.GetPkgAcqFile(fetcher,self.uri, descr=_("Upgrade tool"))
            if fetcher.Run() != fetcher.ResultContinue:
                return False
            return True
        return False

    def runDistUpgrader(self):
        #print "runing: %s" % script
        if os.getuid() != 0:
            os.execv("/usr/bin/gksu",["gksu",self.script])
        else:
            os.execv(self.script,[self.script])

    def cleanup(self):
      # cleanup
      os.chdir("..")
      # del tmpdir
      shutil.rmtree(self.tmpdir)

    def run(self):
        # see if we have release notes
        if not self.showReleaseNotes():
            return
        if not self.fetchDistUpgrader():
            error(self.window_main,
                  _("Failed to fetch"),
                  _("Fetching the upgrade failed. There may be a network "
                    "problem. "))
            return
        if not self.extractDistUpgrader():
            error(self.window_main,
                  _("Failed to extract"),
                  _("Extracting the upgrade failed. There may be a problem "
                  "with the network or with the server. "))
                  
            return
        if not self.verifyDistUprader():
            error(self.window_main,
                  _("Verfication failed"),
                  _("Verfing the upgrade failed.  There may be a problem "
                    "with the network or with the server. "))
            self.cleanup()
            return
        if not self.authenticate():
            error(self.window_main,
                  _("Authentication failed"),
                  _("Authenticating the upgrade failed. There may be a problem "
                    "with the network or with the server. "))
            self.cleanup()
            return
        self.runDistUpgrader()


if __name__ == "__main__":
    error(None, "summary","message")
    d = DistUpgradeFetcher(None,None)
    print d.authenticate('/tmp/Release','/tmp/Release.gpg')

