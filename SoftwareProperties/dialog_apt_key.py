# dialog_apt_key.py.in - edit the apt keys
#  
#  Copyright (c) 2004 Canonical
#  
#  Author: Michael Vogt <mvo@debian.org>
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
import subprocess
import gettext
from utils import *
from subprocess import PIPE

# gettext convenient
_ = gettext.gettext
def dummy(e): return e
N_ = dummy

# some known keys
N_("Ubuntu Archive Automatic Signing Key <ftpmaster@ubuntu.com>")
N_("Ubuntu CD Image Automatic Signing Key <cdimage@ubuntu.com>")

class apt_key:
    def __init__(self):
        self.gpg = ["/usr/bin/gpg"]
        self.base_opt = self.gpg + ["--no-options", "--no-default-keyring",
                                    "--secret-keyring", "/etc/apt/secring.gpg",
                                    "--trustdb-name", "/etc/apt/trustdb.gpg",
                                    "--keyring", "/etc/apt/trusted.gpg"]
        self.list_opt = self.base_opt + ["--with-colons", "--batch",
                                         "--list-keys"]
        self.rm_opt = self.base_opt + ["--quiet", "--batch",
                                       "--delete-key", "--yes"]
        self.add_opt = self.base_opt + ["--quiet", "--batch",
                                        "--import"]
        
       
    def list(self):
        res = []
        #print self.list_opt
        p = subprocess.Popen(self.list_opt,stdout=PIPE).stdout
        for line in p.readlines():
            fields = line.split(":")
            if fields[0] == "pub":
                name = fields[9]
                res.append("%s %s\n%s" %((fields[4])[-8:],fields[5], _(name)))
        return res

    def add(self, filename):
        #print "request to add " + filename
        cmd = self.add_opt[:]
        cmd.append(filename)
        p = subprocess.Popen(cmd)
        return (p.wait() == 0)
        
    def update(self):
        cmd = ["/usr/bin/apt-key", "update"]
        p = subprocess.Popen(cmd)
        return (p.wait() == 0)

    def rm(self, key):
        #print "request to remove " + key
        cmd = self.rm_opt[:]
        cmd.append(key)
        p = subprocess.Popen(cmd)
        return (p.wait() == 0)

class dialog_apt_key:
  def __init__(self, parent, datadir):
    # gtk stuff
    if os.path.exists("../data/SoftwarePropertiesDialogs.glade"):
      self.gladexml = gtk.glade.XML("../data/SoftwarePropertiesDialogs.glade")
    else:
      self.gladexml = gtk.glade.XML("%s/SoftwarePropertiesDialogs.glade", datadir)
    self.main = self.gladexml.get_widget("dialog_apt_key")
    self.main.set_transient_for(parent)

    self.gladexml.signal_connect("on_button_key_add_clicked",
                                 self.on_button_key_add_clicked)
    self.gladexml.signal_connect("on_button_key_remove_clicked",
                                 self.on_button_key_remove_clicked)
    self.gladexml.signal_connect("on_button_apt_key_update_clicked",
                                 self.on_button_apt_key_update_clicked)

    # create apt-key object (abstraction for the apt-key command)
    self.apt_key = apt_key()
    
    # get some widgets
    self.treeview_apt_key = self.gladexml.get_widget("treeview_apt_key")
    self.liststore_apt_key = gtk.ListStore(str)
    self.treeview_apt_key.set_model(self.liststore_apt_key)
    # Create columns and append them.
    tr = gtk.CellRendererText()
    tr.set_property("xpad", 10)
    tr.set_property("ypad", 10)
    c0 = gtk.TreeViewColumn("Key", tr, text=0)
    self.treeview_apt_key.append_column(c0)
    self.update_key_list()

  def on_button_apt_key_update_clicked(self, widget):
      self.apt_key.update()
      self.update_key_list()

  def on_button_key_add_clicked(self, widget):
      chooser = gtk.FileChooserDialog(title=_("Choose a key-file"),
                                      parent=self.main,
                                      buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_REJECT,
                                               gtk.STOCK_OK,gtk.RESPONSE_ACCEPT))
      res = chooser.run()
      chooser.hide()
      if res == gtk.RESPONSE_ACCEPT:
          #print chooser.get_filename()
          if not self.apt_key.add(chooser.get_filename()):
              dialog_error(self.main,
                    _("Error importing selected file"),
                    _("The selected file may not be a GPG key file "
                      "or it might be corrupt."))
          self.update_key_list()
          
  def on_button_key_remove_clicked(self, widget):
      selection = self.treeview_apt_key.get_selection()
      (model,a_iter) = selection.get_selected()
      if a_iter == None:
          return
      key = model.get_value(a_iter,0)
      if not self.apt_key.rm(key[:8]):
          error(self.main,
                _("Error removing the key"),
                _("The key you selected could not be removed. "
                  "Please report this as a bug."))
      self.update_key_list()

  def update_key_list(self):
      self.liststore_apt_key.clear()
      for key in self.apt_key.list():
          self.liststore_apt_key.append([key])

  def run(self):
      res = self.main.run()
      self.main.hide()


if __name__ == "__main__":
    ui = dialog_apt_key(None)
    ui.run()

