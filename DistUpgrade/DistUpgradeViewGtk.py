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
import time
import subprocess

import apt
import apt_pkg
import os

from apt.progress import InstallProgress
from DistUpgradeView import DistUpgradeView
from UpdateManager.Common.SimpleGladeApp import SimpleGladeApp, bindtextdomain

import gettext
from gettext import gettext as _

def utf8(str):
  return unicode(str, 'latin1').encode('utf-8')

def FuzzyTimeToStr(sec):
  " return the time a bit fuzzy (no seconds if time > 60 secs "
  if sec > 60*60*24:
    return _("About %li days %li hours %li minutes remaining") % (sec/60/60/24,
                                                                  (sec/60/60) % 24,
                                                                  (sec/60) % 60)
  if sec > 60*60:
    return _("About %li hours %li minutes remaining") % (sec/60/60,
                                          (sec/60) % 60)
  if sec > 60:
    return _("About %li minutes remaining") % (sec/60)
  return _("About %li seconds remaining") % sec


class GtkOpProgress(apt.progress.OpProgress):
  def __init__(self, progressbar):
      self.progressbar = progressbar
      #self.progressbar.set_pulse_step(0.01)
      #self.progressbar.pulse()

  def update(self, percent):
      #if percent > 99:
      #    self.progressbar.set_fraction(1)
      #else:
      #    self.progressbar.pulse()
      self.progressbar.set_fraction(percent/100.0)
      while gtk.events_pending():
          gtk.main_iteration()

  def done(self):
      self.progressbar.set_text(" ")


