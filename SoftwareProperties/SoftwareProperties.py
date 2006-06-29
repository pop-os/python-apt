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
import string
import re

#sys.path.append("@prefix/share/update-manager/python")

from UpdateManager.Common.SimpleGladeApp import SimpleGladeApp
from UpdateManager.Common.HelpViewer import HelpViewer
import aptsources
import dialog_add
import dialog_edit
import dialog_cache_outdated
#import dialog_edit_predefined
#import dialog_sources_list
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

(
    COLUMN_ACTIVE,
    COLUMN_DESC
) = range(2)


# columns of the source_store
(
    STORE_ACTIVE, 
    STORE_DESCRIPTION, 
    STORE_SOURCE, 
    STORE_SEPARATOR,
    STORE_VISIBLE
) = range(5)

class Distribution:
  def __init__(self):
    """"
    Container for distribution specific informations
    """
    # LSB information
    self.id = ""
    self.codename = ""
    self.description = ""
    self.release = ""

    # corresponding sources
    self.source_template = None
    self.child_sources = []
    self.main_sources = []
    self.enabled_comps = []
    self.used_media = []
    self.source_code_sources = []

    # location of the sources
    self.cdrom_available = False
    self.use_internet = False
    self.main_server = ""
    self.nearest_server = ""
    self.other_servers = []
    
    # get the LSB information
    lsb_info = []
    for lsb_option in ["-i", "-c", "-d", "-r"]:
        pipe = os.popen("lsb_release %s | cut -d : -f 2-" % lsb_option)
        lsb_info.append(pipe.read().strip())
        del pipe
    (self.id, self.codename, self.description, self.release) = lsb_info

  def get_sources(self, sources_list):
    """
    Find the corresponding template, main and child sources 
    for the distribution 
    """
    # find the distro template
    for template in sources_list.matcher.templates:
        if template.name == self.codename and\
           template.distribution == self.id:
            print "yeah! found a template for %s" % self.description
            print template.description, template.base_uri, template.components
            self.source_template = template
            break
    if self.source_template == None:
        print "Error: could not find a distribution template"
        # FIXME: will go away - only for debugging issues
        sys.exit(1)

    # find main and child sources
    media = []
    comps = []
    source_code = []
    for source in sources_list.list:
        if source.disabled == False and source.invalid == False and\
           source.dist == self.codename and\
           source.template.name == self.codename:
            print "yeah! found a distro repo:  %s" % source.line
            if source.type == "deb":
                self.main_sources.append(source)
                comps.extend(source.comps)
                media.append(source.uri)
            elif source.type == "deb-src":
                self.source_code_sources.append(source)
        if source.template in self.source_template.children:
            print "yeah! child found: %s" % source.template.name
            if source.type == "deb":
                self.child_sources.append(source)
    self.enabled_comps = set(comps)
    self.used_media = set(media)

    self.get_mirrors()
  
  def get_mirrors(self):
    """
    Provide a set of mirrors where you can get the distribution from
    """
    # the main server is stored in the template
    self.main_server = self.source_template.base_uri

    # try to guess the nearest mirror from the locale
    # FIXME: for debian we need something different
    if self.id == "Ubuntu":
        locale = os.getenv("LANG", default="en.UK")
        a = locale.find("_")
        z = locale.find(".")
        if z == -1:
            z = len(locale)
        country = locale[a+1:z].lower()
        self.nearest_server = "http://%s.archive.ubuntu.com/ubuntu/" % country

    # other used servers
    for medium in self.used_media:
        if medium.startswith("cdrom:"):
            self.cdrom_available = True
        else:
            # seems to be a network source
            self.use_internet = True
            if not re.match(medium, self.main_server) and \
               not re.match(medium, self.nearest_server):
                self.other_servers.append(medium)


