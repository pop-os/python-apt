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

import UpdateManager.Common.aptsources as aptsources

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
    self.button_edit_ok = self.gladexml.get_widget("button_edit_ok")
    
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

    # finally set the signal so that the check function is not tiggered 
    # during initialisation
    self.gladexml.signal_connect("on_entry_source_line_changed",
                                 self.check_line)

  def check_line(self, *args):
    """Check for a valid apt line and set the sensitiveness of the
       button 'add' accordingly"""
    line = self.get_line()
    if line == False:
      self.button_edit_ok.set_sensitive(False)
      return
    source_entry = aptsources.SourceEntry(line)
    if (source_entry.invalid == True or source_entry.disabled == True):
      self.button_edit_ok.set_sensitive(False)
    else:
      self.button_edit_ok.set_sensitive(True)

  def get_line(self):
    """Collect all values from the entries and create an apt line"""
    combo_type = self.gladexml.get_widget("combobox_type")
    if combo_type.get_active() == 0:
      line = "deb"
    else:
      line = "deb-src"

    entry = self.gladexml.get_widget("entry_uri")
    text = entry.get_text()
    if len(text) < 1 or text.find(" ") != -1 or text.find("#") != -1:
      return False  
    line = line + " " + entry.get_text()

    entry = self.gladexml.get_widget("entry_dist")
    text = entry.get_text()
    if len(text) < 1 or text.find(" ") != -1 or text.find("#") != -1:
      return False    
    line = line + " " + entry.get_text()

    entry = self.gladexml.get_widget("entry_comps")
    text = entry.get_text()
    if len(text) < 1 or text.find("#") != -1:
      return False    
    line = line + " " + entry.get_text()

    entry = self.gladexml.get_widget("entry_comment")
    if entry.get_text() != "":
      line = line + " #" + entry.get_text() + "\n"
    else:
      line = line + "\n"
    return line
          
  def run(self):
      res = self.main.run()
      if res == gtk.RESPONSE_OK:
        line = self.get_line()

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
