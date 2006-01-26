# DistUpgradeViewGtk.py 
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

import pygtk
pygtk.require('2.0')
import gtk
import gtk.gdk
import gtk.glade
import vte
import gobject
import pango
import sys
import logging

import apt
import apt_pkg
import os

from apt.progress import InstallProgress
from DistUpgradeView import DistUpgradeView
from UpdateManager.Common.SimpleGladeApp import SimpleGladeApp, bindtextdomain

from gettext import gettext as _

def utf8(str):
  return unicode(str, 'latin1').encode('utf-8')

class GtkOpProgress(apt.progress.OpProgress):
  def __init__(self, progressbar):
      self.progressbar = progressbar
  def update(self, percent):
      #self._progressbar.show()
      #self.progressbar.set_text(self.op)
      self.progressbar.set_fraction(percent/100.0)
      while gtk.events_pending():
          gtk.main_iteration()
  def done(self):
      #self.progressbar.hide()
      self.progressbar.set_text(" ")


class GtkFetchProgressAdapter(apt.progress.FetchProgress):
    # FIXME: we really should have some sort of "we are at step"
    # xy in the gui
    # FIXME2: we need to thing about mediaCheck here too
    def __init__(self, parent):
        # if this is set to false the download will cancel
        self.status = parent.label_status
        self.progress = parent.progressbar_cache
    def mediaChange(self, medium, drive):
      #print "mediaChange %s %s" % (medium, drive)
      msg = _("Please insert '%s' into the drive '%s'" % (medium,drive))
      dialog = gtk.MessageDialog(parent=self.main,
                                 flags=gtk.DIALOG_MODAL,
                                 type=gtk.MESSAGE_QUESTION,
                                 buttons=gtk.BUTTONS_OK_CANCEL)
      dialog.set_markup(msg)
      res = dialog.run()
      #print res
      dialog.destroy()
      if  res == gtk.RESPONSE_OK:
        return True
      return False
    def start(self):
        #self.progress.show()
        self.progress.set_fraction(0)
        self.status.show()
    def stop(self):
        #self.progress.hide()
        self.progress.set_text(" ")
        self.status.set_text("")
    def pulse(self):
        # FIXME: move the status_str and progress_str into python-apt
        # (python-apt need i18n first for this)
        apt.progress.FetchProgress.pulse(self)
        self.progress.set_fraction(self.percent/100.0)
        currentItem = self.currentItems + 1
        if currentItem > self.totalItems:
            currentItem = self.totalItems

        if self.currentCPS > 0:
            self.status.set_text(_("Downloading file %li of %li with %s/s" % (currentItem, self.totalItems, apt_pkg.SizeToStr(self.currentCPS))))
            self.progress.set_text(_("%s remaining" % apt_pkg.TimeToStr(self.eta)))
        else:
            self.status.set_text(_("Downloading file %li of %li with unknown speed" % (currentItem, self.totalItems)))
            self.progress.set_text("  ")

        while gtk.events_pending():
            gtk.main_iteration()
        return True

class GtkInstallProgressAdapter(InstallProgress):
    def __init__(self,parent):
        InstallProgress.__init__(self)
        self.label_status = parent.label_status
        self.progress = parent.progressbar_cache
        self.expander = parent.expander_terminal
        self.term = parent._term
        self.parent = parent
        # setup the child waiting
        reaper = vte.reaper_get()
        reaper.connect("child-exited", self.child_exited)
    def startUpdate(self):
        self.finished = False
        # FIXME: add support for the timeout
        # of the terminal (to display something useful then)
        # -> longer term, move this code into python-apt 
        self.label_status.set_text(_("Installing updates ..."))
        self.progress.set_fraction(0.0)
        self.progress.set_text(" ")
        self.expander.set_sensitive(True)
        self.term.show()
        self.env = ["VTE_PTY_KEEP_FD=%s"% self.writefd,
                    "DEBIAN_FRONTEND=gnome",
                    "APT_LISTCHANGES_FRONTEND=none"]
    def error(self, pkg, errormsg):
        logging.error("got a error from dpkg for pkg: '%s': '%s'" % (pkg, errormsg))
        dialog = gtk.MessageDialog(self.parent.window_main, 0,
                                   gtk.MESSAGE_ERROR,
                                   gtk.BUTTONS_OK,"")
        summary = _("Error installing '%s'" % pkg)
        msg = _("During the install a error occured. This is usually a bug "
                "in the packages, please report it. See the message below "
                "for more information. ")
        msg="<big><b>%s</b></big>\n\n%s" % (summary,msg)
        dialog.set_markup(msg)
        dialog.vbox.set_spacing(6)
        if errormsg != None:
          scroll = gtk.ScrolledWindow()
          scroll.set_size_request(400,200)
          textview = gtk.TextView()
          textview.set_cursor_visible(False)
          textview.set_editable(False)
          textview.get_buffer().set_text(utf8(errormsg))
          textview.show()
          scroll.add(textview)
          scroll.show()
          dialog.vbox.pack_end(scroll)
        dialog.run()
        dialog.destroy()
    def conffile(self, current, new):
        logging.debug("got a conffile-prompt from dpkg for pkg: '%s'" % current)
        self.expander.set_expanded(True)
        pass
    def fork(self):
        pid = self.term.forkpty(envv=self.env)
        return pid
    def child_exited(self, term, pid, status):
        self.apt_status = os.WEXITSTATUS(status)
        self.finished = True
    def waitChild(self):
        while not self.finished:
            self.updateInterface()
        return self.apt_status
    def finishUpdate(self):
        #self.progress.hide()
        self.label_status.set_text("")
    def updateInterface(self):
        InstallProgress.updateInterface(self)
        self.progress.set_fraction(self.percent/100.0)
        self.label_status.set_text(self.status)
        while gtk.events_pending():
            gtk.main_iteration()


