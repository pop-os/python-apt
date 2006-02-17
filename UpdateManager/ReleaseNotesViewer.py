#!/usr/bin/env python

import pygtk
import gtk
import pango
import subprocess
import os

class ReleaseNotesViewer(gtk.TextView):
    def __init__(self, notes):
        gtk.TextView.__init__(self)
        self.hovering = False
        self.buffer = gtk.TextBuffer()
        self.set_buffer(self.buffer)
        self.buffer.set_text(notes)
        self.connect("event-after", self.event_after)
        self.connect("motion-notify-event", self.motion_notify_event)
        self.connect("visibility-notify-event", self.visibility_notify_event)
        self.search_links()
        self.set_property("editable", False)
        self.set_cursor_visible(False)

    def tag_link(self, start, end, url):
        tag = self.buffer.create_tag(None, foreground="blue",
                                     underline=pango.UNDERLINE_SINGLE)
        tag.set_data("url", url)
        self.buffer.apply_tag(tag , start, end)

    def search_links(self):
        iter = self.buffer.get_iter_at_offset(0)
        while 1:
            ret = iter.forward_search("http://", gtk.TEXT_SEARCH_VISIBLE_ONLY,
                                      None)
            if not ret:
                break
            (match_start, match_end) = ret
            match_tmp = match_end.copy()
            while 1:
                if match_tmp.forward_char():
                    text =  match_end.get_text(match_tmp)
                    if text in (" ", ")", "]", "\n", "\t"):
                        break
                else:
                    break
                match_end = match_tmp.copy()
            url = match_start.get_text(match_end)
            self.tag_link(match_start, match_end, url)
            iter = match_end

    def event_after(self, text_view, event):
        if event.type != gtk.gdk.BUTTON_RELEASE:
            return False
        if event.button != 1:
            return False

        try:
            (start, end) = self.buffer.get_selection_bounds()
        except ValueError:
            pass
        else:
            if start.get_offset() != end.get_offset():
                return False

        (x, y) = self.window_to_buffer_coords(gtk.TEXT_WINDOW_WIDGET,
                                              int(event.x), int(event.y))
        iter = self.get_iter_at_location(x, y)
        
        tags = iter.get_tags()
        for tag in tags:
            url = tag.get_data("url")
            if url != "":
                self.open_url(url)
                break

    def open_url(self, url):
        if os.path.exists('usr/bin/gnome-open'):
            command = ['gnome-open', url]
        else:
            command = ['x-www-browser', url]

        if os.getuid() == 0 and os.environ.has_key('SUDO_USER'):
            command = ['sudo', '-u', os.environ['SUDO_USER']] + command

        subprocess.Popen(command)

    def motion_notify_event(self, text_view, event):
        x, y = text_view.window_to_buffer_coords(gtk.TEXT_WINDOW_WIDGET,
                                                 int(event.x), int(event.y))
        self.check_hovering(x, y)
        self.window.get_pointer()
        return False
    
    def visibility_notify_event(self, text_view, event):
        (wx, wy, mod) = text_view.window.get_pointer()
        (bx, by) = text_view.window_to_buffer_coords(gtk.TEXT_WINDOW_WIDGET, wx,
                                                     wy)
        self.check_hovering(bx, by)
        return False

    def check_hovering(self, x, y):
        _hovering = False
        iter = self.get_iter_at_location(x, y)

        tags = iter.get_tags()
        for tag in tags:
            url = tag.get_data("url")
            if url != "":
                _hovering = True
                break
        
        if _hovering != self.hovering:
            self.hovering = _hovering

        if self.hovering:
            self.get_window(gtk.TEXT_WINDOW_TEXT).set_cursor(gtk.gdk.Cursor(gtk.gdk.HAND2))
        else:
            self.get_window(gtk.TEXT_WINDOW_TEXT).set_cursor(gtk.gdk.Cursor(gtk.gdk.XTERM))
