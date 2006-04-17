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
import dialog_edit

class dialog_add:
  def __init__(self, parent, sourceslist, datadir, source_entry = None):
    self.sourceslist = sourceslist
    self.parent = parent
    self.datadir = datadir
    self.custom = False
    # we have a source_entry that we want to modify
    self.source_entry = source_entry
    if source_entry:
      self.source_entry_index = sourceslist.list.index(source_entry)
    else:
      self.source_entry_index = None
    
    # templates
    self.templatelist = aptsources.SourceEntryTemplates(datadir)

    # FIXME: simple-glade-app should be able to do all this!

    # gtk stuff
    self.gladexml = gtk.glade.XML("%s/glade/SoftwarePropertiesDialogs.glade" % datadir)
    
    self.main = widget = self.gladexml.get_widget("dialog_add")
    self.main.set_transient_for(self.parent)
    
    combo = self.gladexml.get_widget("combobox_what")
    self.gladexml.signal_connect("on_combobox_what_changed", self.on_combobox_what_changed, None)
    # combox box needs 
    cell = gtk.CellRendererText()
    combo.pack_start(cell, True)
    combo.add_attribute(cell, 'text', 0)
    self.fill_combo(combo)
    if source_entry:
      self.main.set_title(_("Edit Channel"))
      self.gladexml.get_widget("button_add").set_label("gtk-ok")
    self.gladexml.signal_connect("on_button_custom_clicked",
                                 self.on_button_custom_clicked, None)


  def fill_combo(self,combo):
    liststore = gtk.ListStore(gobject.TYPE_STRING,gobject.TYPE_PYOBJECT)
    matched_template = None
    for item in self.templatelist.templates:
      liststore.append((item.description, item))
      if self.source_entry and item.matches(self.source_entry):
        matched_template = item
    combo.set_model(liststore)
    if matched_template:
      try:
        combo.set_active(self.templatelist.templates.index(matched_template))
        vbox = self.gladexml.get_widget("vbox_comps")
        for c in vbox.get_children():
          c.set_active(c.get_data("name") in self.source_entry.comps)
      except ValueError:
        pass
    else:
      combo.set_active(0)

  def on_combobox_what_changed(self, combobox, user):
    #print "on_combobox_what_changed"
    vbox = self.gladexml.get_widget("vbox_comps")
    vbox.foreach(lambda widget,vbox:  vbox.remove(widget), vbox)
    liststore = combobox.get_model()
    a_iter = liststore.iter_nth_child(None, combobox.get_active())
    (name, template) = liststore.get(a_iter, 0,1)
    self.selected = template
    comps = template.comps
    for c in comps:
      checkbox = gtk.CheckButton(c.description)
      checkbox.set_active(c.on_by_default)
      checkbox.set_data("name",c.name)
      vbox.pack_start(checkbox)
      checkbox.show()

  def on_button_custom_clicked(self, widget, data):
    #print "on_button_custom_clicked()"
    # this hide here is ugly :/
    self.main.hide()
    # check if we are in add or edit-matched mode
    if self.source_entry:
      # we are in "edit" mode
      # get the SourceEntry as it is now (with local changes)
      # and display the "old" edit dialog
      self.selected_comps = []
      vbox = self.gladexml.get_widget("vbox_comps")
      vbox.foreach(self.get_enabled_comps)
      source_entry = self._make_source_entry()
      # since we're passing the SourceEntry as it is now,
      # this SourceEntry needs to be in the sourceslist,
      # so temporarily swap the original for the current
      if source_entry:
        self.sourceslist.list[self.source_entry_index] = source_entry
      dialog = dialog_edit.dialog_edit(self.parent, self.sourceslist,
                                       source_entry, self.datadir)
      res = dialog.run()
      if res == gtk.RESPONSE_CANCEL:
        # restore original SourceEntry
        self.sourceslist.list[self.source_entry_index] = self.source_entry
      elif res == gtk.RESPONSE_OK:
        # the sourceslist is allready updated, but we'll overwrite it
        # in self.run if we're not carefull
        self.custom = True
    else:
      # we are in "add" mode
      dialog = self.gladexml.get_widget("dialog_add_custom")
      dialog.set_transient_for(self.parent)
      res = dialog.run()
      dialog.hide()
      entry = self.gladexml.get_widget("entry_source_line")
      line = entry.get_text() + "\n"
      self.sourceslist.list.append(aptsources.SourceEntry(line))
    self.main.response(res)

  def get_enabled_comps(self, checkbutton):
    if checkbutton.get_active():
      self.selected_comps.append(checkbutton.get_data("name"))
  
  def _make_source_entry(self):
    " helper for the 'edit' mode "
    # we use "selected" for pretty much everything *but* we use
    # self.source_entry.uri to make sure that the mirror information is
    # preserved

    line = "%s %s %s" % (self.selected.type, self.source_entry.uri, self.selected.dist)
    if self.source_entry.disabled:
      line = "#" + line
    if len(self.selected.comps) > 0 and len(self.selected_comps) == 0:
      line = "#" + line
    elif len(self.selected_comps) > 0:
      line += " " + " ".join(self.selected_comps)
    if self.selected.matches(self.source_entry) and self.source_entry.comment != "":
      line += " #"+self.source_entry.comment
    line += "\n"
    return aptsources.SourceEntry(line,self.source_entry.file)
  
  def run(self):
      res = self.main.run()
      if res == gtk.RESPONSE_OK:
          # add repository
          self.selected_comps = []
          vbox = self.gladexml.get_widget("vbox_comps")
          vbox.foreach(self.get_enabled_comps)
           
          # check if we are in 'add' or 'edit' mode
          if self.source_entry:
            # 'edit' - ode
            # check if there are no selected components
            if len(self.selected_comps) < 1:
              # remove the source
              self.sourceslist.remove(self.source_entry)
            else:
              if not self.custom:
                entry = self._make_source_entry()
                if entry:
                  self.sourceslist.list[self.source_entry_index] = entry
          else:
            # 'add' mode
            self.sourceslist.add(self.selected.type,
                                 self.selected.uri,
                                 self.selected.dist,
                                 self.selected_comps)
      self.main.hide()
      return res
