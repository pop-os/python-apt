# UpdateManager.py 
#  
#  Copyright (c) 2004,2005 Canonical
#                2004 Michiel Sikkes
#                2005 Martin Willemoes Hansen
#  
#  Author: Michiel Sikkes <michiel@eyesopened.nl>
#          Michael Vogt <mvo@debian.org>
#          Martin Willemoes Hansen <mwh@sysrq.dk>
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
import gobject
import gnome
import apt
import apt_pkg
import gettext
import copy
import string
import sys
import os
import os.path
import urllib2
import re
import tempfile
import gconf
import pango
import subprocess
import pwd
import time
import thread
import xml.sax.saxutils

# dist-upgrade tool
import tarfile

from gettext import gettext as _

from Common.utils import *
from Common.SimpleGladeApp import SimpleGladeApp
import GtkProgress

from MetaRelease import Dist, MetaRelease

# FIXME:
# - kill "all_changes" and move the changes into the "Update" class

# list constants
(LIST_INSTALL, LIST_CONTENTS, LIST_NAME, LIST_SHORTDESC,
 LIST_VERSION, LIST_LONG_DESCR, LIST_PKG) = range(7)

# actions for "invoke_manager"
(INSTALL, UPDATE) = range(2)

SYNAPTIC_PINFILE = "/var/lib/synaptic/preferences"

CHANGELOGS_URI="http://changelogs.ubuntu.com/changelogs/pool/%s/%s/%s/%s_%s/changelog"


class MyCache(apt.Cache):
    def __init__(self, progress):
        apt.Cache.__init__(self, progress)
        assert self._depcache.BrokenCount == 0 and self._depcache.DelCount == 0
        self.all_changes = {}
    def clean(self):
        for pkg in self:
            pkg.markKeep()
    def saveDistUpgrade(self):
        """ this functions mimics a upgrade but will never remove anything """
        self._depcache.Upgrade(True)
        if self._depcache.DelCount > 0:
            self.clean()
        assert self._depcache.BrokenCount == 0 and self._depcache.DelCount == 0
        self._depcache.Upgrade()
        
    def get_changelog(self, name, lock):
        # don't touch the gui in this function, it needs to be thread-safe
        pkg = self[name]

        verstr = pkg.candidateVersion
        srcpkg = pkg.sourcePackageName

        # assume "main" section 
        src_section = "main"
        # check if we have something else
        l = string.split(pkg.section,"/")
        if len(l) > 1:
            sec_section = l[0]

        # lib is handled special
        prefix = srcpkg[0]
        if srcpkg.startswith("lib"):
            prefix = "lib" + srcpkg[3]

        # stip epoch
        l = string.split(verstr,":")
        if len(l) > 1:
            verstr = l[1]

        try:
            uri = CHANGELOGS_URI % (src_section,prefix,srcpkg,srcpkg, verstr)
            #print "Trying: %s " % uri
            changelog = urllib2.urlopen(uri)
            #print changelog.read()
            # do only get the lines that are new
            alllines = ""
            regexp = "^%s \((.*)\)(.*)$" % (srcpkg)

            i=0
            while True:
                line = changelog.readline()
                #print line
                if line == "":
                    break
                match = re.match(regexp,line)
                if match:
                    if apt_pkg.VersionCompare(match.group(1),pkg.installedVersion) <= 0:
                        break
                    # EOF (shouldn't really happen)
                alllines = alllines + line

            # only write if we where not canceld
            if lock.locked():
                self.all_changes[name] = [alllines, srcpkg]
        except urllib2.HTTPError:
            if lock.locked():
                self.all_changes[name] = [_("Changes not found, the server may not be updated yet."), srcpkg]
        except IOError:
            if lock.locked():
                self.all_changes[name] = [_("Failed to download changes. Please check if there is an active internet connection."), srcpkg]
        if lock.locked():
            lock.release()

        