class SoftwareProperties(SimpleGladeApp):

  def __init__(self, datadir=None, options=None, parent=None, file=None):
    gtk.window_set_default_icon_name("software-properties")

    # FIXME: some saner way is needed here
    if datadir == None:
      datadir = "/usr/share/update-manager/"
    self.datadir = datadir
    SimpleGladeApp.__init__(self, datadir+"glade/SoftwareProperties.glade",
                            None, domain="update-manager")
    self.modified = False

    self.file = file

    self.distribution = Distribution()

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
    
    self.init_sourceslist()
    self.reload_sourceslist()

    self.window_main.show()

    # internet update setings
    
    # this maps the key (combo-box-index) to the auto-update-interval value
    # where (-1) means, no key
    self.combobox_interval_mapping = { 0 : 1,
                                       1 : 2,
                                       2 : 7,
                                       3 : 14 }
    self.combobox_update_interval.set_active(0)

    update_days = apt_pkg.Config.FindI(CONF_MAP["autoupdate"])

    self.combobox_update_interval.append_text(_("Daily"))
    self.combobox_update_interval.append_text(_("Every two days"))
    self.combobox_update_interval.append_text(_("Weekly"))
    self.combobox_update_interval.append_text(_("Every two weeks"))

    # If a custom period is defined add an corresponding entry
    if not update_days in self.combobox_interval_mapping.values():
        if update_days > 0:
            self.combobox_update_interval.append_text(_("Every %s days") 
                                                      % update_days)
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

    self.combobox_delete_interval.append_text(_("After one week"))
    self.combobox_delete_interval.append_text(_("After two weeks"))
    self.combobox_delete_interval.append_text(_("After one month"))

    # If a custom period is defined add an corresponding entry
    if not delete_days in self.combobox_delete_interval_mapping.values():
        if delete_days > 0 and CONF_MAP["autoclean"] != 0:
            self.combobox_delete_interval.append_text(_("After %s days") 
                                                      % delete_days)
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

    # drag and drop support for sources.list
    self.treeview_sources.drag_dest_set(gtk.DEST_DEFAULT_ALL, \
                                        [('text/uri-list',0, 0)], \
                                        gtk.gdk.ACTION_COPY)
    self.treeview_sources.connect("drag_data_received",\
                                  self.on_sources_drag_data_received)

    # call the add sources.list dialog if we got a file from the cli
    if self.file != None:
        self.open_file(file)

  def distro_to_widgets(self):
    """
    Represent the distro information in the user interface
    """
    # TRANS: %s stands for the distribution name e.g. Debian or Ubuntu
    self.label_updates.set_label(_("%s Updates") % self.distribution.id)
    # TRANS: %s stands for the distribution name e.g. Debian or Ubuntu
    self.label_dist_software.set_label(_("%s Software") % self.distribution.id)
    self.label_dist_name.set_label("<b>%s</b>" % self.distribution.description)

    # Setup the checkbuttons for the components
    for checkbutton in self.vbox_dist_comps.get_children():
         self.vbox_dist_comps.remove(checkbutton)
    for comp in self.distribution.source_template.components.keys():
        checkbox = gtk.CheckButton(label=self.distribution.source_template.components[comp][2])
        # check if the comp is enabled
        # FIXME: use inconsistence if there are main sources with not all comps
        if comp in self.distribution.enabled_comps:
            checkbox.set_active(True)
        # do not allow to disable an enabled main component
        if comp == "main":
            checkbox.set_property("sensitive", False)
        # setup the callback and show the checkbutton
        checkbox.connect("toggled", self.on_checkbutton_comp_toggled, comp)
        self.vbox_dist_comps.add(checkbox)
        checkbox.show()

    # Setup the checkbuttons for the child repos / updates
    for checkbutton in self.vbox_updates.get_children():
         self.vbox_updates.remove(checkbutton)
    for template in self.distribution.source_template.children:
        checkbox = gtk.CheckButton(label=template.description)
        for child in self.distribution.child_sources:
            if child.template == template:
                # check if all comps of the main source are also enabled 
                # for the child source
                if len(set(child.comps) - self.distribution.enabled_comps) == 0:
                    checkbox.set_active(True)
                elif len(set(child.comps) - self.distribution.enabled_comps) ==\
                     len(self.distribution.enabled_comps):
                    checkbox.set_active(False)
                else:
                    checkbox.set_inconsistent(True)
                #FIXME: currently we don't handle multiple sources of the same
                #       child source - the required effort would be questionable
                break
        # setup the callback and show the checkbutton
        checkbox.connect("toggled", self.on_checkbutton_child_toggled,
                         template.name)
        self.vbox_updates.add(checkbox)
        checkbox.show()

    # setup the location
    # FIXME: how to handle uncommented cdroms?
    if self.distribution.cdrom_available == True:
        self.checkbutton_cdrom.set_active(True)
    else:
        self.checkbutton_cdrom.set_active(False)

    # FIXME: needs inconsistence
    if self.distribution.use_internet == True:
        self.checkbutton_internet.set_active(True)
        self.combobox_server.set_property("sensitive", True)
    else:
        self.checkbutton_internet.set_active(False)
        self.combobox_server.set_property("sensitive", False)
    server_store = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING)
    self.combobox_server.set_model(server_store)
    cell = gtk.CellRendererText()
    self.combobox_server.pack_start(cell, True)
    self.combobox_server.add_attribute(cell, 'text', 0)
    # load the mirror list in to the combo and select the one of the first
    # main source
    server_store.append([_("%s (default)") % self.distribution.main_server, 
                        self.distribution.main_server])
    server_store.append([_("%s (nearest)") % self.distribution.nearest_server, 
                        self.distribution.main_server])
    for server in self.distribution.other_servers:
        server_store.append(["%s" % server, server])
    # FIXME: which one to choose?
    self.combobox_server.set_active(0)


  def on_checkbutton_comp_toggled(self, checkbutton, comp):
    """
    Enable or disable a component for the distribution main repository
    and its children
    """
    print "Set %s to %s" % (checkbutton.get_active(), comp)
    state = checkbutton.get_active()

  def on_checkbutton_child_toggled(self, checkbutton, child):
    """
    Enable or disable a child repo of the distribution main repository
    """
    print "Set %s to %s" % (checkbutton.get_active(), child)

  def open_file(self, file):
    """Show an confirmation for adding the channels of the specified file"""
    #dialog = dialog_sources_list.AddSourcesList(self.window_main,
    #                                            self.sourceslist,
    #                                            self.render_source,
    #                                            self.get_comparable,
    #                                            self.datadir,
    #                                            file)
    #res = dialog.run()
    #if res == gtk.RESPONSE_OK:
    #  self.modified_sourceslist()
    print "droped a sources.list"

  def on_sources_drag_data_received(self, widget, context, x, y,
                                     selection, target_type, timestamp):
      """Extract the dropped file pathes and open the first file, only"""
      uri = selection.data.strip()
      uri_splitted = uri.split()
      if len(uri_splitted)>0:
          self.open_file(uri_splitted[0])

  def hide(self):
    self.window_main.hide()
    
  def init_sourceslist(self):
    """
    Read all valid sources into our ListStore
    """
    # STORE_ACTIVE - is the source enabled or disabled
    # STORE_DESCRIPTION - description of the source entry
    # STORE_SOURCE - the source entry object
    # STORE_SEPARATOR - if the entry is a separator
    # STORE_VISIBLE - if the entry is shown or hidden
    self.source_store = gtk.ListStore(gobject.TYPE_BOOLEAN, 
                                      gobject.TYPE_STRING,
                                      gobject.TYPE_PYOBJECT,
                                      gobject.TYPE_BOOLEAN,
                                      gobject.TYPE_BOOLEAN)
    self.treeview_sources.set_model(self.source_store)
    self.treeview_sources.set_row_separator_func(self.is_separator,
                                                 STORE_SEPARATOR)
    #self.treeview_sources.set_rules_hint(False)

    cell_desc = gtk.CellRendererText()
    cell_desc.set_property("xpad", 2)
    cell_desc.set_property("ypad", 2)
    col_desc = gtk.TreeViewColumn(_("Software Channel"), cell_desc,
                                  markup=COLUMN_DESC)
    col_desc.set_max_width(1000)

    cell_toggle = gtk.CellRendererToggle()
    cell_toggle.set_property("xpad", 2)
    cell_toggle.set_property("ypad", 2)
    cell_toggle.connect('toggled', self.on_channel_toggled)
    col_active = gtk.TreeViewColumn(_("Active"), cell_toggle,
                                    active=COLUMN_ACTIVE)

    self.treeview_sources.append_column(col_active)
    self.treeview_sources.append_column(col_desc)

    self.sourceslist = aptsources.SourcesList()

  def on_channel_activate(self, treeview, path, column):
    """Open the edit dialog if a channel was double clicked"""
    self.on_edit_clicked(treeview)

  def on_treeview_sources_cursor_changed(self, treeview):
    """Enable the buttons remove and edit if a channel is selected"""
    sel = self.treeview_sources.get_selection()
    (model, iter) = sel.get_selected()
    if iter:
        self.button_edit.set_sensitive(True)
        self.button_remove.set_sensitive(True)
    else:
        self.button_edit.set_sensitive(False)
        self.button_remove.set_sensitive(False)
  
  def on_channel_toggled(self, cell_toggle, path):
    """Enable or disable the selected channel"""
    iter = self.source_store.get_iter((int(path),))
    source_entry = self.source_store.get_value(iter, STORE_SOURCE) 
    source_entry.disabled = not source_entry.disabled
    self.modified_sourceslist()

  def init_keyslist(self):
    self.keys_store = gtk.ListStore(str)
    self.treeview2.set_model(self.keys_store)
    
    tr = gtk.CellRendererText()
    
    keys_col = gtk.TreeViewColumn("Key", tr, text=0)
    self.treeview2.append_column(keys_col)
    
  def on_button_revert_clicked(self, button):
    """Restore the source list from the startup of the dialog"""
    self.sourceslist.restoreBackup(".save")
    self.sourceslist.clearBackup(".save")
    self.sourceslist.backup(".save")
    self.sourceslist.refresh()
    self.reload_sourceslist()
    self.button_revert.set_sensitive(False)
    self.modified = False
  
  def modified_sourceslist(self):
    """The sources list was changed and now needs to be saved and reloaded"""
    self.button_revert.set_sensitive(True)
    self.sourceslist.check_for_endangered_dists()
    self.save_sourceslist()
    self.reload_sourceslist()
    self.modified = True

  def render_source(self, source):
    """Render a nice output to show the source in a treeview"""

    if source.template == None:
        if source.comment:
            contents = "<b>%s</b>" % source.comment
            # Only show the components if there are more than one
            if len(source.comps) > 1:
                for c in source.comps:
                    contents += " %s" % c
        else:
            contents = "<b>%s %s</b>" % (source.uri, source.dist)
            for c in source.comps:
                contents += " %s" % c
        if source.type in ("deb-src", "rpm-src"):
            contents += " %s" % _("(Source Code)")
        return contents
    else:
        # try to make use of an corresponding template
        contents = "<b>%s</b>" % source.template.description
        if source.type in ("deb-src", "rpm-src"):
            contents += " (%s)" % _("Source Code")
        if source.comment:
            contents +=" %s" % source.comment
        if source.template.child == False:
            for comp in source.comps:
                if source.template.components.has_key(comp):
                    print source.template.components[comp]
                    (desc, enabled, desc_long) = source.template.components[comp]
                    contents += "\n%s" % desc
                else:
                    contents += "\n%s" % comp
        return contents

  def get_comparable(self, source):
      """extract attributes to sort the sources"""
      cur_sys = 1
      has_template = 1
      has_comment = 1
      is_source = 1
      revert_numbers = string.maketrans("0123456789", "9876543210")
      if source.template:
        has_template = 0
        desc = source.template.description
        if source.template.distribution == self.distribution:
            cur_sys = 0
      else:
          desc = "%s %s %s" % (source.uri, source.dist, source.comps)
          if source.comment:
              has_comment = 0
      if source.type.find("src"):
          is_source = 0
      return (cur_sys, has_template, has_comment, is_source,
              desc.translate(revert_numbers))

  def reload_sourceslist(self):
    (path_x, path_y) = self.treeview_sources.get_cursor()
    self.source_store.clear()
    self.sourceslist.refresh()
    self.sourceslist_visible=[]
    self.distribution.get_sources(self.sourceslist)
    for source in self.sourceslist.list:
      if not source.invalid and\
         source not in self.distribution.main_sources and\
         source not in self.distribution.child_sources:
        self.sourceslist_visible.append(source)

    # Sort the sources list
    self.sourceslist_visible.sort(key=self.get_comparable)

    dist_first = False
    for source in self.sourceslist_visible:
        contents = self.render_source(source)

        self.source_store.append([not source.disabled, contents,
                                  source, False, True])
    self.distro_to_widgets()
    
  def is_separator(self, model, iter, column):
    return model.get_value(iter, column) 
      
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
    conffiles = ["/etc/apt/apt.conf.d/10periodic",
                 "/etc/apt/apt.conf.d/15adept-periodic-update"]

    # check (beforehand) if one exists, if not create one
    for f in conffiles:
      if os.path.isfile(f):
        break
    else:
      print "No config found, creating one"
      open(conffiles[0], "w")

    # now update them
    for periodic in conffiles:
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
    if source_entry.template == None:
        dialog = dialog_edit.dialog_edit(self.window_main, self.sourceslist,
                                         source_entry, self.datadir)
    else:
        dialog = dialog_edit_predefined.dialog_edit_predefined(self.window_main, 
                                                    self.sourceslist,
                                                    source_entry, self.datadir)
    if dialog.run() == gtk.RESPONSE_OK:
        self.modified_sourceslist()

  # FIXME:outstanding from merge
  def on_channel_activated(self, treeview, path, column):
     """Open the edit dialog if a channel was double clicked"""
     # check if the channel can be edited
     if self.button_edit.get_property("sensitive") == True:
         self.on_edit_clicked(treeview)

  # FIXME:outstanding from merge
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
  
