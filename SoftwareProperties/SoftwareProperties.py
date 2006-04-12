# gnome-software-properties.in - edit /etc/apt/sources.list
#
#  Copyright (c) 2004,2005 Canonical
#                2004-2005 Michiel Sikkes
#
#  Author: Michiel Sikkes <michiel@eyesopened.nl>
#          Michael Vogt <mvo@debian.org>
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
import apt
import apt_pkg
import gobject
import shutil
import gettext
import tempfile
from gettext import gettext as _
import os

#sys.path.append("@prefix/share/update-manager/python")

from UpdateManager.Common.SimpleGladeApp import SimpleGladeApp
from UpdateManager.Common.HelpViewer import HelpViewer
import aptsources
import dialog_add
import dialog_edit
import dialog_cache_outdated
from dialog_apt_key import apt_key
from utils import *

(LIST_MARKUP, LIST_ENABLED, LIST_ENTRY_OBJ) = range(3)

CONF_MAP = {
  "autoupdate"   : "APT::Periodic::Update-Package-Lists",
  "autodownload" : "APT::Periodic::Download-Upgradeable-Packages",
  "autoclean"    : "APT::Periodic::AutocleanInterval",
  "unattended"   : "APT::Periodic::Unattended-Upgrade",
  "max_size"     : "APT::Archives::MaxSize",
  "max_age"      : "APT::Archives::MaxAge"
}


