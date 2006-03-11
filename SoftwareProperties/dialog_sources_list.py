#!/usr/bin/env python
import pygtk
import gtk
import gtk.glade
import gobject
import os
from optparse import OptionParser
from aptsources import SourcesList, SourceEntryMatcher
from gettext import gettext as _
import gettext
import urllib
from utils import *

class AddSourcesList:
    def __init__(self, parent, sourceslist, source_renderer, datadir, file):
        print file
        self.parent = parent
        self.source_renderer = source_renderer
        self.sources_old = sourceslist
        self.file = self.format_uri(file)
        self.glade = gtk.glade.XML(os.path.join(datadir,
                     "glade/SoftwarePropertiesDialogs.glade"))
        self.glade.signal_autoconnect(self)
        self.dialog = self.glade.get_widget("dialog_sources_list")
        self.label = self.glade.get_widget("label_sources")
        self.button_add = self.glade.get_widget("button_add")
        self.button_cancel = self.glade.get_widget("button_cancel")
        self.treeview = self.glade.get_widget("treeview_sources")
        self.button_close = self.glade.get_widget("button_close")
        self.scrolled = self.glade.get_widget("scrolled_window")
        self.image = self.glade.get_widget("image_sources_list")

        self.dialog.realize()
        if self.parent != None:
            self.dialog.set_transient_for(parent)
        else:
            self.dialog.set_title(_("Add Software Channels"))
        self.dialog.window.set_functions(gtk.gdk.FUNC_MOVE)

        # Setup the treeview
        self.store = gtk.ListStore(gobject.TYPE_STRING)
        self.treeview.set_model(self.store)
        cell = gtk.CellRendererText()
        cell.set_property("xpad", 2)
        cell.set_property("ypad", 2)
        column = gtk.TreeViewColumn("Software Channel", cell, markup=0)
        column.set_max_width(500)
        self.treeview.append_column(column)

        # Parse the source.list file
        try:
            self.sources = SingleSourcesList(self.file)
        except:
            self.error()
            return

        # show the found channels or an error message
        if len(self.sources.list) > 0:
            self.button_close.hide()
            counter = 0
            for source in self.sources.list:
                if source.invalid or source.disabled:
                    continue
                counter = counter +1
                line = self.source_renderer(source)
                self.store.append([line])
            if counter == 0:
                self.error()
                return

            header = gettext.ngettext("Add the following software channel?",
                                      "Add the following software channels?",
                                      counter)
            body = _("You can install software from a channel. Use "\
                     "trusted channels, only.")
            self.label.set_markup("<big><b>%s</b></big>\n\n%s" % (header, body))
            self.button_add.set_use_underline(True)
            self.button_add.set_label(gettext.ngettext("_Add Channel",
                                                       "_Add Channels",
                                                       counter))
        else:
            self.error()
            return

    def error(self):
        self.button_add.hide()
        self.button_cancel.hide()
        self.scrolled.hide()
        self.button_close.show()
        self.image.set_from_stock(gtk.STOCK_DIALOG_ERROR, gtk.ICON_SIZE_DIALOG)
        header = _("Could not add any software channels")
        body = _("The file '%s' does not contain any valid "
                 "software channels." % self.file)
        self.label.set_markup("<big><b>%s</b></big>\n\n%s" % (header, body))

    def run(self):
        res = self.dialog.run()
        if res == gtk.RESPONSE_OK:
            for source in self.sources:
                self.sources_old.add(source.type,
                                     source.uri,
                                     source.dist,
                                     source.comps,
                                     source.comment)
        self.dialog.destroy()
        return res

    def format_uri(self, uri):
        path = urllib.url2pathname(uri) # escape special chars
        path = path.strip('\r\n\x00') # remove \r\n and NULL
        if path.startswith('file:\\\\\\'): # windows
            path = path[8:] # 8 is len('file:///')
        elif path.startswith('file://'): #nautilus, rox
            path = path[7:] # 7 is len('file://')
        elif path.startswith('file:'): # xffm
            path = path[5:] # 5 is len('file:')
        return path

class SingleSourcesList(SourcesList):
    def __init__(self, file):
        self.matcher = SourceEntryMatcher()
        self.list = []
        self.load(file)
