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

import aptsources

class dialog_add:
  def __init__(self, parent, sourceslist, datadir):
    print datadir
    self.sourceslist = sourceslist

    # templates
    self.templatelist = aptsources.SourceEntryTemplates(datadir)

    # FIXME: simple-glade-app should be able to do all this!

    # gtk stuff
    self.gladexml = gtk.glade.XML("%s/glade/SoftwarePropertiesDialogs.glade" % datadir)
    
    self.main = widget = self.gladexml.get_widget("dialog_add")
    self.main.set_transient_for(parent)
    
    combo = self.gladexml.get_widget("combobox_what")
    self.gladexml.signal_connect("on_combobox_what_changed", self.on_combobox_what_changed, None)
    # combox box needs 
    cell = gtk.CellRendererText()
    combo.pack_start(cell, True)
    combo.add_attribute(cell, 'text', 0)
    self.fill_combo(combo)
    self.gladexml.signal_connect("on_button_custom_clicked",
                                 self.on_button_custom_clicked, None)


  def fill_combo(self,combo):
    liststore = gtk.ListStore(gobject.TYPE_STRING,gobject.TYPE_PYOBJECT)
    for item in self.templatelist.templates:
      liststore.append((item.description, item))
    combo.set_model(liststore)
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
    dialog = self.gladexml.get_widget("dialog_add_custom")
    res = dialog.run()
    dialog.hide()
    entry = self.gladexml.get_widget("entry_source_line")
    line = entry.get_text() + "\n"
    self.sourceslist.list.append(aptsources.SourceEntry(line))
    self.main.response(res)

  def get_enabled_comps(self, checkbutton):
    if checkbutton.get_active():
      self.selected_comps.append(checkbutton.get_data("name"))
  
  def run(self):
      res = self.main.run()
      if res == gtk.RESPONSE_OK:
          # add repository
          self.selected_comps = []
          vbox = self.gladexml.get_widget("vbox_comps")
          vbox.foreach(self.get_enabled_comps)
          self.sourceslist.add(self.selected.type,
                               self.selected.uri,
                               self.selected.dist,
                               self.selected_comps)
      self.main.hide()
      return res
