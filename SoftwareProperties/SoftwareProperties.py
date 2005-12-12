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
import gnome
import gconf
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
import aptsources
import dialog_add
import dialog_edit
from dialog_apt_key import apt_key
from utils import *

(LIST_MARKUP, LIST_ENABLED, LIST_ENTRY_OBJ) = range(3)

CONF_MAP = {
  "autoupdate"   : "APT::Periodic::Update-Package-Lists",
  "autodownload" : "APT::Periodic::Download-Upgradeable-Packages",
  "autoclean"    : "APT::Periodic::AutocleanInterval",
  "max_size"     : "APT::Archives::MaxSize",
  "max_age"      : "APT::Archives::MaxAge"
}


class SoftwareProperties(SimpleGladeApp):

  def __init__(self, datadir, options):

    self.datadir = datadir
    SimpleGladeApp.__init__(self, datadir+"glade/SoftwareProperties.glade",
                            None, domain="update-manager")
    self.modified = False
		  
    self.gnome_program = gnome.init("Software Properties", "0.41")
    self.gconfclient = gconf.client_get_default()

    # If externally called, reparent to external application.
    if options and options.toplevel != None:
      toplevel = gtk.gdk.window_foreign_new(int(options.toplevel))
      self.window_main.window.set_transient_for(toplevel)
      
    self.init_sourceslist()
    self.reload_sourceslist()
      
    update_days = apt_pkg.Config.FindI(CONF_MAP["autoupdate"])
    
    self.spinbutton_update_interval.set_value(update_days)
    
    if update_days >= 1:
      self.checkbutton_auto_update.set_active(True)
    else:
      self.checkbutton_auto_update.set_active(False)
      
    self.apt_key = apt_key()
    
    self.init_keyslist()
    self.reload_keyslist()
    
  def init_sourceslist(self):
    self.source_store = gtk.ListStore(str, bool, gobject.TYPE_PYOBJECT)
    self.treeview_sources.set_model(self.source_store)
    
    tr = gtk.CellRendererText()
    tr.set_property("xpad", 10)
    tr.set_property("ypad", 10)
    
    source_col = gtk.TreeViewColumn("Description", tr, markup=LIST_MARKUP)
    source_col.set_max_width(500)

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
    self.source_store.clear()
    for source in self.sourceslist.list:
      if source.invalid or source.disabled:
        continue
      (a_type, dist, comps) = self.matcher.match(source)
      
      contents = ""
      if source.comment != "":
        contents += "<i>%s</i>\n\n" % (source.comment)
      contents +="<big><b>%s </b></big> (%s) <small>\n%s</small>" % (dist,a_type, comps)

      self.source_store.append([contents, not source.disabled, source])
      
  def reload_keyslist(self):
    self.keys_store.clear()
    for key in self.apt_key.list():
      self.keys_store.append([key])
  
  def opt_autoupdate_toggled(self, widget):  
    if self.checkbutton_auto_update.get_active():
      if self.spinbutton_update_interval.get_value() == 0:
        self.spinbutton_update_interval.set_value(1)
        value = "1"
      else:
        value = str(self.spinbutton_update_interval.get_value()) 
    else:
      value = "0"
    
    apt_pkg.Config.Set(CONF_MAP["autoupdate"], str(value))
    
    # FIXME: Write config options, apt_pkg should be able to do this.
    self.write_config()
    
  def write_config(self):
    periodic = "/etc/apt/apt.conf.d/10periodic"
    
    content = []
    
    if os.path.isfile(periodic):
      content = open(periodic, "r").readlines()
      
    cnf = apt_pkg.Config.SubTree("APT::Periodic")
    
    f = open(periodic, "w+")
    for line in content:
      found = False
      for key in cnf.List():
        if line.find("APT::Periodic::%s" % (key)) >= 0:
          found = True
          break
        if not found:
          f.write(line)
          
    for i in cnf.List():
      f.write("APT::Periodic::%s \"%s\";\n" % (i, cnf.FindI(i)))
    f.close()    
    
  def save_sourceslist(self):
    #location = "/etc/apt/sources.list"
    #shutil.copy(location, location + ".save")
    self.sourceslist.backup(".save")
    self.sourceslist.save()
    
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
    dialog = dialog_edit.dialog_edit(self.window_main, self.sourceslist,
                                     source_entry, self.datadir)
    if dialog.run() == gtk.RESPONSE_OK:
      self.reload_sourceslist()
      self.modified = True
      
  def on_remove_clicked(self, widget):
    sel = self.treeview_sources.get_selection()
    (model, iter) = sel.get_selected()
    if iter:
      source = model.get_value(iter, LIST_ENTRY_OBJ)
      self.sourceslist.remove(source)
      self.reload_sourceslist()  
      self.modified = True
    
  def add_key_clicked(self, widget):
    chooser = gtk.FileChooserDialog(title=_("Choose a key-file"),
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
    gnome.help_display_desktop(self.gnome_program, 
                               "update-manager", "update-manager", 
                               "setting-preferences")

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
  