class SoftwareProperties(SimpleGladeApp):

  def __init__(self, datadir=None, options=None, parent=None):

    # FIXME: some saner way is needed here
    if datadir == None:
      datadir = "/usr/share/update-manager/"
    self.datadir = datadir
    SimpleGladeApp.__init__(self, datadir+"glade/SoftwareProperties.glade",
                            None, domain="update-manager")
    self.modified = False

    #self.gnome_program = gnome.init("Software Properties", "0.41")
    #self.gconfclient = gconf.client_get_default()

    if parent:
      self.window_main.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
      self.window_main.show()
      self.window_main.set_transient_for(parent)

    # If externally called, reparent to external application.
    self.options = options
    if options and options.toplevel != None:
      self.window_main.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
      self.window_main.show()
      toplevel = gtk.gdk.window_foreign_new(int(options.toplevel))
      self.window_main.window.set_transient_for(toplevel)
    
    self.window_main.show()
      
    self.init_sourceslist()
    self.reload_sourceslist()

    # internet update setings
    
    # this maps the key (combo-box-index) to the auto-update-interval value
    # where (-1) means, no key
    self.combobox_interval_mapping = { 0 : 1,
                                       1 : 2,
                                       2 : 7,
                                       3 : 14 }
    self.combobox_update_interval.set_active(0)

    update_days = apt_pkg.Config.FindI(CONF_MAP["autoupdate"])

    self.combobox_update_interval.append_text("Daily")
    self.combobox_update_interval.append_text("Every two days")
    self.combobox_update_interval.append_text("Weekly")
    self.combobox_update_interval.append_text("Every two weeks")

    # If a custom period is defined add an corresponding entry
    if not update_days in self.combobox_interval_mapping.values():
        if update_days > 0:
            self.combobox_update_interval.append_text(_("Every %s days" 
                                                      % update_days))
            self.combobox_interval_mapping[4] = update_days
    
    for key in self.combobox_interval_mapping:
      if self.combobox_interval_mapping[key] == update_days:
        self.combobox_update_interval.set_active(key)
        break

    if update_days >= 1:
      self.checkbutton_auto_update.set_active(True)
      self.combobox_update_interval.set_sensitive(True)
    else:
      self.checkbutton_auto_update.set_active(False)
      self.combobox_update_interval.set_sensitive(False)

    # Automatic removal of cached packages by age
    self.combobox_delete_interval_mapping = { 0 : 7,
                                              1 : 14,
                                              2 : 30 }

    delete_days = apt_pkg.Config.FindI(CONF_MAP["max_age"])

    self.combobox_delete_interval.append_text("After one week")
    self.combobox_delete_interval.append_text("After two weeks")
    self.combobox_delete_interval.append_text("After one month")

    # If a custom period is defined add an corresponding entry
    if not delete_days in self.combobox_delete_interval_mapping.values():
        if delete_days > 0 and CONF_MAP["autoclean"] != 0:
            self.combobox_delete_interval.append_text(_("After %s days" 
                                                      % delete_days))
            self.combobox_delete_interval_mapping[3] = delete_days
    
    for key in self.combobox_delete_interval_mapping:
      if self.combobox_delete_interval_mapping[key] == delete_days:
        self.combobox_delete_interval.set_active(key)
        break

    if delete_days >= 1 and apt_pkg.Config.FindI(CONF_MAP["autoclean"]) != 0:
      self.checkbutton_auto_delete.set_active(True)
      self.combobox_delete_interval.set_sensitive(True)
    else:
      self.checkbutton_auto_delete.set_active(False)
      self.combobox_delete_interval.set_sensitive(False)

    # Autodownload
    if apt_pkg.Config.FindI(CONF_MAP["autodownload"]) == 1:
      self.checkbutton_auto_download.set_active(True)
    else:
      self.checkbutton_auto_download.set_active(False)

    # Unattended updates
    if os.path.exists("/usr/bin/unattended-upgrade"):
        # FIXME: we should always show the option. if unattended-upgrades is
        # not installed a dialog should popup and allow the user to install
        # unattended-upgrade
        #self.checkbutton_unattended.set_sensitive(True)
        self.checkbutton_unattended.show()
    else:
        #self.checkbutton_unattended.set_sensitive(False)
        self.checkbutton_unattended.hide()
    if apt_pkg.Config.FindI(CONF_MAP["unattended"]) == 1:
        self.checkbutton_unattended.set_active(True)
    else:
        self.checkbutton_unattended.set_active(False)

    self.help_viewer = HelpViewer("update-manager#setting-preferences")
    if self.help_viewer.check() == False:
        self.button_help.set_sensitive(False)

    # apt-key stuff
    self.apt_key = apt_key()
    self.init_keyslist()
    self.reload_keyslist()

  def hide(self):
    self.window_main.hide()
    
  def init_sourceslist(self):
    self.source_store = gtk.ListStore(str, bool, gobject.TYPE_PYOBJECT)
    self.treeview_sources.set_model(self.source_store)
    
    tr = gtk.CellRendererText()
    tr.set_property("xpad", 10)
    tr.set_property("ypad", 10)
    
    source_col = gtk.TreeViewColumn("Description", tr, markup=LIST_MARKUP)
    #source_col.set_max_width(500)

    toggle = gtk.CellRendererToggle()
    toggle.connect("toggled", self.on_channel_toggled)
    toggle_col = gtk.TreeViewColumn("Active", toggle, active=LIST_ENABLED)

    self.treeview_sources.append_column(toggle_col)
    self.treeview_sources.append_column(source_col)
    
    self.sourceslist = aptsources.SourcesList()
    self.matcher = aptsources.SourceEntryMatcher()
    
  def init_keyslist(self):
    self.keys_store = gtk.ListStore(str)
    self.treeview2.set_model(self.keys_store)
    
    tr = gtk.CellRendererText()
    
    keys_col = gtk.TreeViewColumn("Key", tr, text=0)
    self.treeview2.append_column(keys_col)
    
  def reload_sourceslist(self):
    (path_x, path_y) = self.treeview_sources.get_cursor()
    self.source_store.clear()
    for source in self.sourceslist.list:
      if source.invalid:
        continue
      (a_type, dist, comps) = self.matcher.match(source)
      
      contents = ""
      if source.comment != "":
        contents += "<i>%s</i>\n\n" % (source.comment)
      contents +="<big><b>%s </b></big> (%s) <small>\n%s</small>" % (dist,a_type, comps)

      self.source_store.append([contents, not source.disabled, source])
    # try to reselect the latest selected channel or if it fails the first
    # one
    if len(self.source_store) > 0 and \
       (path_x == None or self.treeview_sources.set_cursor(path_x)):
            self.treeview_sources.set_cursor(0)
    else:
        # call the cursor_changed signal if no channel is selected
        self.treeview_sources.emit("cursor_changed")

  def reload_keyslist(self):
    self.keys_store.clear()
    for key in self.apt_key.list():
      self.keys_store.append([key])

  def on_combobox_update_interval_changed(self, widget):
    i = self.combobox_update_interval.get_active()
    if i != -1:
        value = self.combobox_interval_mapping[i]
        # Only write the key if it has changed
        if not value == apt_pkg.Config.FindI(CONF_MAP["autoupdate"]):
            apt_pkg.Config.Set(CONF_MAP["autoupdate"], str(value))
            self.write_config()

  def on_opt_autoupdate_toggled(self, widget):
    if self.checkbutton_auto_update.get_active():
      self.combobox_update_interval.set_sensitive(True)
      # if no frequency was specified use daily
      i = self.combobox_update_interval.get_active()
      if i == -1:
          i = 0
          self.combobox_update_interval.set_active(i)
      value = self.combobox_interval_mapping[i]
    else:
      self.combobox_update_interval.set_sensitive(False)
      value = 0
    apt_pkg.Config.Set(CONF_MAP["autoupdate"], str(value))
    # FIXME: Write config options, apt_pkg should be able to do this.
    self.write_config()

  def on_opt_unattended_toggled(self, widget):  
    if self.checkbutton_unattended.get_active():
        self.checkbutton_unattended.set_active(True)
        apt_pkg.Config.Set(CONF_MAP["unattended"], str(1))
    else:
        self.checkbutton_unattended.set_active(False)
        apt_pkg.Config.Set(CONF_MAP["unattended"], str(0))
    # FIXME: Write config options, apt_pkg should be able to do this.
    self.write_config()

  def on_opt_autodownload_toggled(self, widget):  
    if self.checkbutton_auto_download.get_active():
        self.checkbutton_auto_download.set_active(True)
        apt_pkg.Config.Set(CONF_MAP["autodownload"], str(1))
    else:
        self.checkbutton_auto_download.set_active(False)
        apt_pkg.Config.Set(CONF_MAP["autodownload"], str(0))
    # FIXME: Write config options, apt_pkg should be able to do this.
    self.write_config()

  def on_combobox_delete_interval_changed(self, widget):
    i = self.combobox_delete_interval.get_active()
    if i != -1:
        value = self.combobox_delete_interval_mapping[i]
        # Only write the key if it has changed
        if not value == apt_pkg.Config.FindI(CONF_MAP["max_age"]):
            apt_pkg.Config.Set(CONF_MAP["max_age"], str(value))
            self.write_config()
      
  def on_opt_autodelete_toggled(self, widget):  
    if self.checkbutton_auto_delete.get_active():
      self.combobox_delete_interval.set_sensitive(True)
      # if no frequency was specified use the first default value
      i = self.combobox_delete_interval.get_active()
      if i == -1:
          i = 0
          self.combobox_delete_interval.set_active(i)
      value_maxage = self.combobox_delete_interval_mapping[i]
      value_clean = 1
      apt_pkg.Config.Set(CONF_MAP["max_age"], str(value_maxage))
    else:
      self.combobox_delete_interval.set_sensitive(False)
      value_clean = 0
    apt_pkg.Config.Set(CONF_MAP["autoclean"], str(value_clean))
    # FIXME: Write config options, apt_pkg should be able to do this.
    self.write_config()
    
  def write_config(self):
    # update the adept file as well if it is there
    for periodic in ["/etc/apt/apt.conf.d/10periodic",
                     "/etc/apt/apt.conf.d/15adept-periodic-update"]:

      # read the old content first
      content = []
      if os.path.isfile(periodic):
        content = open(periodic, "r").readlines()
        cnf = apt_pkg.Config.SubTree("APT::Periodic")

        # then write a new file without the updated keys
        f = open(periodic, "w")
        for line in content:
          for key in cnf.List():
            if line.find("APT::Periodic::%s" % (key)) >= 0:
              break
          else:
            f.write(line)

        # and append the updated keys
        for i in cnf.List():
          f.write("APT::Periodic::%s \"%s\";\n" % (i, cnf.FindI(i)))
        f.close()    

  def save_sourceslist(self):
    #location = "/etc/apt/sources.list"
    #shutil.copy(location, location + ".save")
    self.sourceslist.backup(".save")
    self.sourceslist.save()
    # show a dialog that a reload of the channel information is required
    # only if there is no parent defined
    if self.modified == True and \
       self.options.toplevel == None:
        d = dialog_cache_outdated.DialogCacheOutdated(self.window_main,
                                                      self.datadir)
        res = d.run()

  def on_add_clicked(self, widget):
    dialog = dialog_add.dialog_add(self.window_main, self.sourceslist,
                                   self.datadir)
    if dialog.run() == gtk.RESPONSE_OK:
      self.reload_sourceslist()
      self.modified = True
      
  def on_edit_clicked(self, widget):
    sel = self.treeview_sources.get_selection()
    (model, iter) = sel.get_selected()
    if not iter:
      return
    source_entry = model.get_value(iter, LIST_ENTRY_OBJ)
    # see if we know what this thing should look like
    found_matcher = False
    for item in aptsources.SourceEntryTemplates(self.datadir).templates:
      if item.matches(source_entry):
        found_matcher = True
        break
    if found_matcher:
      dialog = dialog_add.dialog_add(self.window_main, self.sourceslist,
                                     self.datadir, source_entry)
    else:
      dialog = dialog_edit.dialog_edit(self.window_main, self.sourceslist,
                                       source_entry, self.datadir)
    if dialog.run() == gtk.RESPONSE_OK:
      self.reload_sourceslist()
      self.modified = True

  def on_channel_activated(self, treeview, path, column):
     """Open the edit dialog if a channel was double clicked"""
     # check if the channel can be edited
     if self.button_edit.get_property("sensitive") == True:
         self.on_edit_clicked(treeview)

  def on_treeview_sources_cursor_changed(self, treeview):
    """set the sensitiveness of the edit and remove button
       corresponding to the selected channel"""
    sel = self.treeview_sources.get_selection()
    (model, iter) = sel.get_selected()
    if not iter:
        # No channel is selected, so disable edit and remove
        self.button_edit.set_sensitive(False)
        self.button_remove.set_sensitive(False)
        return
    # allow to remove the selected channel
    self.button_remove.set_sensitive(True)
    # disable editing of cdrom sources
    source_entry = model.get_value(iter, LIST_ENTRY_OBJ)
    if source_entry.uri.startswith("cdrom:"):
        self.button_edit.set_sensitive(False)
    else:
        self.button_edit.set_sensitive(True)

  def on_remove_clicked(self, widget):
    sel = self.treeview_sources.get_selection()
    (model, iter) = sel.get_selected()
    if iter:
      source = model.get_value(iter, LIST_ENTRY_OBJ)
      self.sourceslist.remove(source)
      self.reload_sourceslist()  
      self.modified = True
    
  def add_key_clicked(self, widget):
    chooser = gtk.FileChooserDialog(title=_("Import key"),
                                    parent=self.window_main,
                                    buttons=(gtk.STOCK_CANCEL,
                                             gtk.RESPONSE_REJECT,
                                             gtk.STOCK_OK,gtk.RESPONSE_ACCEPT))
    res = chooser.run()
    chooser.hide()
    if res == gtk.RESPONSE_ACCEPT:
      if not self.apt_key.add(chooser.get_filename()):
        error(self.window_main,
              _("Error importing selected file"),
              _("The selected file may not be a GPG key file " \
                "or it might be corrupt."))
        self.reload_keyslist()
        
  def remove_key_clicked(self, widget):
    selection = self.treeview2.get_selection()
    (model,a_iter) = selection.get_selected()
    if a_iter == None:
        return
    key = model.get_value(a_iter,0)
    if not self.apt_key.rm(key[:8]):
      error(self.main,
        _("Error removing the key"),
        _("The key you selected could not be removed. "
          "Please report this as a bug."))
    self.reload_keyslist()
    
  def on_restore_clicked(self, widget):
    self.apt_key.update()
    self.reload_keyslist()
    
  def on_delete_event(self, widget, args):
    self.save_sourceslist()
    self.quit()
    
  def on_close_button(self, widget):
    self.save_sourceslist()
    self.quit()
    
  def on_help_button(self, widget):
    self.help_viewer.run()

  def on_button_add_cdrom_clicked(self, widget):
    #print "on_button_add_cdrom_clicked()"

    # testing
    #apt_pkg.Config.Set("APT::CDROM::Rename","true")

    saved_entry = apt_pkg.Config.Find("Dir::Etc::sourcelist")
    tmp = tempfile.NamedTemporaryFile()
    apt_pkg.Config.Set("Dir::Etc::sourcelist",tmp.name)
    progress = GtkCdromProgress(self.datadir,self.window_main)
    cdrom = apt_pkg.GetCdrom()
    # if nothing was found just return
    try:
      res = cdrom.Add(progress)
    except SystemError, msg:
      #print "aiiiieeee, exception from cdrom.Add() [%s]" % msg
      progress.close()
      dialog = gtk.MessageDialog(parent=self.window_main,
                                 flags=gtk.DIALOG_MODAL,
                                 type=gtk.MESSAGE_ERROR,
                                 buttons=gtk.BUTTONS_OK,
                                 message_format=None)
      dialog.set_markup(_("<big><b>Error scaning the CD</b></big>\n\n%s"%msg))
      res = dialog.run()
      dialog.destroy()
      return
    apt_pkg.Config.Set("Dir::Etc::sourcelist",saved_entry)
    if res == False:
      progress.close()
      return
    # read tmp file with source name (read only last line)
    line = ""
    for x in open(tmp.name):
      line = x
    if line != "":
      full_path = "%s%s" % (apt_pkg.Config.FindDir("Dir::Etc"),saved_entry)
      self.sourceslist.list.append(aptsources.SourceEntry(line,full_path))
      self.reload_sourceslist()
      self.modified = True

  def on_channel_toggled(self, cell_toggle, path):
      """Enable or disable the selected channel"""
      iter = self.source_store.get_iter((int(path),))
      source_entry = self.source_store.get_value(iter, LIST_ENTRY_OBJ)
      source_entry.disabled = not source_entry.disabled
      self.reload_sourceslist()
      self.modified = True