class GtkDistUpgradeView(DistUpgradeView,SimpleGladeApp):
    " gtk frontend of the distUpgrade tool "

      
    
    def __init__(self):
        # FIXME: i18n must be somewhere relative do this dir
        bindtextdomain("update-manager",os.path.join(os.getcwd(),"mo"))

        SimpleGladeApp.__init__(self, "DistUpgrade.glade",
                                None, domain="update-manager")
        self.window_main.set_keep_above(True)
        self._opCacheProgress = GtkOpProgress(self.progressbar_cache)
        self._fetchProgress = GtkFetchProgressAdapter(self)
        self._installProgress = GtkInstallProgressAdapter(self)
        # details dialog
        self.details_list = gtk.ListStore(gobject.TYPE_STRING)
        column = gtk.TreeViewColumn("")
        render = gtk.CellRendererText()
        column.pack_start(render, True)
        column.add_attribute(render, "markup", 0)
        self.treeview_details.append_column(column)
        self.treeview_details.set_model(self.details_list)
        self.vscrollbar_terminal.set_adjustment(self._term.get_adjustment())
        # work around bug in VteTerminal here
        self._term.realize()

        # Use italic style in the status labels
        attrlist=pango.AttrList()
        attr = pango.AttrStyle(pango.STYLE_ITALIC, 0, -1)
        attrlist.insert(attr)
        self.label_status.set_property("attributes", attrlist)

        # reasonable fault handler
        sys.excepthook = self._handleException

    def _handleException(self, type, value, tb):
      import traceback
      lines = traceback.format_exception(type, value, tb)
      logging.error("not handled expection:\n%s" % "\n".join(lines))
      self.error(_("A fatal error occured"),
                 _("During the operation a fatal error occured. "
                   "Please report this as a bug and include the "
                   "files ~/dist-upgrade.log and ~/dist-upgrade-apt.log "
                   "in your report. The upgrade will abort now. "),
                 "\n".join(lines))

    def create_terminal(self, arg1,arg2,arg3,arg4):
        " helper to create a vte terminal "
        self._term = vte.Terminal()
        self._term.set_font_from_string("monospace 10")
        self._term.connect("contents-changed", self._term_content_changed)
        self._terminal_lines = []
        self._terminal_log = open(os.path.expanduser("~/dist-upgrade-term.log"),"w")
        return self._term
    def _term_content_changed(self, term):
        " called when the *visible* part of the terminal changes "

        # get the current visible text, 
        current_text = self._term.get_text(lambda a,b,c,d: True)
        # see what we have currently and only print stuff that wasn't
        # visible last time
        new_lines = []
        for line in current_text.split("\n"):
          new_lines.append(line)
          if not line in self._terminal_lines:
            self._terminal_log.write(line+"\n")
            self._terminal_log.flush()
        self._terminal_lines = new_lines
    def getFetchProgress(self):
        return self._fetchProgress
    def getInstallProgress(self):
        return self._installProgress
    def getOpCacheProgress(self):
        return self._opCacheProgress
    def updateStatus(self, msg):
        self.label_status.set_text("%s" % msg)
    def setStep(self, step):
        # first update the "last" step as completed
        size = gtk.ICON_SIZE_MENU
        attrlist=pango.AttrList()
        if step > 1:
            image = getattr(self,"image_step%i" % (step-1))
            label = getattr(self,"label_step%i" % (step-1))
            image.set_from_stock(gtk.STOCK_APPLY, size)
            label.set_property("attributes",attrlist)
        image = getattr(self,"image_step%i" % step)
        label = getattr(self,"label_step%i" % step)
        image.set_from_stock(gtk.STOCK_YES, size)
        attr = pango.AttrWeight(pango.WEIGHT_BOLD, 0, -1)
        # we can't make it bold here without layout changes in the view :(
        #attr = pango.AttrStyle(pango.STYLE_ITALIC, 0, -1)
        attrlist.insert(attr)
        label.set_property("attributes",attrlist)
                                
    def error(self, summary, msg, extended_msg=None):
        dialog = gtk.MessageDialog(self.window_main, 0, gtk.MESSAGE_ERROR,
                                   gtk.BUTTONS_OK,"")
        msg="<big><b>%s</b></big>\n\n%s" % (summary,msg)
        dialog.set_markup(msg)
        dialog.vbox.set_spacing(6)
        if extended_msg != None:
          scroll = gtk.ScrolledWindow()
          scroll.set_size_request(400,200)
          textview = gtk.TextView()
          textview.set_cursor_visible(False)
          textview.set_editable(False)
          textview.get_buffer().set_text(extended_msg)
          textview.show()
          scroll.add(textview)
          scroll.show()
          dialog.vbox.pack_end(scroll)
        dialog.run()
        dialog.destroy()
        return False

    def confirmChanges(self, summary, changes, downloadSize):
        # FIXME: add a whitelist here for packages that we expect to be
        # removed (how to calc this automatically?)
        DistUpgradeView.confirmChanges(self, summary, changes, downloadSize)
        self.label_summary.set_markup("<big><b>%s</b></big>" % summary)
        msg = _("%s packages are going to be removed.\n"
                "%s packages are going to be newly installed.\n"
                "%s packages are going to be upgraded.\n\n"
                "%s needs to be fetched" % (len(self.toRemove),
                                            len(self.toInstall),
                                            len(self.toUpgrade),
                                            apt_pkg.SizeToStr(downloadSize)))
        self.label_changes.set_text(msg)
        # fill in the details
        self.details_list.clear()
        for rm in self.toRemove:
            self.details_list.append([_("<b>To be removed: %s</b>" % rm)])
        for inst in self.toInstall:
            self.details_list.append([_("To be installed: %s" % inst)])
        for up in self.toUpgrade:
            self.details_list.append([_("To be upgraded: %s" % up)])
        self.dialog_changes.set_transient_for(self.window_main)
        res = self.dialog_changes.run()
        self.dialog_changes.hide()
        if res == gtk.RESPONSE_YES:
            return True
        return False

    def askYesNoQuestion(self, summary, msg):
        msg = "<big><b>%s</b></big>\n\n%s" % (summary,msg)
        dialog = gtk.MessageDialog(parent=self.window_main,
                                   flags=gtk.DIALOG_MODAL,
                                   type=gtk.MESSAGE_QUESTION,
                                   buttons=gtk.BUTTONS_YES_NO)
        dialog.set_markup(msg)
        res = dialog.run()
        dialog.destroy()
        if res == gtk.RESPONSE_YES:
            return True
        return False
    
    def confirmRestart(self):
        self.dialog_restart.set_transient_for(self.window_main)
        res = self.dialog_restart.run()
        self.dialog_restart.hide()
        if res == gtk.RESPONSE_YES:
            return True
        return False

    def on_window_main_delete_event(self, widget, event):
      #print "on_window_main_delete_event()"
      summary = _("Are you sure you want cancel?")
      msg = _("Canceling during a upgrade can leave the system in a "
              "unstable state. It is strongly adviced to continue "
              "the operation. ")
      if self.askYesNoQuestion(summary, msg):
        self.exit(1)
      return True

if __name__ == "__main__":
  view = GtkDistUpgradeView()
  view.error("short","long",
             "asfds afsdj af asdf asdf asf dsa fadsf asdf as fasf sextended\n"
             "asfds afsdj af asdf asdf asf dsa fadsf asdf as fasf sextended\n"
             "asfds afsdj af asdf asdf asf dsa fadsf asdf as fasf sextended\n"
             "asfds afsdj af asdf asdf asf dsa fadsf asdf as fasf sextended\n"
             "asfds afsdj af asdf asdf asf dsa fadsf asdf as fasf sextended\n"
             "asfds afsdj af asdf asdf asf dsa fadsf asdf as fasf sextended\n"
             "asfds afsdj af asdf asdf asf dsa fadsf asdf as fasf sextended\n"
             )
