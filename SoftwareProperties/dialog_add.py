# dialog_add.py.in - dialog to add a new repository
#  
#  Copyright (c) 2004-2005 Canonical
#                2005 Michiel Sikkes
#              
#  Authors: 
#       Michael Vogt <mvo@debian.org>
#       Michiel Sikkes <michiels@gnome.org>
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

import os
import gobject
import gtk
import gtk.glade
from gettext import gettext as _

import aptsources

class dialog_add:
  def __init__(self, parent, sourceslist, datadir):
    self.sourceslist = sourceslist
    self.parent = parent
    
    # templates
    self.templatelist = aptsources.SourceEntryTemplates(datadir)

    # FIXME: simple-glade-app should be able to do all this!

    # gtk stuff
    self.gladexml = gtk.glade.XML("%s/glade/SoftwarePropertiesDialogs.glade" % datadir)
    
    self.main = widget = self.gladexml.get_widget("dialog_add")
    self.main.set_transient_for(self.parent)

    self.vbox = self.gladexml.get_widget("vbox_comps")

    # Setup the official channel widgets
    self.combo = self.gladexml.get_widget("combobox_what")
    self.gladexml.signal_connect("on_combobox_what_changed", self.on_combobox_what_changed, None)
    cell = gtk.CellRendererText()
    self.combo.pack_start(cell, True)
    self.combo.add_attribute(cell, 'text', 0)
    self.fill_combo(self.combo)
    self.label_dist = self.gladexml.get_widget("label_dist")
    if self.templatelist.dist != "":
        # TRANSLATORS: %s is the distribution name, eg. Ubuntu or Debian
        self.label_dist.set_markup("<b>%s</b>" %  \
                                   _("%s channels" % self.templatelist.dist))

    # Setup the custom channel widgets
    self.entry = self.gladexml.get_widget("entry_source_line")
    self.gladexml.signal_connect("on_entry_source_line_changed",
                                 self.check_line)

    # Setup the toggle action
    self.radio_official = self.gladexml.get_widget("radiobutton_official")
    self.radio_custom = self.gladexml.get_widget("radiobutton_custom")
    self.button_add = self.gladexml.get_widget("button_add_channel")
    self.gladexml.signal_connect("on_radiobutton_custom_toggled",
                                 self.on_radio_custom_toggled)
    self.gladexml.signal_connect("on_radiobutton_official_toggled",
                                 self.on_radio_official_toggled)

    # We start with the official channels:
    self.official = True
    self.radio_custom.toggled()

  def check_line(self, *args):
    """Check for a valid apt line"""
    if self.official == True:
      self.button_add.set_sensitive(True)
      return

    line = self.entry.get_text() + "\n"
    source_entry = aptsources.SourceEntry(line)
    if source_entry.invalid == True or source_entry.disabled == True:
      self.button_add.set_sensitive(False)
    else:
      self.button_add.set_sensitive(True)

  
  def on_radio_custom_toggled(self, radio):
    state = radio.get_active()
    self.entry.set_sensitive(state)
    self.check_line()

  def on_radio_official_toggled(self, radio):
    state = radio.get_active()
    self.combo.set_sensitive(state)
    for check in self.comps:
        check.set_sensitive(state)
    self.official = state
    self.count_comps()

  def fill_combo(self,combo):
    liststore = gtk.ListStore(gobject.TYPE_STRING,gobject.TYPE_PYOBJECT)
    for item in self.templatelist.templates:
      liststore.append((item.description, item))
    combo.set_model(liststore)
    combo.set_active(0)

  def on_combobox_what_changed(self, combobox, user):
    #print "on_combobox_what_changed"
    self.vbox.foreach(lambda widget,vbox:  self.vbox.remove(widget), self.vbox)
    liststore = combobox.get_model()
    a_iter = liststore.iter_nth_child(None, combobox.get_active())
    (name, template) = liststore.get(a_iter, 0,1)
    self.selected = template

    # figure what is currently active in the sources.list
    already_enabled_comps = []
    for entry in self.sourceslist:
      if entry.disabled or entry.invalid or entry.type != "deb":
        continue
      if template.dist == entry.dist and \
            self.sourceslist.is_mirror(template.uri, entry.uri):
        already_enabled_comps = entry.comps
        
    comps = template.comps
    self.comps=[]
    for c in comps:
      checkbox = gtk.CheckButton(c.description)
      # show what should be enabled by default if the source was not found
      # else show the already enabled ones
      if len(already_enabled_comps) == 0:
        checkbox.set_active(c.on_by_default)
      else:
        checkbox.set_active(c.name in already_enabled_comps)
      checkbox.set_data("name",c.name)
      checkbox.connect("toggled", self.count_comps)
      self.vbox.pack_start(checkbox)
      checkbox.show()
      self.comps.append(checkbox)
    self.count_comps()

  def get_enabled_comps(self, checkbutton):
    if checkbutton.get_active():
      self.selected_comps.append(checkbutton.get_data("name"))
  
  def count_comps(self, *args):
    button_add = self.gladexml.get_widget("button_add_channel")
    self.selected_comps=[]
    self.vbox.foreach(self.get_enabled_comps)
    if len(self.selected_comps) > 0:
      button_add.set_sensitive(True)
    else:
      button_add.set_sensitive(False)

  def run(self):
      res = self.main.run()
      if res == gtk.RESPONSE_OK:
          # add repository
          if self.official == True:
            #self.selected_comps = []
            self.sourceslist.add(self.selected.type,
                                 self.selected.uri,
                                 self.selected.dist,
                                 self.selected_comps)
          else:
            line = self.entry.get_text() + "\n"
            self.sourceslist.list.append(aptsources.SourceEntry(line))
      self.main.hide()
      return res
