import pygtk
pygtk.require('2.0')
import gtk
import apt
from gettext import gettext as _

class GtkOpProgress(apt.progress.OpProgress):
  def __init__(self, progressbar):
      self._progressbar = progressbar
  def update(self, percent):
      self._progressbar.show()
      self._progressbar.set_text(self.op)
      self._progressbar.set_fraction(percent/100.0)
      while gtk.events_pending():
          gtk.main_iteration()
  def done(self):
      self._progressbar.hide()