# FIXME: move this into a different file
class GtkCdromProgress(apt.progress.CdromProgress, SimpleGladeApp):
  def __init__(self,datadir, parent):
    SimpleGladeApp.__init__(self,
                            datadir+"glade/SoftwarePropertiesDialogs.glade",
                            "dialog_cdrom_progress",
                            domain="update-manager")
    self.dialog_cdrom_progress.show()
    self.dialog_cdrom_progress.set_transient_for(parent)
    self.parent = parent
    self.button_cdrom_close.set_sensitive(False)
  def close(self):
    self.dialog_cdrom_progress.hide()
  def on_button_cdrom_close_clicked(self, widget):
    self.close()
  def update(self, text, step):
    """ update is called regularly so that the gui can be redrawn """
    if step > 0:
      self.progressbar_cdrom.set_fraction(step/float(self.totalSteps))
      if step == self.totalSteps:
        self.button_cdrom_close.set_sensitive(True)
    if text != "":
      self.label_cdrom.set_text(text)
    while gtk.events_pending():
      gtk.main_iteration()
  def askCdromName(self):
    dialog = gtk.MessageDialog(parent=self.dialog_cdrom_progress,
                               flags=gtk.DIALOG_MODAL,
                               type=gtk.MESSAGE_QUESTION,
                               buttons=gtk.BUTTONS_OK_CANCEL,
                               message_format=None)
    dialog.set_markup(_("Please enter a name for the disc"))
    entry = gtk.Entry()
    entry.show()
    dialog.vbox.pack_start(entry)
    res = dialog.run()
    dialog.destroy()
    if res == gtk.RESPONSE_OK:
      name = entry.get_text()
      return (True,name)
    return (False,"")
  def changeCdrom(self):
    dialog = gtk.MessageDialog(parent=self.dialog_cdrom_progress,
                               flags=gtk.DIALOG_MODAL,
                               type=gtk.MESSAGE_QUESTION,
                               buttons=gtk.BUTTONS_OK_CANCEL,
                               message_format=None)
    dialog.set_markup(_("Please insert a disc in the drive:"))
    res = dialog.run()
    dialog.destroy()
    if res == gtk.RESPONSE_OK:
      return True
    return False
  