class UpdateList:
  def __init__(self, parent_window):
    self.pkgs = []
    self.num_updates = 0
    self.parent_window = parent_window

  def update(self, cache):
    held_back = []
    broken = []
    cache.saveDistUpgrade()
    for pkg in cache:
      if pkg.markedUpgrade or pkg.markedInstall:
        self.pkgs.append(pkg)
        self.num_updates = self.num_updates + 1
      elif pkg.isUpgradable:
        #print "MarkedKeep: %s " % pkg.name
          held_back.append(pkg.name)
    self.pkgs.sort(lambda x,y: cmp(x.name,y.name))
    if cache._depcache.KeepCount > 0:
      #print "WARNING, keeping packages"
      msg=("<big><b>%s</b></big>\n\n%s"%(_("It is not possible to upgrade "
                                           "all packages."),
                                         _("This means that "
                                           "besides the actual upgrade of the "
                                           "packages some further action "
                                           "(such as installing or removing "
                                           "packages) "
                                           "is required. Please use Synaptic "
                                           "\"Smart Upgrade\" or "
                                           "\"apt-get dist-upgrade\" to fix "
                                           "the situation."
                                           )))
      dialog = gtk.MessageDialog(self.parent_window, 0, gtk.MESSAGE_INFO,
                                 gtk.BUTTONS_OK,"")
      dialog.set_default_response(gtk.RESPONSE_OK)
      dialog.set_markup(msg)
      dialog.vbox.set_spacing(6)
      label = gtk.Label(_("The following packages are not upgraded: "))
      label.set_alignment(0.0,0.5)
      dialog.set_border_width(6)
      label.show()
      dialog.vbox.pack_start(label)
      scroll = gtk.ScrolledWindow()
      scroll.set_size_request(-1,200)
      scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
      text = gtk.TextView()
      text.set_editable(False)
      text.set_cursor_visible(False)
      buf = text.get_buffer()
      held_back.sort()
      buf.set_text("\n".join(held_back))
      scroll.add(text)
      dialog.vbox.pack_start(scroll)
      scroll.show_all()
      dialog.run()
      dialog.destroy()

        
