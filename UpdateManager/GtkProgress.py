# GtkProgress.py 
#  
#  Copyright (c) 2004,2005 Canonical
#  
#  Author: Michael Vogt <michael.vogt@ubuntu.com>
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

import pygtk
pygtk.require('2.0')
import gtk
import apt
import apt_pkg
from gettext import gettext as _
from Common.utils import *

# intervals of the start up progress
# 3x caching and menu creation
STEPS_UPDATE_CACHE = [33, 66, 100]

class GtkOpProgress(apt.OpProgress):
    def __init__(self, host_window, progressbar, status, parent,
                 steps=STEPS_UPDATE_CACHE):
        # used for the "one run progressbar"
        self.steps = steps[:]
        self.base = 0
        self.old = 0
        self.next = int(self.steps.pop(0))

        self._parent = parent
        self._window = host_window
        self._status = status
        self._progressbar = progressbar
        # Do not show the close button 
        self._window.realize()
        host_window.window.set_functions(gtk.gdk.FUNC_MOVE)
        self._window.set_transient_for(parent)

    def update(self, percent):
        #print percent
        #print self.Op
        #print self.SubOp
        self._window.show()
        self._parent.set_sensitive(False)
        # if the old percent was higher, a new progress was started
        if self.old > percent:
            # set the borders to the next interval
            self.base = self.next
            try:
                self.next = int(self.steps.pop(0))
            except:
                pass
        progress = self.base + percent/100 * (self.next - self.base)
        self.old = percent
        self._status.set_markup("<i>%s</i>" % self.op)
        self._progressbar.set_fraction(progress/100.0)
        while gtk.events_pending():
            gtk.main_iteration()

    def done(self):
        self._parent.set_sensitive(True)
    def hide(self):
        self._window.hide()

class GtkFetchProgress(apt.progress.FetchProgress):
    def __init__(self, parent, summary="", descr=""):
        # if this is set to false the download will cancel
        self._continue = True
        # init vars here
        # FIXME: find a more elegant way, this sucks
        self.summary = parent.label_fetch_summary
        self.status = parent.label_fetch_status
        self.progress = parent.progressbar_fetch
        self.window_fetch = parent.window_fetch
        self.window_fetch.set_transient_for(parent.window_main)
        self.window_fetch.realize()
        self.window_fetch.window.set_functions(gtk.gdk.FUNC_MOVE)
        # set summary
        if self.summary != "":
            self.summary.set_markup("<big><b>%s</b></big> \n\n%s" %
                                    (summary, descr))
    def start(self):
        self.progress.set_fraction(0)
        self.window_fetch.show()
    def stop(self):
        self.window_fetch.hide()
    def on_button_fetch_cancel_clicked(self, widget):
        self._continue = False
    def pulse(self):
        apt.progress.FetchProgress.pulse(self)
        currentItem = self.currentItems + 1
        if currentItem > self.totalItems:
          currentItem = self.totalItems
        if self.currentCPS > 0:
            statusText = (_("Downloading file %(current)li of %(total)li with "
                            "%(speed)s/s") % {"current" : currentItem,
                                              "total" : self.totalItems,
                                              "speed" : humanize_size(self.currentCPS)})
        else:
            statusText = (_("Downloading file %(current)li of %(total)li") % \
                          {"current" : currentItem,
                           "total" : self.totalItems })
            self.progress.set_fraction(self.percent/100.0)
        self.status.set_markup("<i>%s</i>" % statusText)
        # TRANSLATORS: show the remaining time in a progress bar:
        #self.progress.set_text(_("About %s left" % (apt_pkg.TimeToStr(self.eta))))
	# FIXME: show remaining time
        self.progress.set_text("")

        while gtk.events_pending():
            gtk.main_iteration()
        return self._continue
