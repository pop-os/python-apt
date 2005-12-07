# dialog_edit.py.in - edit a existing repository
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

class dialog_edit:
  def __init__(self, parent, sourceslist, source_entry, datadir):
    self.sourceslist = sourceslist
    self.source_entry = source_entry

    # gtk stuff
    if os.path.exists("../data/SoftwarePropertiesDialogs.glade"):
      self.gladexml = gtk.glade.XML("../data/SoftwarePropertiesDialogs.glade")
    else:
      self.gladexml = gtk.glade.XML("%s/glade/SoftwarePropertiesDialogs.glade" % datadir)
    self.main = self.gladexml.get_widget("dialog_edit")
    self.main.set_transient_for(parent)
    
    # type
    combo_type = self.gladexml.get_widget("combobox_type")
    if source_entry.type == "deb":
      combo_type.set_active(0)
    elif source_entry.type == "deb-src":
      combo_type.set_active(1)
    else:
      print "Error, unknown source type: '%s'" % source_enrty.type

    # uri
    entry = self.gladexml.get_widget("entry_uri")
    entry.set_text(source_entry.uri)

    entry = self.gladexml.get_widget("entry_dist")
    entry.set_text(source_entry.dist)

    entry = self.gladexml.get_widget("entry_comps")
    comps = ""
    for c in source_entry.comps:
      if len(comps) > 0:
        comps = comps + " " + c
      else:
        comps = c
    entry.set_text(comps)

    entry = self.gladexml.get_widget("entry_comment")
    entry.set_text(source_entry.comment)

  def run(self):
      res = self.main.run()
      if res == gtk.RESPONSE_OK:
        # get values
        combo_type = self.gladexml.get_widget("combobox_type")
        if combo_type.get_active() == 0:
          line = "deb"
        else:
          line = "deb-src"
        entry = self.gladexml.get_widget("entry_uri")
        line = line + " " + entry.get_text()

        entry = self.gladexml.get_widget("entry_dist")
        line = line + " " + entry.get_text()

        entry = self.gladexml.get_widget("entry_comps")
        line = line + " " + entry.get_text()

        entry = self.gladexml.get_widget("entry_comment")
        if entry.get_text() != "":
          line = line + " #" + entry.get_text() + "\n"
        else:
          line = line + "\n"

        # change repository
        index = self.sourceslist.list.index(self.source_entry)
        file = self.sourceslist.list[index].file
        self.sourceslist.list[index] = aptsources.SourceEntry(line,file)
        #self.sourceslist.add(self.selected.type,
        #                     self.selected.uri,
        #                     self.selected.dist,
        #                     self.selected_comps)
      self.main.hide()
      return res