class GtkFetchProgressAdapter(apt.progress.FetchProgress):
    # FIXME: we really should have some sort of "we are at step"
    # xy in the gui
    # FIXME2: we need to thing about mediaCheck here too
    def __init__(self, parent):
        # if this is set to false the download will cancel
        self.status = parent.label_status
        self.progress = parent.progressbar_cache
        self.parent = parent
    def mediaChange(self, medium, drive):
      #print "mediaChange %s %s" % (medium, drive)
      msg = _("Please insert '%s' into the drive '%s'" % (medium,drive))
      dialog = gtk.MessageDialog(parent=self.parent.window_main,
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
        self.progress.set_text(" ")
        self.status.set_text(_("Download is complete"))
    def pulse(self):
        # FIXME: move the status_str and progress_str into python-apt
        # (python-apt need i18n first for this)
        apt.progress.FetchProgress.pulse(self)
        self.progress.set_fraction(self.percent/100.0)
        currentItem = self.currentItems + 1
        if currentItem > self.totalItems:
            currentItem = self.totalItems

        if self.currentCPS > 0:
            self.status.set_text(_("Downloading file %li of %li at %s/s" % (currentItem, self.totalItems, apt_pkg.SizeToStr(self.currentCPS))))
            self.progress.set_text(FuzzyTimeToStr(self.eta))
        else:
            self.status.set_text(_("Downloading file %li of %li" % (currentItem, self.totalItems)))
            self.progress.set_text("  ")

        while gtk.events_pending():
            gtk.main_iteration()
        return True

class GtkInstallProgressAdapter(InstallProgress):
    # timeout with no status change when the terminal is expanded
    # automatically
    TIMEOUT_TERMINAL_ACTIVITY = 240
    
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
        # some options for dpkg to make it die less easily
        apt_pkg.Config.Set("DPkg::Options::","--force-overwrite")

    def startUpdate(self):
        self.finished = False
        # FIXME: add support for the timeout
        # of the terminal (to display something useful then)
        # -> longer term, move this code into python-apt 
        self.label_status.set_text(_("Applying changes"))
        self.progress.set_fraction(0.0)
        self.progress.set_text(" ")
        self.expander.set_sensitive(True)
        self.term.show()
        self.env = ["VTE_PTY_KEEP_FD=%s"% self.writefd,
                    "DEBIAN_FRONTEND=gnome",
                    "APT_LISTCHANGES_FRONTEND=none"]
        # do a bit of time-keeping
        self.start_time = 0.0
        self.time_ui = 0.0
        self.last_activity = 0.0
        
    def error(self, pkg, errormsg):
        logging.error("got an error from dpkg for pkg: '%s': '%s'" % (pkg, errormsg))
        #self.expander_terminal.set_expanded(True)
        self.parent.dialog_error.set_transient_for(self.parent.window_main)
        summary = _("Could not install '%s'" % pkg)
        msg = _("The upgrade aborts now. Please report this bug.")
        markup="<big><b>%s</b></big>\n\n%s" % (summary, msg)
        self.parent.dialog_error.realize()
        self.parent.dialog_error.window.set_functions(gtk.gdk.FUNC_MOVE)
        self.parent.label_error.set_markup(markup)
        self.parent.textview_error.get_buffer().set_text(utf8(errormsg))
        self.parent.scroll_error.show()
        self.parent.dialog_error.run()
        self.parent.dialog_error.hide()

    def conffile(self, current, new):
        logging.debug("got a conffile-prompt from dpkg for file: '%s'" % current)
        #self.expander.set_expanded(True)
        prim = _("Replace configuration file\n'%s'?" % current)
        sec = ("The configuration file %s was modified (by "
               "you or by a script). An updated version is shipped "
               "in this package. If you want to keep your current "
               "version say 'Keep'. Do you want to replace the "
               "current file and install the new package "
               "maintainers version? " % current)
        markup = "<span weight=\"bold\" size=\"larger\">%s </span> \n\n%s" % (prim, sec)
        self.parent.label_conffile.set_markup(markup)
        self.parent.dialog_conffile.set_transient_for(self.parent.window_main)

        # now get the diff
        if os.path.exists("/usr/bin/diff"):
          cmd = ["/usr/bin/diff", "-u", current, new]
          diff = utf8(subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0])
          self.parent.textview_conffile.get_buffer().set_text(diff)
        else:
          self.parent.textview_conffile.get_buffer().set_text(_("The 'diff' command was not found"))
        res = self.parent.dialog_conffile.run()
        self.parent.dialog_conffile.hide()
        # if replace, send this to the terminal
        if res == gtk.RESPONSE_YES:
          self.term.feed_child("y\n")
        else:
          self.term.feed_child("n\n")
        
    def fork(self):
        pid = self.term.forkpty(envv=self.env)
        if pid == 0:
          # HACK to work around bug in python/vte and unregister the logging
          #      atexit func in the child
          sys.exitfunc = lambda: True
        return pid

    def statusChange(self, pkg, percent, status):
        # start the timer when the first package changes its status
        if self.start_time == 0.0:
          #print "setting start time to %s" % self.start_time
          self.start_time = time.time()
        self.progress.set_fraction(float(self.percent)/100.0)
        self.label_status.set_text(status.strip())
        # start showing when we gathered some data
        if percent > 1.0:
          self.last_activity = time.time()
          self.activity_timeout_reported = False
          delta = self.last_activity - self.start_time
          time_per_percent = (float(delta)/percent)
          eta = (100.0 - self.percent) * time_per_percent
          # only show if we have some sensible data
          if eta > 61.0 and eta < (60*60*24*2):
            self.progress.set_text(FuzzyTimeToStr(eta))
          else:
            self.progress.set_text(" ")

    def child_exited(self, term, pid, status):
        self.apt_status = os.WEXITSTATUS(status)
        self.finished = True

    def waitChild(self):
        while not self.finished:
            self.updateInterface()
        return self.apt_status

    def finishUpdate(self):
        self.label_status.set_text("")
    
    def updateInterface(self):
        InstallProgress.updateInterface(self)
        # check if we haven't started yet with packages, pulse then
        if self.start_time == 0.0:
          self.progress.pulse()
          time.sleep(0.2)
        # check about terminal activity
        if self.last_activity > 0 and \
           (self.last_activity + self.TIMEOUT_TERMINAL_ACTIVITY) < time.time():
          if not self.activity_timeout_reported:
            logging.warning("no activity on terminal for %s seconds (%s)" % (self.TIMEOUT_TERMINAL_ACTIVITY, self.label_status.get_text()))
            self.activity_timeout_reported = True
          self.parent.expander_terminal.set_expanded(True)
        while gtk.events_pending():
            gtk.main_iteration()
	time.sleep(0.02)

