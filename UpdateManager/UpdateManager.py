# UpdateManager.py 
#  
#  Copyright (c) 2004-2006 Canonical
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
try:
	import gconf
except:
	import fakegconf as gconf
import gobject
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
import pango
import subprocess
import pwd
import time
import thread
import xml.sax.saxutils
from Common.HelpViewer import HelpViewer


from gettext import gettext as _

from Common.utils import *
from Common.SimpleGladeApp import SimpleGladeApp
from DistUpgradeFetcher import DistUpgradeFetcher
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
                self.all_changes[name] = [_("The list of changes is not "
                                            "available yet. Please try again "
                                            "later."), srcpkg]
        except IOError:
            if lock.locked():
                self.all_changes[name] = [_("Failed to download the list"
                                            "of changes. Please "
                                            "check your internet "
                                            "connection."), srcpkg]
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
      msg = ("<big><b>%s</b></big>\n\n%s" % \
            (_("Cannot install all available updates"),
             _("Some updates require the removal of further software. "
               "Use the function \"Mark All Upgrades\" of the package manager "
	       "\"Synaptic\" or run \"sudo apt-get dist-upgrade\" in a "
	       "terminal to update your system completely.")))
      dialog = gtk.MessageDialog(self.parent_window, 0, gtk.MESSAGE_INFO,
                                 gtk.BUTTONS_CLOSE,"")
      dialog.set_default_response(gtk.RESPONSE_OK)
      dialog.set_markup(msg)
      dialog.set_title("")
      dialog.vbox.set_spacing(6)
      label = gtk.Label(_("The following updates will be skipped:"))
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
    icons = gtk.icon_theme_get_default()
    try:
        logo=icons.load_icon("update-manager", 48, 0)
        gtk.window_set_default_icon_list(logo)
    except:
        pass

    self.datadir = datadir
    SimpleGladeApp.__init__(self, datadir+"glade/UpdateManager.glade",
                            None, domain="update-manager")

    self.window_main.set_sensitive(False)
    self.window_main.grab_focus()
    self.button_close.grab_focus()

    self.packages = []
    self.dl_size = 0

    # create text view
    changes_buffer = self.textview_changes.get_buffer()
    changes_buffer.create_tag("versiontag", weight=pango.WEIGHT_BOLD)

    # expander
    self.expander_details.connect("notify::expanded", self.activate_details)

    # useful exit stuff
    self.window_main.connect("delete_event", self.close)
    self.button_close.connect("clicked", lambda w: self.exit())

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
    self.cb.set_visible(True)
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

    # setup the help viewer and disable the help button if there
    # is no viewer available
    self.help_viewer = HelpViewer("update-manager")
    if self.help_viewer.check() == False:
        self.button_help.set_sensitive(False)

    self.gconfclient = gconf.client_get_default()
    # restore state
    self.restore_state()
      

  def on_checkbutton_reminder_toggled(self, checkbutton):
    self.gconfclient.set_bool("/apps/update-manager/remind_reload",
                              not checkbutton.get_active())

  def close(self, widget, data=None):
    if self.window_main.get_property("sensitive") is False:
        return True
    else:
        self.exit()

  
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
    long_desc = model.get_value(iter, LIST_LONG_DESCR)
    if long_desc == None:
      return
    # Skip the first line - it's a duplicate of the summary
    i = long_desc.find("\n")
    long_desc = long_desc[i+1:]
    # do some regular expression magic on the description
    # Add a newline before each bullet
    p = re.compile(r'^(\s|\t)*(\*|0|-)',re.MULTILINE)
    long_desc = p.sub('\n*', long_desc)
    # replace all newlines by spaces
    p = re.compile(r'\n', re.MULTILINE)
    long_desc = p.sub(" ", long_desc)
    # replace all multiple spaces by newlines
    p = re.compile(r'\s\s+', re.MULTILINE)
    long_desc = p.sub("\n", long_desc)

    desc_buffer = self.textview_descr.get_buffer()
    desc_buffer.set_text(utf8(long_desc))

    # now do the changelog
    name = model.get_value(iter, LIST_NAME)
    if name == None:
      return

    changes_buffer = self.textview_changes.get_buffer()
    
    # check if we have the changes already
    if self.cache.all_changes.has_key(name):
      changes = self.cache.all_changes[name]
      self.set_changes_buffer(changes_buffer, changes[0], name, changes[1])
    else:
      if self.expander_details.get_expanded():
        lock = thread.allocate_lock()
        lock.acquire()
        t=thread.start_new_thread(self.cache.get_changelog,(name,lock))
        changes_buffer.set_text(_("Downloading the list of changes..."))
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

  def add_update(self, pkg):
    name = pkg.name
    if name not in self.packages:
      self.packages.append(name)
      self.dl_size += pkg.packageSize
      if len(self.packages) > 0:
        self.button_install.set_sensitive(True)

  def update_count(self):
      """activate or disable widgets and show dialog texts correspoding to
         the number of available updates"""
      if self.list.num_updates == 0:
          text_header= "<big><b>"+_("Your system is up-to-date")+"</b></big>"
          text_download = ""
          self.notebook_details.set_sensitive(False)
          self.treeview_update.set_sensitive(False)
          self.label_downsize.set_text=""
          self.button_close.grab_default()
          self.textview_changes.get_buffer().set_text("")
          self.textview_descr.get_buffer().set_text("")
      else:
          text_header = "<big><b>"+gettext.ngettext("You can install one update", "You can install %s updates" % len(self.store), len(self.store))+"</b></big>"
          
          text_download = _("Download size: %s" % apt_pkg.SizeToStr(self.dl_size))
          self.notebook_details.set_sensitive(True)
          self.treeview_update.set_sensitive(True)
          self.button_install.grab_default()
          self.treeview_update.set_cursor(0)
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
#    cmd = ["gksu","--",
    cmd = ["/usr/sbin/synaptic", "--hide-main-window",  "--non-interactive",
           "--parent-window-id", "%s" % (id) ]
    if action == INSTALL:
      cmd.append("--progress-str")
      cmd.append("%s" % _("Please wait, this can take some time."))
      cmd.append("--finish-str")
      cmd.append("%s" %  _("Update is complete"))
      f = tempfile.NamedTemporaryFile()
      for s in self.packages:
        f.write("%s\tinstall\n" % s)
      cmd.append("--set-selections-file")
      cmd.append("%s" % f.name)
      f.flush()
      subprocess.call(cmd)
      f.close()
    elif action == UPDATE:
      cmd.append("--update-at-startup")
      subprocess.call(cmd)
    else:
      print "run_synaptic() called with unknown action"
      sys.exit(1)
    lock.release()

  def on_button_reload_clicked(self, widget):
    #print "on_button_reload_clicked"
    self.invoke_manager(UPDATE)

  def on_button_help_clicked(self, widget):
    self.help_viewer.run()

  def on_button_install_clicked(self, widget):
    #print "on_button_install_clicked"
    self.invoke_manager(INSTALL)

  def invoke_manager(self, action):
    # check first if no other package manager is runing

    # don't display apt-listchanges, we already showed the changelog
    os.environ["APT_LISTCHANGES_FRONTEND"]="none"

    # set window to insensitive
    self.window_main.set_sensitive(False)
    self.window_main.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
    lock = thread.allocate_lock()
    lock.acquire()
    t = thread.start_new_thread(self.run_synaptic,
                                (self.window_main.window.xid,action,lock))
    while lock.locked():
      while gtk.events_pending():
        gtk.main_iteration()
      time.sleep(0.05)
    while gtk.events_pending():
      gtk.main_iteration()
    self.fillstore()
    self.window_main.set_sensitive(True)
    self.window_main.window.set_cursor(None)

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
    prop = SoftwareProperties.SoftwareProperties(self.datadir, None)
    prop.window_main.set_transient_for(self.window_main)
    prop.run()
    prop.window_main.hide()
    if prop.modified:
        primary = "<span weight=\"bold\" size=\"larger\">%s</span>" % \
                  _("Repositories changed")
        secondary = _("You need to reload the package list from the servers "
                      "for your changes to take effect. Do you want to do "
                      "this now?") 
        dialog = gtk.MessageDialog(self.window_main, 0,
                               gtk.MESSAGE_INFO,gtk.BUTTONS_YES_NO,"")
        dialog.set_markup(primary);
        dialog.format_secondary_text(secondary);
        res = dialog.run()
        dialog.destroy()
        if res == gtk.RESPONSE_YES:
            self.on_button_reload_clicked(None)
    self.window_main.set_sensitive(True)

  def fillstore(self):
    # use the watch cursor
    self.window_main.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))

    # clean most objects
    self.packages = []
    self.dl_size = 0
    self.store.clear()
    self.initCache()
    self.list = UpdateList(self.window_main)

    # fill them again
    self.list.update(self.cache)
    if self.list.num_updates > 0:
      i=0
      for pkg in self.list.pkgs:

        name = xml.sax.saxutils.escape(pkg.name)
        summary = xml.sax.saxutils.escape(pkg.summary)
        contents = "<big><b>%s</b></big>\n<small>%s\n\n" % (name, summary)
        contents = contents + _("New version: %s   (Size: %s)") % (pkg.candidateVersion,apt.SizeToStr(pkg.packageSize)) + "</small>"

        iter = self.store.append([True, contents, pkg.name, pkg.summary,
                                  pkg.candidateVersion, pkg.description, pkg])
        self.add_update(pkg)
        i = i + 1

    self.update_count()
    # use the normal cursor
    self.window_main.window.set_cursor(None)
    return False

  def dist_no_longer_supported(self, meta_release):
    msg = "<big><b>%s</b></big>\n\n%s" % \
          (_("Your distribution is not supported anymore"),
	   _("You will not get any further security fixes or critical "
             "updates. "
             "Upgrade to a later version of Ubuntu Linux. See "
             "http://www.ubuntu.com for more information on "
             "upgrading."))
    dialog = gtk.MessageDialog(self.window_main, 0, gtk.MESSAGE_WARNING,
                               gtk.BUTTONS_CLOSE,"")
    dialog.set_title("")
    dialog.set_markup(msg)
    dialog.run()
    dialog.destroy()
    
  def on_button_dist_upgrade_clicked(self, button):
      #print "on_button_dist_upgrade_clicked"
      fetcher = DistUpgradeFetcher(self, self.new_dist)
      fetcher.run()
      
  def new_dist_available(self, meta_release, upgradable_to):
    #print "new_dist_available: %s" % upgradable_to.name
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
    self.label_new_release.set_markup("<b>New distribution release '%s' is available</b>" % upgradable_to.name)
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
                              buttons=gtk.BUTTONS_CLOSE)
        d.set_markup("<big><b>%s</b></big>\n\n%s" % (
            _("Only one software management tool is allowed to "
              "run at the same time"),
            _("Please close the other application e.g. 'aptitude' "
              "or 'Synaptic' first.")))
        print "error from apt: '%s'" % e
        d.set_title("")
        res = d.run()
        d.destroy()
        sys.exit()

    try:
        progress = GtkProgress.GtkOpProgress(self.dialog_cacheprogress,
                                             self.progressbar_cache,
                                             self.label_cache,
                                             self.window_main)
        self.cache = MyCache(progress)
    except AssertionError:
        # we assert a clean cache
        msg=("<big><b>%s</b></big>\n\n%s"% \
             (_("Software index is broken"),
              _("It is impossible to install or remove any software. "
                "Please use the package manager \"Synaptic\" or run "
		"\"sudo apt-get install -f\" in a terminal to fix "
		"this issue at first.")))
        dialog = gtk.MessageDialog(self.window_main,
                                   0, gtk.MESSAGE_ERROR,
                                   gtk.BUTTONS_CLOSE,"")
        dialog.set_markup(msg)
        dialog.vbox.set_spacing(6)
        dialog.run()
        dialog.destroy()
        sys.exit(1)
    else:
        progress.hide()
    #apt_pkg.Config.Set("Debug::pkgPolicy","1")
    #self.depcache = apt_pkg.GetDepCache(self.cache)
    self.cache._depcache.ReadPinFile()
    if os.path.exists(SYNAPTIC_PINFILE):
        self.cache._depcache.ReadPinFile(SYNAPTIC_PINFILE)
    self.cache._depcache.Init()


  def check_auto_update(self):
      # Check if automatic update is enabled. If not show a dialog to inform
      # the user about the need of manual "reloads"
      remind = self.gconfclient.get_bool("/apps/update-manager/remind_reload")
      if remind == False:
          return

      update_days = apt_pkg.Config.FindI("APT::Periodic::Update-Package-Lists")
      if update_days < 1:
          self.dialog_manual_update.set_transient_for(self.window_main)
          res = self.dialog_manual_update.run()
          self.dialog_manual_update.hide()
          if res == gtk.RESPONSE_YES:
              self.on_button_reload_clicked(None)


  def main(self, options):
    gconfclient = gconf.client_get_default() 
    self.meta = MetaRelease(options.devel_release)
    self.meta.connect("dist_no_longer_supported",self.dist_no_longer_supported)

    # check if we are interessted in dist-upgrade information
    # (we are not by default on dapper)
    if options.check_dist_upgrades or \
	   gconfclient.get_bool("/apps/update-manager/check_dist_upgrades"):
      self.meta.connect("new_dist_available",self.new_dist_available)
    
    while gtk.events_pending():
      gtk.main_iteration()

    self.fillstore()
    self.check_auto_update()
    gtk.main()
