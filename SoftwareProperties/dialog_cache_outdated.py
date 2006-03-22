# dialog_cache_outdated.py - inform the user to update the apt cache
#  
#  Copyright (c) 2006 Canonical
#  
#  Authors: 
#       Sebastian Heinlein <sebastian.heinlein@web.de>
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
import subprocess
import thread
import time
import gobject
import gtk
import gtk.glade
import apt_pkg

class DialogCacheOutdated:
    def __init__(self, parent, datadir):
        """setup up the gtk dialog"""
        self.parent = parent

        if os.path.exists("../data/SoftwarePropertiesDialogs.glade"):
            self.gladexml = gtk.glade.XML("../data/SoftwarePropertiesDialogs.glade")
        else:
            self.gladexml = gtk.glade.XML("%s/glade/SoftwarePropertiesDialogs.glade" % datadir)
        self.dialog = self.gladexml.get_widget("dialog_cache_outofdate")
        self.dialog.set_transient_for(parent)

    def update_cache(self, window_id, lock):
        """start synaptic to update the package cache"""
        try:
            apt_pkg.PkgSystemUnLock()
        except SystemError:
            pass
        cmd = ["/usr/sbin/synaptic", "--hide-main-window",
               "--non-interactive",
               "--parent-window-id", "%s" % (window_id),
               "--update-at-startup"]
        subprocess.call(cmd)
        lock.release()

    def run(self):
        """run the dialog, and if reload was pressed run synaptic"""
        res = self.dialog.run()
        self.dialog.hide()
        if res == gtk.RESPONSE_APPLY:
            self.parent.set_sensitive(False)
            lock = thread.allocate_lock()
            lock.acquire()
            t = thread.start_new_thread(self.update_cache,
                                       (self.parent.window.xid, lock))
            while lock.locked():
                while gtk.events_pending():
                    gtk.main_iteration()
                    time.sleep(0.05)
            self.parent.set_sensitive(True)
        return res
