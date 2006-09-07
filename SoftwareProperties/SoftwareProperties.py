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

#import pdb
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
import UpdateManager.Common.aptsources as aptsources
import dialog_add
import dialog_edit
import dialog_cache_outdated
import dialog_add_sources_list
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

RESPONSE_REPLACE = 1
RESPONSE_ADD = 2

# columns of the source_store
(
    STORE_ACTIVE, 
    STORE_DESCRIPTION, 
    STORE_SOURCE, 
    STORE_SEPARATOR,
    STORE_VISIBLE
) = range(5)


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

    self.distro = aptsources.Distribution()
    cell = gtk.CellRendererText()
    self.combobox_server.pack_start(cell, True)
    self.combobox_server.add_attribute(cell, 'text', 0)
    
    # set up the handler id for the callbacks 
    self.handler_server_changed = self.combobox_server.connect("changed", 
                                  self.on_combobox_server_changed)
    self.handler_source_code_changed = self.checkbutton_source_code.connect(
                                         "toggled",
                                         self.on_checkbutton_source_code_toggled
                                         )

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
    self.backup_sourceslist()

    self.window_main.show()

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
    self.label_updates.set_label("<b>%s</b>" % (_("%s updates") %\
                                                self.distro.id))
    # TRANS: %s stands for the distribution name e.g. Debian or Ubuntu
    self.label_dist_name.set_label("%s" % self.distro.description)

    # Setup the checkbuttons for the components
    for checkbutton in self.vbox_dist_comps.get_children():
         self.vbox_dist_comps.remove(checkbutton)
    for comp in self.distro.source_template.components.keys():
        # TRANSLATORS: Label for the components in the Internet section
        #              first %s is the description of the component
        #              second %s is the code name of the comp, eg main, universe
        label = _("%s (%s)") % (self.distro.source_template.components[comp][2],
                                comp)
        checkbox = gtk.CheckButton(label)
        # check if the comp is enabled
        # FIXME: use inconsistence if there are main sources with not all comps
        if comp in self.distro.download_comps:
            checkbox.set_active(True)
        # setup the callback and show the checkbutton
        checkbox.connect("toggled", self.on_component_toggled, comp)
        self.vbox_dist_comps.add(checkbox)
        checkbox.show()

    # Setup the checkbuttons for the child repos / updates
    for checkbutton in self.vbox_updates.get_children():
         self.vbox_updates.remove(checkbutton)
    for template in self.distro.source_template.children:
        checkbox = gtk.CheckButton(label=template.description)
        comps = []
        for child in self.distro.child_sources:
            if child.template == template:
                comps.extend(child.comps)
        # check if all comps of the main source are also enabled 
        # for the corresponding child sources
        if len(comps) > 0 and \
             len(self.distro.enabled_comps ^ set(comps)) == 0:
            # the cild source covers all components
            checkbox.set_active(True)
        elif len(comps) > 0 and\
             len(self.distro.enabled_comps ^ set(comps)) != 0:
            # the cild is enabled, but doesn't cover 
            # all components
            checkbox.set_active(False)
            checkbox.set_inconsistent(True)
        else:
            # there is no corresponding child source at all
            checkbox.set_active(False)
        # setup the callback and show the checkbutton
        checkbox.connect("toggled", self.on_checkbutton_child_toggled,
                         template)
        self.vbox_updates.add(checkbox)
        checkbox.show()

    if len(self.distro.enabled_comps) < 1:
        self.vbox_updates.set_sensitive(False)
    else:
        self.vbox_updates.set_sensitive(True)

    # Intiate the combobox which allows do specify a server for all
    # distro related sources
    self.combobox_server.handler_block(self.handler_server_changed)
    server_store = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING)
    self.combobox_server.set_model(server_store)
    server_store.append([_("Main server"),
                        self.distro.main_server])
    if self.distro.country != None:
        # TRANSLATORS: %s is a country
        server_store.append([_("Server for %s") % gettext.dgettext("iso-3166",
                             self.distro.country).rstrip(),
                             self.distro.nearest_server])
    else:
        server_store.append([_("Nearest server"),
                             self.distro.nearest_server])
    if len(self.distro.used_servers) > 0:
        for server in self.distro.used_servers:
            if not re.match(server, self.distro.main_server) and \
               not re.match(server, self.distro.nearest_server):
                # FIXME: use regexp here instead of this
                country = ""
                i = server.find("://")
                l = server.find(".archive.ubuntu.com")
                if i != -1 and l != -1:
                  country = server[i+len("://"):l]
                if self.distro.countries.has_key(country):
                    # TRANSLATORS: %s is a country
                    server_store.append([_("Server for %s") % \
                                        gettext.dgettext("iso-3166",
                                        self.distro.countries[country].rstrip()),
                                        server])
                else:
                    server_store.append(["%s" % server, server])
        if len(self.distro.used_servers) > 1:
            server_store.append([_("Custom servers"), None])
            self.combobox_server.set_active(2)
        elif self.distro.used_servers[0] == self.distro.main_server:
            self.combobox_server.set_active(0)
        elif self.distro.used_servers[0] == self.distro.nearest_server:
            self.combobox_server.set_active(1)
        elif len(self.distro.used_servers) == 1:
            self.combobox_server.set_active(2)

    else:
        self.combobox_server.set_active(0)

    self.combobox_server.handler_unblock(self.handler_server_changed)

    # Check for source code sources
    self.checkbutton_source_code.handler_block(self.handler_source_code_changed)
    self.checkbutton_source_code.set_inconsistent(False)
    if len(self.distro.source_code_sources) < 1:
        # we don't have any source code sources, so
        # uncheck the button
        self.checkbutton_source_code.set_active(False)
        self.distro.get_source_code = False
    else:
        # there are source code sources, so we check the button
        self.checkbutton_source_code.set_active(True)
        self.distro.get_source_code = True
        # check if there is a corresponding source code source for
        # every binary source. if not set the checkbutton to inconsistent
        templates = {}
        sources = []
        sources.extend(self.distro.main_sources)
        sources.extend(self.distro.child_sources)
        for source in sources:
            if templates.has_key(source.template):
                for comp in source.comps:
                    templates[source.template].add(comp)
            else:
                templates[source.template] = set(source.comps)
        # add fake http sources for the cdrom, since the sources
        # for the cdrom are only available in the internet
        if len(self.distro.cdrom_sources) > 0:
            templates[self.distro.source_template] = self.distro.cdrom_comps
        for source in self.distro.source_code_sources:
            if not templates.has_key(source.template) or \
               (templates.has_key(source.template) and not \
                (len(set(templates[source.template]) ^ set(source.comps)) == 0\
                 or (len(set(source.comps) ^ self.distro.enabled_comps) == 0))):
                self.checkbutton_source_code.set_inconsistent(True)
                self.distro.get_source_code = False
                break
    self.checkbutton_source_code.handler_unblock(self.handler_source_code_changed)

    if len(self.cdrom_store) == 0:
        self.treeview_cdroms.set_sensitive(False)
    else:
        self.treeview_cdroms.set_sensitive(True)

    if self.options.debug == True or self.options.massive_debug == True:
        print "ENABLED COMPS: %s" % self.distro.enabled_comps
        print "INTERNET COMPS: %s" % self.distro.download_comps
        print "MAIN SOURCES"
        for source in self.distro.main_sources:
            self.print_source_entry(source)
        print "CHILD SOURCES"
        for source in self.distro.child_sources:
            self.print_source_entry(source)
        print "CDROM SOURCES"
        for source in self.distro.cdrom_sources:
            self.print_source_entry(source)
        print "SOURCE CODE SOURCES"
        for source in self.distro.source_code_sources:
            self.print_source_entry(source)
        print "DISABLED SOURCES"
        for source in self.distro.disabled_sources:
            self.print_source_entry(source)
        print "ISV"
        for source in self.sourceslist_visible:
            self.print_source_entry(source)

  def print_source_entry(self, source):
    """Print the data of a source entry to the command line"""
    print source.dist
    for (label, value) in [("URI:", source.uri),
                           ("Comps:", source.comps),
                           ("Enabled:", not source.disabled),
                           ("Valid:", not source.invalid)]:
        print " %s %s" % (label, value)
    if source.template:
        for (label, value) in [("MatchURI:", source.template.match_uri),
                               ("BaseURI:", source.template.base_uri)]:
            print " %s %s" % (label, value)
    print "\n"

  def on_combobox_server_changed(self, combobox):
    """
    Replace the servers used by the main and update sources with
    the selected one
    """
    server_store = combobox.get_model()
    iter = combobox.get_active_iter()
    uri_selected = server_store.get_value(iter, 1)
    sources = []
    sources.extend(self.distro.main_sources)
    sources.extend(self.distro.child_sources)
    sources.extend(self.distro.source_code_sources)
    for source in sources:
        # FIXME: ugly
        if not "security.ubuntu.com" in source.uri:
            source.uri = uri_selected
    self.distro.ddefault_server = uri_selected
    self.modified_sourceslist()

  def on_component_toggled(self, checkbutton, comp):
    """
    Sync the components of all main sources (excluding cdroms),
    child sources and source code sources
    """
    if checkbutton.get_active() == True:
        self.distro.enable_component(self.sourceslist, comp)
    else:
        self.distro.disable_component(self.sourceslist, comp)
    self.modified_sourceslist()

  def massive_debug_output(self):
      """
      do not write our changes yet - just print them to std_out
      """
      print "START SOURCES.LIST:"
      for source in self.sourceslist:
          print source.str()
      print "END SOURCES.LIST\n"

  def on_checkbutton_child_toggled(self, checkbutton, template):
    """
    Enable or disable a child repo of the distribution main repository
    """
    if checkbutton.get_active() == False:
        for source in self.distro.child_sources:
            if source.template == template:
                self.sourceslist.remove(source)
    else:
        self.distro.add_source(self.sourceslist,
                                     uri=template.base_uri,
                                     dist=template.name)
    self.modified_sourceslist()
  
  def on_checkbutton_source_code_toggled(self, checkbutton):
    """
    Disable or enable the source code for all sources
    """
    self.distro.get_source_code = checkbutton.get_active()
    sources = []
    sources.extend(self.distro.main_sources)
    sources.extend(self.distro.child_sources)

    # remove all exisiting sources
    for source in self.distro.source_code_sources:
        self.sourceslist.remove(source)

    if checkbutton.get_active() == True:
        for source in sources:
            self.sourceslist.add("deb-src",
                                 source.uri,
                                 source.dist,
                                 source.comps,
                                 "Added by software-properties",
                                 self.sourceslist.list.index(source)+1,
                                 source.file)
        for source in self.distro.cdrom_sources:
            self.sourceslist.add("deb-src",
                                 self.distro.source_template.base_uri,
                                 self.distro.source_template.name,
                                 source.comps,
                                 "Added by software-properties",
                                 self.sourceslist.list.index(source)+1,
                                 source.file)
    self.modified_sourceslist()

  def on_checkbutton_popcon_toggled(self, widget):
    """ The user clicked on the popcon paritipcation button """
    popcon = "/etc/popularity-contest.conf"
    if widget.get_active():
      new_value = "yes"
    else:
      new_value = "no"
    if os.path.exists(popcon):
      # read it
      lines = open(popcon).read().split("\n")
      for line in lines:
        try:
          (key,value) = line.split("=")
          if key == "PARTICIPATE":
            lines[lines.index(line)] = 'PARTICIPATE=\"%s"' % new_value
        except ValueError:
          continue
      # write it
      open(popcon,"w").write("\n".join(lines))


  def open_file(self, file):
    """Show an confirmation for adding the channels of the specified file"""
    dialog = dialog_add_sources_list.AddSourcesList(self.window_main,
                                                    self.sourceslist,
                                                    self.render_source,
                                                    self.get_comparable,
                                                    self.datadir,
                                                    file)
    (res, new_sources) = dialog.run()
    if res == RESPONSE_REPLACE:
        self.sourceslist.list = []
    if res in (RESPONSE_ADD, RESPONSE_REPLACE):
        for source in new_sources:
            self.sourceslist.add(source.type,
                                 source.uri,
                                 source.dist,
                                 source.comps,
                                 source.comment)
        self.modified_sourceslist()

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
    self.cdrom_store = gtk.ListStore(gobject.TYPE_BOOLEAN, 
                                     gobject.TYPE_STRING,
                                     gobject.TYPE_PYOBJECT,
                                     gobject.TYPE_BOOLEAN,
                                     gobject.TYPE_BOOLEAN)
    self.treeview_cdroms.set_model(self.cdrom_store)
    self.source_store = gtk.ListStore(gobject.TYPE_BOOLEAN, 
                                      gobject.TYPE_STRING,
                                      gobject.TYPE_PYOBJECT,
                                      gobject.TYPE_BOOLEAN,
                                      gobject.TYPE_BOOLEAN)
    self.treeview_sources.set_model(self.source_store)
    self.treeview_sources.set_row_separator_func(self.is_separator,
                                                 STORE_SEPARATOR)

    cell_desc = gtk.CellRendererText()
    cell_desc.set_property("xpad", 2)
    cell_desc.set_property("ypad", 2)
    col_desc = gtk.TreeViewColumn(_("Software Channel"), cell_desc,
                                  markup=COLUMN_DESC)
    col_desc.set_max_width(1000)

    cell_toggle = gtk.CellRendererToggle()
    cell_toggle.set_property("xpad", 2)
    cell_toggle.set_property("ypad", 2)
    cell_toggle.connect('toggled', self.on_channel_toggled, self.cdrom_store)
    col_active = gtk.TreeViewColumn(_("Active"), cell_toggle,
                                    active=COLUMN_ACTIVE)

    self.treeview_cdroms.append_column(col_active)
    self.treeview_cdroms.append_column(col_desc)

    cell_desc = gtk.CellRendererText()
    cell_desc.set_property("xpad", 2)
    cell_desc.set_property("ypad", 2)
    col_desc = gtk.TreeViewColumn(_("Software Channel"), cell_desc,
                                  markup=COLUMN_DESC)
    col_desc.set_max_width(1000)

    cell_toggle = gtk.CellRendererToggle()
    cell_toggle.set_property("xpad", 2)
    cell_toggle.set_property("ypad", 2)
    cell_toggle.connect('toggled', self.on_channel_toggled, self.source_store)
    col_active = gtk.TreeViewColumn(_("Active"), cell_toggle,
                                    active=COLUMN_ACTIVE)

    self.treeview_sources.append_column(col_active)
    self.treeview_sources.append_column(col_desc)

    self.sourceslist = aptsources.SourcesList()

  def backup_sourceslist(self):
    """
    Duplicate the list of sources
    """
    self.sourceslist_backup = []
    for source in self.sourceslist.list:
        source_bkp = aptsources.SourceEntry(line=source.line,file=source.file)
        self.sourceslist_backup.append(source_bkp)

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
  
  def on_channel_toggled(self, cell_toggle, path, store):
    """Enable or disable the selected channel"""
    #FIXME cdroms need to disable the comps in the childs and sources
    iter = store.get_iter((int(path),))
    source_entry = store.get_value(iter, STORE_SOURCE) 
    source_entry.disabled = not source_entry.disabled
    store.set_value(iter, STORE_ACTIVE, not source_entry.disabled)
    self.modified_sourceslist()

  def init_keyslist(self):
    self.keys_store = gtk.ListStore(str)
    self.treeview2.set_model(self.keys_store)
    
    tr = gtk.CellRendererText()
    
    keys_col = gtk.TreeViewColumn("Key", tr, text=0)
    self.treeview2.append_column(keys_col)
    
  def on_button_revert_clicked(self, button):
    """Restore the source list from the startup of the dialog"""
    self.sourceslist.list = []
    for source in self.sourceslist_backup:
        source_reset = aptsources.SourceEntry(line=source.line,file=source.file)
        self.sourceslist.list.append(source_reset)
    self.save_sourceslist()
    self.reload_sourceslist()
    self.button_revert.set_sensitive(False)
    self.modified = False
  
  def modified_sourceslist(self):
    """The sources list was changed and now needs to be saved and reloaded"""
    if self.options.massive_debug == True:
        self.massive_debug_output()
    self.modified = True
    self.button_revert.set_sensitive(True)
    self.save_sourceslist()
    self.reload_sourceslist()

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
        if source.template.distribution == self.distro:
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
    self.cdrom_store.clear()
    self.sourceslist.refresh()
    self.sourceslist_visible=[]
    self.distro.get_sources(self.sourceslist)
    # Only show sources that are no binary or source code repos for
    # the current distribution, but show cdrom based repos
    for source in self.sourceslist.list:
        if not source.invalid and\
           (source not in self.distro.main_sources and\
            source not in self.distro.cdrom_sources and\
            source not in self.distro.child_sources and\
            source not in self.distro.disabled_sources) and\
           source not in self.distro.source_code_sources:
            self.sourceslist_visible.append(source)
        elif not source.invalid and source in self.distro.cdrom_sources:
            contents = self.render_source(source)
            self.cdrom_store.append([not source.disabled, contents,
                                    source, False, True])

    # Sort the sources list
    self.sourceslist_visible.sort(key=self.get_comparable)

    for source in self.sourceslist_visible:
        contents = self.render_source(source)

        self.source_store.append([not source.disabled, contents,
                                  source, False, True])

    (path_x, path_y) = self.treeview_sources.get_cursor()
    if len(self.source_store) < 1 or path_x <0:
        self.button_remove.set_sensitive(False)
        self.button_edit.set_sensitive(False)
    self.distro.get_sources(self.sourceslist)
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

  def on_add_clicked(self, widget):
    dialog = dialog_add.dialog_add(self.window_main, self.sourceslist,
                                   self.datadir)
    line = dialog.run()
    if line != None:
      self.sourceslist.list.append(aptsources.SourceEntry(line))
      self.modified_sourceslist()
      
  def on_edit_clicked(self, widget):
    sel = self.treeview_sources.get_selection()
    (model, iter) = sel.get_selected()
    if not iter:
      return
    source_entry = model.get_value(iter, LIST_ENTRY_OBJ)
    dialog = dialog_edit.dialog_edit(self.window_main, self.sourceslist,
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
    model = self.treeview_sources.get_model()
    (path, column) = self.treeview_sources.get_cursor()
    iter = model.get_iter(path)
    if iter:
      source = model.get_value(iter, LIST_ENTRY_OBJ)
      self.sourceslist.remove(source)
      self.modified_sourceslist()

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
    self.on_close_button(widget)

  def on_close_button(self, widget):
    # show a dialog that a reload of the channel information is required
    # only if there is no parent defined
    if self.modified == True and \
       self.options.toplevel == None:
        d = dialog_cache_outdated.DialogCacheOutdated(self.window_main,
                                                      self.datadir)
        res = d.run()
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

 # def on_channel_toggled(self, cell_toggle, path, store):
 #     """Enable or disable the selected channel"""
 #     iter = store.get_iter((int(path),))
  #    source_entry = store.get_value(iter, LIST_ENTRY_OBJ)
  #    source_entry.disabled = not source_entry.disabled
  #    self.reload_sourceslist()
  #    self.modified = True

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
  
    