class UpdateManager(SimpleGladeApp):

  def __init__(self, datadir):

    self.datadir = datadir
    SimpleGladeApp.__init__(self, datadir+"glade/UpdateManager.glade",
                            None, domain="update-manager")
    self.gnome_program = gnome.init("update-manager", "0.41")

    self.packages = []
    self.dl_size = 0

    # create text view
    changes_buffer = self.textview_changes.get_buffer()
    changes_buffer.create_tag("versiontag", weight=pango.WEIGHT_BOLD)

    # expander
    self.expander_details.connect("notify::expanded", self.activate_details)

    # useful exit stuff
    self.window_main.connect("delete_event", lambda w, ev: self.exit())
    self.button_cancel.connect("clicked", lambda w: self.exit())

    # the treeview (move into it's own code!)
    self.store = gtk.ListStore(gobject.TYPE_BOOLEAN, str, str, str, str, str,
                               gobject.TYPE_PYOBJECT)
    self.treeview_update.set_model(self.store)
    self.treeview_update.set_headers_clickable(True);

    tr = gtk.CellRendererText()
    tr.set_property("xpad", 10)
    tr.set_property("ypad", 10)
    cr = gtk.CellRendererToggle()
    cr.set_property("activatable", True)
    cr.set_property("xpad", 10)
    cr.connect("toggled", self.toggled)
    self.cb = gtk.TreeViewColumn("Install", cr, active=LIST_INSTALL)
    c0 = gtk.TreeViewColumn("Name", tr, markup=LIST_CONTENTS)
    c0.set_resizable(True)
    major,minor,patch = gtk.pygtk_version
    if (major >= 2) and (minor >= 5):
      self.cb.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
      self.cb.set_fixed_width(30)
      c0.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
      c0.set_fixed_width(100)
      #self.treeview_update.set_fixed_height_mode(True)

    self.treeview_update.append_column(self.cb)
    self.cb.set_visible(False)
    self.treeview_update.append_column(c0)
    self.treeview_update.set_search_column(LIST_NAME)	


    # proxy stuff
    # FIXME: move this into it's own function
    SYNAPTIC_CONF_FILE = "%s/.synaptic/synaptic.conf" % pwd.getpwuid(0)[5]
    if os.path.exists(SYNAPTIC_CONF_FILE):
      cnf = apt_pkg.newConfiguration()
      apt_pkg.ReadConfigFile(cnf, SYNAPTIC_CONF_FILE)
      use_proxy = cnf.FindB("Synaptic::useProxy", False)
      if use_proxy:
        proxy_host = cnf.Find("Synaptic::httpProxy")
        proxy_port = str(cnf.FindI("Synaptic::httpProxyPort"))
        if proxy_host and proxy_port:
          proxy_support = urllib2.ProxyHandler({"http":"http://%s:%s" % (proxy_host, proxy_port)})
          opener = urllib2.build_opener(proxy_support)
          urllib2.install_opener(opener)

    self.gconfclient = gconf.client_get_default()
    # restore state
    self.restore_state()


  def set_changes_buffer(self, changes_buffer, text, name, srcpkg):
    changes_buffer.set_text("")
    lines = text.split("\n")
    if len(lines) == 1:
      changes_buffer.set_text(text)
      return
    
    for line in lines:
    
      end_iter = changes_buffer.get_end_iter()
      
      version_match = re.match("^%s \((.*)\)(.*)$" % (srcpkg), line)
      #bullet_match = re.match("^.*[\*-]", line)
      author_match = re.match("^.*--.*<.*@.*>.*$", line)
      if version_match:
        version = version_match.group(1)
        version_text = _("Version %s: \n") % version
        changes_buffer.insert_with_tags_by_name(end_iter, version_text, "versiontag")
      # mvo: disabled for now as it does not catch multi line entries
      #      (see ubuntu #7034 for rational)
      #elif bullet_match and not author_match:
      #  bullet_text = "    " + line + "\n"
      #  changes_buffer.insert(end_iter, bullet_text)
      elif (author_match):
        pass
        #chanages_buffer.insert(end_iter, "\n")
      else:
        changes_buffer.insert(end_iter, line+"\n")
        

  def on_treeview_update_cursor_changed(self, widget):
    tuple = widget.get_cursor()
    path = tuple[0]
    # check if we have a path at all
    if path == None:
      return
    model = widget.get_model()
    iter = model.get_iter(path)

    # set descr
    long_desc = model.get_value(iter, 5)
    if long_desc == None:
      return
    desc_buffer = self.textview_descr.get_buffer()
    desc_buffer.set_text(utf8(long_desc))

    # now do the changelog
    name = model.get_value(iter, 2)
    if name == None:
      return

    changes_buffer = self.textview_changes.get_buffer()
    
    # check if we have the changes already
    if self.cache.all_changes.has_key(name):
      changes = self.cache.all_changes[name]
      self.set_changes_buffer(changes_buffer, changes[0], name, changes[1])
    else:
      if self.expander_details.get_expanded():
        self.treeview_update.set_sensitive(False)
        self.hbox_footer.set_sensitive(False)
        lock = thread.allocate_lock()
        lock.acquire()
        t=thread.start_new_thread(self.cache.get_changelog,(name,lock))
        changes_buffer.set_text(_("Downloading changes..."))
        button = self.button_cancel_dl_changelog
        button.show()
        id = button.connect("clicked",
                            lambda w,lock: lock.release(), lock)
        # wait for the dl-thread
        while lock.locked():
          time.sleep(0.05)
          while gtk.events_pending():
            gtk.main_iteration()
        # download finished (or canceld, or time-out)
        button.hide()
        button.disconnect(id);
        self.treeview_update.set_sensitive(True)
        self.hbox_footer.set_sensitive(True)

    if self.cache.all_changes.has_key(name):
      changes = self.cache.all_changes[name]
      self.set_changes_buffer(changes_buffer, changes[0], name, changes[1])

  def remove_update(self, pkg):
    name = pkg.name
    if name in self.packages:
      self.packages.remove(name)
      self.dl_size -= pkg.packageSize
      if len(self.packages) == 0:
        self.button_install.set_sensitive(False)
    self.update_count()

  def add_update(self, pkg):
    name = pkg.name
    if name not in self.packages:
      self.packages.append(name)
      self.dl_size += pkg.packageSize
      if len(self.packages) > 0:
        self.button_install.set_sensitive(True)
    self.update_count()

  def update_count(self):
      if len(self.packages) == 0:
          text_header= _("<big><b>No updates available</b></big>")
          text_download = ""
      else:
          text_header = gettext.ngettext("<big><b>You can install one update</b></big>", "<big><b>You can install %s updates</b></big>" % len(self.packages), len(self.packages))
          
          text_download = _("Download size: %s" % apt_pkg.SizeToStr(self.dl_size))
      self.label_header.set_markup(text_header)
      self.label_downsize.set_markup(text_download)

  def activate_details(self, expander, data):
    expanded = self.expander_details.get_expanded()
    if expanded:
        expander.set_label(_("Hide details"))
    else:
        expander.set_label(_("Show details"))
    self.gconfclient.set_bool("/apps/update-manager/show_details",expanded)
    if expanded:
      self.on_treeview_update_cursor_changed(self.treeview_update)

  def run_synaptic(self, id, action, lock):
    try:
        apt_pkg.PkgSystemUnLock()
    except SystemError:
        pass
    cmd = ["/usr/sbin/synaptic", "--hide-main-window",  "--non-interactive",
           "--plug-progress-into", "%s" % (id) ]
    if action == INSTALL:
      cmd.append("--set-selections")
      cmd.append("--progress-str")
      cmd.append("%s" % _("The updates are being applied."))
      cmd.append("--finish-str")
      cmd.append("%s" %  _("Upgrade is complete"))
      proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
      f = proc.stdin
      for s in self.packages:
        f.write("%s\tinstall\n" % s)
      f.close()
      proc.wait()
    elif action == UPDATE:
      cmd.append("--update-at-startup")
      subprocess.call(cmd)
    else:
      print "run_synaptic() called with unknown action"
      sys.exit(1)

    # use this once gksudo does propper reporting
    #if os.geteuid() != 0:
    #  if os.system("gksudo  /bin/true") != 0:
    #    return
    #  cmd = "sudo " + cmd;
    lock.release()

  def plug_removed(self, w, (win,socket)):
    #print "plug_removed"
    # plug was removed, but we don't want to get it removed, only hiden
    # unti we get more 
    win.hide()
    return True

  def plug_added(self, sock, win):
    while gtk.events_pending():
      gtk.main_iteration()
    # hack around the problem that too early showing has unpleasnt effect
    # (like double arrow, incorrect window size etc)
    gobject.timeout_add(500, lambda win: win.show(), win)

  def on_button_reload_clicked(self, widget):
    #print "on_button_reload_clicked"
    #self.invoke_manager(UPDATE)
    progress = GtkProgress.GtkFetchProgress(self,
                                            _("Downloading package "
                                              "information"),
                                            _("The repositories will be "
                                              "checked for new, removed "
                                              "or upgraded software "
                                              "packages."))
    # FIXME: do a try/except here otherwise it may bomb
    try:
        self.cache.update(progress)
    except (IOError,SystemError), msg:
        dialog = gtk.MessageDialog(self.window_main, 0, gtk.MESSAGE_ERROR,
                                   gtk.BUTTONS_OK,"")
        dialog.set_markup("<span weight=\"bold\" size=\"larger\">%s</span>"%\
                          _("Error reloading"))
        dialog.format_secondary_text(_("A error occured during the package "
                                       "list reload. Please see the below "
                                       "information for details what went "
                                       "wrong."))
        dialog.set_border_width(6)
        dialog.set_size_request(width=500,height=-1)
        scroll = gtk.ScrolledWindow()
        scroll.set_size_request(-1,200)
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        text = gtk.TextView()
        text.set_editable(False)
        text.set_cursor_visible(False)
        text.set_wrap_mode(gtk.WRAP_WORD)
        buf = text.get_buffer()
        buf.set_text("%s" % msg)
        scroll.add(text)
        dialog.vbox.pack_start(scroll)
        scroll.show_all()
        dialog.run()
        dialog.destroy()
    # unlock the cache here, it will be locked again in fillstore
    try:
        apt_pkg.PkgSystemUnLock()
    except SystemError:
        pass
    self.fillstore()

  def on_button_help_clicked(self, widget):
    gnome.help_display_desktop(self.gnome_program, "update-manager", "update-manager", "")

  def on_button_install_clicked(self, widget):
    #print "on_button_install_clicked"
    self.invoke_manager(INSTALL)

  def invoke_manager(self, action):
    # check first if no other package manager is runing
    import struct, fcntl
    lock = os.path.dirname(apt_pkg.Config.Find("Dir::State::status"))+"/lock"
    lock_file= open(lock)
    flk=struct.pack('hhllhl',fcntl.F_WRLCK,0,0,0,0,0)
    try:
      rv = fcntl.fcntl(lock_file, fcntl.F_GETLK, flk)
    except IOError:
      print "Error getting lockstatus"
      raise
    locked = struct.unpack('hhllhl', rv)[0]
    if locked != fcntl.F_UNLCK:
      msg=("<big><b>%s</b></big>\n\n%s"%(_("Another package manager is "
                                           "running"),
                                         _("You can run only one "
                                           "package management application "
                                           "at the same time. Please close "
                                           "this other application first.")));
      dialog = gtk.MessageDialog(self.window_main, 0, gtk.MESSAGE_ERROR,
                                 gtk.BUTTONS_OK,"")
      dialog.set_markup(msg)
      dialog.run()
      dialog.destroy()
      return

    # don't display apt-listchanges, we already showed the changelog
    os.environ["APT_LISTCHANGES_FRONTEND"]="none"

    # set window to insensitive
    self.window_main.set_sensitive(False)
    # create a progress window that will swallow the synaptic progress bars
    win = gtk.Window()
    if action==UPDATE:
      win.set_title(_("Updating package list..."))
    else:
      win.set_title(_("Installing updates..."))
    win.set_border_width(6)
    win.set_transient_for(self.window_main)
    win.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
    win.resize(400,200)
    win.set_resizable(False)
    # prevent the window from closing with the delete button (there is
    # a cancel button in the window)
    win.connect("delete_event", lambda e,w: True);
    
    # create the socket
    socket = gtk.Socket()
    socket.show()
    win.add(socket)

    socket.connect("plug-added", self.plug_added, win)
    socket.connect("plug-removed", self.plug_removed, (win,socket))
    lock = thread.allocate_lock()
    lock.acquire()
    t = thread.start_new_thread(self.run_synaptic,(socket.get_id(),action,lock))
    while lock.locked():
      while gtk.events_pending():
        gtk.main_iteration()
      time.sleep(0.05)
    win.destroy()
    while gtk.events_pending():
      gtk.main_iteration()
    self.fillstore()
    self.window_main.set_sensitive(True)    

  def toggled(self, renderer, path_string):
    """ a toggle button in the listview was toggled """
    iter = self.store.get_iter_from_string(path_string)
    if self.store.get_value(iter, LIST_INSTALL):
      self.store.set_value(iter, LIST_INSTALL, False)
      self.remove_update(self.store.get_value(iter, LIST_PKG))
    else:
      self.store.set_value(iter, LIST_INSTALL, True)
      self.add_update(self.store.get_value(iter, LIST_PKG))


  def exit(self):
    """ exit the application, save the state """
    self.save_state()
    gtk.main_quit()
    sys.exit(0)

  def save_state(self):
    """ save the state  (window-size for now) """
    (x,y) = self.window_main.get_size()
    self.gconfclient.set_pair("/apps/update-manager/window_size",
                              gconf.VALUE_INT, gconf.VALUE_INT, x, y)

  def restore_state(self):
    """ restore the state (window-size for now) """
    expanded = self.gconfclient.get_bool("/apps/update-manager/show_details")
    self.expander_details.set_expanded(expanded)
    (x,y) = self.gconfclient.get_pair("/apps/update-manager/window_size",
                                      gconf.VALUE_INT, gconf.VALUE_INT)
    if x > 0 and y > 0:
      self.window_main.resize(x,y)

  def on_button_preferences_clicked(self, widget):
    """ start gnome-software preferences """
    # args: "-n" means we take care of the reloading of the
    # package list ourself
    #apt_pkg.PkgSystemUnLock()
    #args = ['/usr/bin/gnome-software-properties', '-n']
    #child = subprocess.Popen(args)
    #self.window_main.set_sensitive(False)
    #res = None
    #while res == None:
    #  res = child.poll()
    #  time.sleep(0.05)
    ##  while gtk.events_pending():
    #    gtk.main_iteration()
    # repository information changed, call "reload"
    #try:
    #    apt_pkg.PkgSystemLock()
    #except SystemError:
    #	print "Error geting the cache"
    #    apt_pkg.PkgSystemLock()
    #    if res > 0:
    #      self.on_button_reload_clicked(None)
    #    self.window_main.set_sensitive(True)
    self.window_main.set_sensitive(False)
    from SoftwareProperties import SoftwareProperties
    prop = SoftwareProperties(self.datadir, None)
    prop.window_main.set_transient_for(self.window_main)
    prop.run()
    prop.window_main.hide()
    if prop.modified:
        primary = "<span weight=\"bold\" size=\"larger\">%s</span>" % \
                  _("Repositories changed")
        secondary = _("You need to reload the package list from the servers "
                      "for your changes to take effect. Do you want to do "
                      "this now?") 
        dialog = gtk.MessageDialog(self.window_main,gtk.DIALOG_MODAL,
                               gtk.MESSAGE_INFO,gtk.BUTTONS_YES_NO,"")
        dialog.set_markup(primary);
        dialog.format_secondary_text(secondary);
        res = dialog.run()
        dialog.destroy()
        if res == gtk.RESPONSE_YES:
            self.on_button_reload_clicked(None)
    self.window_main.set_sensitive(True)

  def fillstore(self):

    # clean most objects
    self.packages = []
    self.dl_size = 0
    self.store.clear()
    self.initCache()
    self.list = UpdateList(self.window_main)

    # fill them again
    self.list.update(self.cache)
    if self.list.num_updates < 1:
      # set the label and treeview and hide the checkbox column
      self.cb.set_visible(False)
      self.expander_details.hide()
      text = "<big><b>%s</b></big>\n\n%s" % (_("Your system is up-to-date"),
                                             _("There are no updates available."))
      self.label_header.set_markup(text)
      self.store.append([False, _("Your system is up-to-date!"), None, None, None, None, None])
      # make sure no install is possible
      self.button_install.set_sensitive(False)
    else:
      self.cb.set_visible(True)
      self.expander_details.show()
      self.treeview_update.set_headers_visible(False)
      text = _("<big><b>Available Updates</b></big>\n"
               "\n"
               "The following packages are found to be upgradable. You can upgrade them by "
               "using the Install button.")
      self.label_header.set_markup(text)
      i=0
      for pkg in self.list.pkgs:

        name = xml.sax.saxutils.escape(pkg.name)
        summary = xml.sax.saxutils.escape(pkg.summary)
        contents = "<big><b>%s</b></big>\n<small>%s\n\n" % (name, summary)
	contents = contents + _("New version: %s   (Size: %s)") % (pkg.candidateVersion,apt.SizeToStr(pkg.packageSize)) + "</small>"

        iter = self.store.append([True, contents, pkg.name, pkg.summary, pkg.candidateVersion, pkg.description, pkg])
	self.add_update(pkg)
        i = i + 1


    self.update_count()
    return False

  def dist_no_longer_supported(self, meta_release):
    msg = "<big><b>%s</b></big>\n\n%s" % (_("Your distribution is no longer supported"), _("Please upgrade to a newer version of Ubuntu Linux. The version you are running will no longer get security fixes or other critical updates. Please see http://www.ubuntulinux.org for upgrade information."))
    dialog = gtk.MessageDialog(self.window_main, 0, gtk.MESSAGE_WARNING,
                               gtk.BUTTONS_OK,"")
    dialog.set_markup(msg)
    dialog.run()
    dialog.destroy()
    
  def on_button_dist_upgrade_clicked(self, button):
      print "on_button_dist_upgrade_clicked"

      # see if we have release notes

      # FIXME: care about i18n! (append -$lang or something)
      if self.new_dist.releaseNotesURI != None:
          uri = self.new_dist.releaseNotesURI
          print uri
          self.window_main.set_sensitive(False)
          self.window_main.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
          while gtk.events_pending():
              gtk.main_iteration()

          # download/display the release notes
          # FIXME: add some progress reporting here 
          try:
              release_notes = urllib2.urlopen(uri)
              notes = release_notes.read()
              self.textview_release_notes.get_buffer().set_text(notes)
              self.dialog_release_notes.set_transient_for(self.window_main)
              self.dialog_release_notes.run()
              self.dialog_release_notes.hide()
          except urllib2.HTTPError:
              # FIXME: make proper error dialogs here
              print _("Release notes not found on the server.")
          except IOError:
              print _("Failed to download Release Notes. Please "
                      "check if there is an active internet connection.")
          self.window_main.set_sensitive(True)
          self.window_main.window.set_cursor(None)

      # now download the tarball with the upgrade script
      tmpdir = tempfile.mkdtemp()
      os.chdir(tmpdir)
      if self.new_dist.upgradeTool != None:
          progress = GtkProgress.GtkFetchProgress(self,
                                                  _("Downloading upgrade "
                                                    "informtion"),
                                                  _("The upgrade information "
                                                    "are downloaded"))
          fetcher = apt_pkg.GetAcquire(progress)
          uri = self.new_dist.upgradeTool
          #print "Downloading %s to %s" % (uri, tmpdir)
          af = apt_pkg.GetPkgAcqFile(fetcher,uri,
                                     descr=_("Upgrade tool"))
          fetcher.Run()
          #print "Done downloading"

          # extract the tarbal
          print "extracting"
          tar = tarfile.open(tmpdir+"/"+os.path.basename(uri),"r")
          for tarinfo in tar:
              tar.extract(tarinfo)
          tar.close()

          # FIXME: check a internal dependency file to make sure
          #        that the script will run correctly
          
          # see if we have a script file that we can run
          script = "%s/%s" % (tmpdir, self.new_dist.name)
          if not os.path.exists(script):
	      # FIXME: display a proper error message here
              print "no script file found in extracted tarbal"
          else:
              #print "runing: %s" % script
              os.execv(script,[])
          
      # cleanup
      os.chdir("..")
      # del tmpdir
      for root, dirs, files in os.walk(tmpdir, topdown=False):
          for name in files:
              os.remove(os.path.join(root, name))
              #print "would remove file: %s" % os.path.join(root, name)
          for name in dirs:
              os.rmdir(os.path.join(root, name))
              #print "would remove dir: %s" % os.path.join(root, name)
      os.rmdir(tmpdir)
      
  def new_dist_available(self, meta_release, upgradable_to):
    print "new_dist_available: %s" % upgradable_to.name
    # check if the user already knowns about this dist
    #seen = self.gconfclient.get_string("/apps/update-manager/seen_dist")
    #if name == seen:
    #  return
    
    #msg = "<big><b>%s</b></big>\n\n%s" % (_("There is a new release of Ubuntu available!"), _("A new release with the codename '%s' is available. Please see http://www.ubuntulinux.org/ for upgrade instructions.") % name)
    #dialog = gtk.MessageDialog(self.window_main, 0, gtk.MESSAGE_INFO,
    #                           gtk.BUTTONS_CLOSE, "")
    #dialog.set_markup(msg)
    #check = gtk.CheckButton(_("Never show this message again"))
    #check.show()
    #dialog.vbox.pack_start(check)
    #dialog.run()
    #if check.get_active():
    #  self.gconfclient.set_string("/apps/update-manager/seen_dist",name)
    #dialog.destroy()
    self.frame_new_release.show()
    self.label_new_release.set_markup("<b>New distibution release codename '%s' available</b>" % upgradable_to.name)
    self.new_dist = upgradable_to
    

  # fixme: we should probably abstract away all the stuff from libapt
  def initCache(self): 
    # get the lock
    try:
        apt_pkg.PkgSystemLock()
    except SystemError, e:
        d = gtk.MessageDialog(parent=self.window_main,
                              flags=gtk.DIALOG_MODAL,
                              type=gtk.MESSAGE_ERROR,
                              buttons=gtk.BUTTONS_OK)
        d.set_markup("<big><b>%s</b></big>\n\n%s" % (
            _("Unable to get exclusive lock"),
            _("This usually means that another package management "
              "application (like apt-get or aptitude) already running. "
              "Please close that application first")))
        print "error from apt: '%s'" % e
        res = d.run()
        d.destroy()
        sys.exit()

    try:
        self.cache = MyCache(GtkProgress.GtkOpProgress(self.dialog_cacheprogress,
                                                       self.progressbar_cache,
                                                       self.window_main))
    except AssertionError:
        # we assert a clean cache
        msg=("<big><b>%s</b></big>\n\n%s"% \
             (_("Your system has broken packages!"),
              _("This means that some dependencies "
                "of the installed packages are not "
                "satisfied. Please use \"Synaptic\" "
                "or \"apt-get\" to fix the "
                "situation."
                )))
        dialog = gtk.MessageDialog(self.window_main,
                                   0, gtk.MESSAGE_ERROR,
                                   gtk.BUTTONS_OK,"")
        dialog.set_markup(msg)
        dialog.vbox.set_spacing(6)
        dialog.run()
        sys.exit(1)
    #apt_pkg.Config.Set("Debug::pkgPolicy","1")
    #self.depcache = apt_pkg.GetDepCache(self.cache)
    self.cache._depcache.ReadPinFile()
    if os.path.exists(SYNAPTIC_PINFILE):
        self.cache._depcache.ReadPinFile(SYNAPTIC_PINFILE)
    self.cache._depcache.Init()

  def main(self):
    self.meta = MetaRelease()
    self.meta.connect("new_dist_available",self.new_dist_available)
    self.meta.connect("dist_no_longer_supported",self.dist_no_longer_supported)
    
    self.store.append([True, _("Initializing and getting list of updates..."),
                       None, None, None, None, None])

    while gtk.events_pending():
      gtk.main_iteration()

    self.fillstore()
    gtk.main()