class DistUpgradeVteTerminal(object):
  def __init__(self, parent, term):
    self.term = term
    self.parent = parent
  def call(self, cmd):
    def wait_for_child(widget):
      #print "wait for child finished"
      self.finished=True
    self.term.show()
    self.term.connect("child-exited", wait_for_child)
    self.parent.expander_terminal.set_expanded(True)
    self.term.fork_command(command=cmd[0],argv=cmd)
    self.finished = False
    while not self.finished:
      while gtk.events_pending():
        gtk.main_iteration()
      time.sleep(0.1)
    del self.finished

class DistUpgradeViewGtk(DistUpgradeView,SimpleGladeApp):
    " gtk frontend of the distUpgrade tool "
    def __init__(self):
        # FIXME: i18n must be somewhere relative do this dir
        bindtextdomain("update-manager",os.path.join(os.getcwd(),"mo"))

        icons = gtk.icon_theme_get_default()
        gtk.window_set_default_icon(icons.load_icon("update-manager", 32, 0))
        SimpleGladeApp.__init__(self, "DistUpgrade.glade",
                                None, domain="update-manager")
        # we dont use this currently
        #self.window_main.set_keep_above(True)
        self.window_main.realize()
        self.window_main.window.set_functions(gtk.gdk.FUNC_MOVE)
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
                 _("Please report this as a bug and include the "
                   "files /var/log/dist-upgrade.log and "
                   "/var/log/dist-upgrade-apt.log "
                   "in your report. The upgrade aborts now.\n"
                   "Your original sources.list was saved in "
                   "/etc/apt/sources.list.distUpgrade."),
                 "\n".join(lines))
      sys.exit(1)

    def getTerminal(self):
        return DistUpgradeVteTerminal(self, self._term)

    def create_terminal(self, arg1,arg2,arg3,arg4):
        " helper to create a vte terminal "
        self._term = vte.Terminal()
        self._term.set_font_from_string("monospace 10")
        self._term.connect("contents-changed", self._term_content_changed)
        self._terminal_lines = []
        try:
          self._terminal_log = open("/var/log/dist-upgrade-term.log","w")
        except IOError:
          # if something goes wrong (permission denied etc), use stdout
          self._terminal_log = sys.stdout
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

    def information(self, summary, msg, extended_msg=None):
      self.dialog_information.set_transient_for(self.window_main)
      msg = "<big><b>%s</b></big>\n\n%s" % (summary,msg)
      self.label_information.set_markup(msg)
      if extended_msg != None:
        buffer = self.textview_information.get_buffer()
        buffer.set_text(extended_msg)
        self.scroll_information.show()
      else:
        self.scroll_information.hide()
      self.dialog_information.realize()
      self.dialog_information.window.set_functions(gtk.gdk.FUNC_MOVE)
      self.dialog_information.run()
      self.dialog_information.hide()

    def error(self, summary, msg, extended_msg=None):
        self.dialog_error.set_transient_for(self.window_main)
        #self.expander_terminal.set_expanded(True)
        msg="<big><b>%s</b></big>\n\n%s" % (summary, msg)
        self.label_error.set_markup(msg)
        if extended_msg != None:
            buffer = self.textview_error.get_buffer()
            buffer.set_text(extended_msg)
            self.scroll_error.show()
        else:
            self.scroll_error.hide()
        self.dialog_error.realize()
        self.dialog_error.window.set_functions(gtk.gdk.FUNC_MOVE)
        self.dialog_error.run()
        self.dialog_error.hide()
        return False

    def confirmChanges(self, summary, changes, downloadSize, actions=None):
        # FIXME: add a whitelist here for packages that we expect to be
        # removed (how to calc this automatically?)
        DistUpgradeView.confirmChanges(self, summary, changes, downloadSize)
        pkgs_remove = len(self.toRemove)
        pkgs_inst = len(self.toInstall)
        pkgs_upgrade = len(self.toUpgrade)
        msg = ""

        if pkgs_remove > 0:
            msg += gettext.ngettext("%s package is going to be removed." %\
                                    pkgs_remove,
                                    "%s packages are going to be removed." %\
                                    pkgs_remove, pkgs_remove)
            msg += " "
        if pkgs_inst > 0:
            msg += gettext.ngettext("%s new package is going to be "\
                                    "installed." % pkgs_inst,
                                    "%s new packages are going to be "\
                                    "installed." % pkgs_inst, pkgs_inst)
            msg += " "
        if pkgs_upgrade > 0:
            msg += gettext.ngettext("%s package is going to be upgraded." %\
                                    pkgs_upgrade,
                                    "%s packages are going to be upgraded." %\
                                    pkgs_upgrade, pkgs_upgrade)
            msg +=" "

        if downloadSize > 0:
            msg += _("You have to download a total of %s." %\
                     apt_pkg.SizeToStr(downloadSize))

        if (pkgs_upgrade + pkgs_inst + pkgs_remove) > 100:
            msg += "\n\n%s" % _("The upgrade can take several hours and "\
                                "cannot be canceled at any time later.")

        msg += "\n\n<b>%s</b>" % _("To prevent data loss close all open "\
                                   "applications and documents.")

        # Show an error if no actions are planned
        if (pkgs_upgrade + pkgs_inst + pkgs_remove) < 1:
            # FIXME: this should go into DistUpgradeController
            summary = _("Could not find any upgrades")
            msg = _("Your system has already been upgraded.")
            self.error(summary, msg)
            return False

        if actions != None:
            self.button_cancel_changes.set_use_stock(False)
            self.button_cancel_changes.set_use_underline(True)
            self.button_cancel_changes.set_label(actions[0])
            self.button_confirm_changes.set_label(actions[1])

        self.label_summary.set_markup("<big><b>%s</b></big>" % summary)
        self.label_changes.set_markup(msg)
        # fill in the details
        self.details_list.clear()
        for rm in self.toRemove:
            self.details_list.append([_("<b>Remove %s</b>" % rm)])
        for inst in self.toInstall:
            self.details_list.append([_("Install %s" % inst)])
        for up in self.toUpgrade:
            self.details_list.append([_("Upgrade %s" % up)])
        self.treeview_details.scroll_to_cell((0,))
        self.dialog_changes.set_transient_for(self.window_main)
        self.dialog_changes.realize()
        self.dialog_changes.window.set_functions(gtk.gdk.FUNC_MOVE)
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
        self.dialog_restart.realize()
        self.dialog_restart.window.set_functions(gtk.gdk.FUNC_MOVE)
        res = self.dialog_restart.run()
        self.dialog_restart.hide()
        if res == gtk.RESPONSE_YES:
            return True
        return False

    def on_window_main_delete_event(self, widget, event):
        self.dialog_cancel.set_transient_for(self.window_main)
        self.dialog_cancel.realize()
        self.dialog_cancel.window.set_functions(gtk.gdk.FUNC_MOVE)
        res = self.dialog_cancel.run()
        self.dialog_cancel.hide()
        if res == gtk.RESPONSE_CANCEL:
            #FIXME: this does not work correctly and leaves a stalled
            #       dist-upgrade.py process
            self.destroy()
        return True

if __name__ == "__main__":
  
  view = DistUpgradeViewGtk()
  fp = GtkFetchProgressAdapter(view)
  ip = GtkInstallProgressAdapter(view)


  cache = apt.Cache()
  for pkg in sys.argv[1:]:
    cache[pkg].markInstall()
  cache.commit(fp,ip)
  
  #sys.exit(0)
  ip.conffile("TODO","TODO~")
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
  
