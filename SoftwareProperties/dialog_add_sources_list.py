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
    def __init__(self, parent, sourceslist, source_renderer,
                 get_comparable, datadir, file):
        print file
        self.parent = parent
        self.source_renderer = source_renderer
        self.sourceslist = sourceslist
        self.get_comparable = get_comparable
        self.file = self.format_uri(file)
        self.glade = gtk.glade.XML(os.path.join(datadir,
                     "glade/SoftwarePropertiesDialogs.glade"))
        self.glade.signal_autoconnect(self)
        self.dialog = self.glade.get_widget("dialog_add_sources_list")
        self.label = self.glade.get_widget("label_sources")
        self.button_add = self.glade.get_widget("button_add")
        self.button_cancel = self.glade.get_widget("button_cancel")
        self.button_replace = self.glade.get_widget("button_replace")
        self.treeview = self.glade.get_widget("treeview_sources")
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
            self.new_sources = SingleSourcesList(self.file)
        except:
            self.error()
            return

        # show the found channels or an error message
        if len(self.new_sources.list) > 0:
            counter = 0

            for source in self.new_sources.list:
                if source.invalid or source.disabled:
                    continue
                self.new_sources.matcher.match(source)
            # sort the list
            self.new_sources.list.sort(key=self.get_comparable)
            
            for source in self.new_sources.list:
                if source.invalid or source.disabled:
                    continue
                counter = counter +1
                line = self.source_renderer(source)
                self.store.append([line])
            if counter == 0:
                self.error()
                return

            header = gettext.ngettext("Install software additionally or "
                                      "only from this source?",
                                      "Install software additionally or "
                                      "only from these sources?",
                                      counter)
            body = _("You can either add the following sources or replace your "
                     "current sources by them. Only install software from "
                     "trusted sources.")
            self.label.set_markup("<big><b>%s</b></big>\n\n%s" % (header, body))
        else:
            self.error()
            return

    def error(self):
        self.button_add.hide()
        self.button_cancel.set_use_stock(True)
        self.button_cancel.set_label("gtk-close")
        self.button_replace.hide()
        self.scrolled.hide()
        self.image.set_from_stock(gtk.STOCK_DIALOG_ERROR, gtk.ICON_SIZE_DIALOG)
        header = _("There are no sources to install software from")
        body = _("The file '%s' does not contain any valid "
                 "software sources." % self.file)
        self.label.set_markup("<big><b>%s</b></big>\n\n%s" % (header, body))

    def run(self):
        res = self.dialog.run()
        self.dialog.destroy()
        return res, self.new_sources

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
