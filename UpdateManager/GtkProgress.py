import pygtk
pygtk.require('2.0')
import gtk
import apt
import apt_pkg
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
        # set summary
        if self.summary != "":
            self.summary.set_markup("<big><b>%s</b></big> \n\n%s" %
                                    (summary, descr))
            self.window_fetch.set_title(summary)
    def start(self):
	self.progress.set_fraction(0)
        self.window_fetch.show()
    def stop(self):
	self.window_fetch.hide()
    def on_button_fetch_cancel_clicked(self, widget):
        self._continue = False
    def pulse(self):
        apt.progress.FetchProgress.pulse(self)
        if self.currentCPS > 0:
            self.status.set_text(_("Download rate: %s/s - %s remaining" % (apt_pkg.SizeToStr(self.currentCPS), apt_pkg.TimeToStr(self.eta))))
        else:
            self.status.set_text(_("Download rate: unkown"))
	self.progress.set_fraction(self.percent/100.0)
        currentItem = self.currentItems + 1
        if currentItem > self.totalItems:
          currentItem = self.totalItems
        self.progress.set_text(_("Downloading file %li of %li" % (currentItem, self.totalItems)))
	while gtk.events_pending():
		gtk.main_iteration()
        return self._continue
