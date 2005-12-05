#!/usr/bin/python2.4

import pygtk
pygtk.require('2.0')
import gtk
import gtk.gdk
import gtk.glade

import apt
import apt_pkg
import sys

from UpdateManager.Common.SimpleGladeApp import SimpleGladeApp
from UpdateManager.GtkProgress import GtkOpProgress
from SoftwareProperties.aptsources import SourcesList, SourceEntry
from gettext import gettext as _

class DistUpgradeProgress(object):
    pass


class DistUpgradeView(object):
    " abstraction for the upgrade view "
    def __init__(self):
        pass
    def getOpCacheProgress(self):
        " return a OpProgress() subclass for the given graphic"
        return apt.progress.OpProgress()
    def updateStatus(self, msg):
        """ update the current status of the distUpgrade based
            on the current view
        """
        pass
    def askYesNoQuestion(self,msg):
        pass
    def error(self, summary, msg):
        pass
        

class GtkDistUpgradeView(DistUpgradeView,SimpleGladeApp):
    " gtk frontend of the distUpgrade tool "
    def __init__(self):
        # FIXME: i18n must be somewhere relative do this dir
        SimpleGladeApp.__init__(self, "DistUpgrade.glade",
                                None, domain="update-manager")
        self._opCacheProgress = GtkOpProgress(self.progressbar_cache)
    def getOpCacheProgress(self):
        return self._opCacheProgress
    def updateStatus(self, msg):
        self.label_status.set_markup("<b>%s</b>" % msg)
    def error(self, summary, msg):
        dialog = gtk.MessageDialog(self.window_main, 0, gtk.MESSAGE_ERROR,
                                   gtk.BUTTONS_OK,"")
        msg=("<big><b>%s</b></big>\n\n%s"%(summary,msg))
        dialog.set_markup(msg)
        dialog.vbox.set_spacing(6)
        dialog.run()
        dialog.destroy()
        return False
        
class DistUpgradeControler(object):
    def __init__(self, distUpgradeView):
        self._view = distUpgradeView
        self._view.updateStatus(_("Reading cache"))
        self._cache = apt.Cache(self._view.getOpCacheProgress())

    def sanityCheck(self):
        if self._cache._depcache.BrokenCount > 0:
            # FIXME: we more helpful here and offer to actually fix the
            # system
            self._view.error(_("Broken packages"),
                             _("Your system contains broken packages. "
                               "Please fix them first using synaptic or "
                               "apt-get before proceeding."))
            return False
        # FIXME: check for ubuntu-desktop, kubuntu-dekstop, edubuntu-desktop
        return True

    def updateSourcesList(self, fromDist, to):
        sources = SourcesList()

        # this must map, i.e. second in "from" must be the second in "to"
        # (but they can be different, so in theory we could exchange
        #  component names here)
        fromDists = [fromDist,
                     fromDist+"-security",
                     fromDist+"-updates",
                     fromDist+"-backports"
                    ]
        toDists = [to,
                   to+"-security",
                   to+"-updates",
                   to+"-backports"
                   ]

        # list of valid mirrors that we can add
        valid_mirrors = ["http://archive.ubuntu.com/ubuntu",
                         "http://security.ubuntu.com/ubuntu"]

        # look over the stuff we have
        foundToDist = False
        for entry in sources:
            # check if it's a mirror (or offical site)
            for mirror in valid_mirrors:
                if sources.is_mirror(mirror,entry.uri):
                    if entry.dist in toDists:
                        # so the sources.list is already set to the new
                        # distro
                        foundToDist = True
                    elif entry.dist in fromDists:
                        foundToDist = True
                        entry.dist = toDists[fromDists.index(entry.dist)]
                    else:
                        # disable all entries that are official but don't
                        # point to the "from" dist
                        entry.disabled = True
                    # it can only be one valid mirror, so we can break here
                    break
                else:
                    # disable non-official entries that point to dist
                    if entry.dist == fromDist:
                        entry.disabled = True

        if not foundToDist:
            # FIXME: offer to write a new sources.list entry
            return self._view.error(_("No valid entry found"),
                                    _("While scaning your repository "
                                      "information no valid entry for "
                                      "the upgrade was found.\n"))
        
        # write (well, backup first ;) !
        backup_ext = ".distUpgrade"
        sources.backup(backup_ext)
        sources.save()

        # re-check if the written sources are valid, if not revert and
        # bail out
        try:
            sourceslist = apt_pkg.GetPkgSourceList()
            sourceslist.ReadMainList()
        except SystemError:
            sources.restoreBackup(backup_ext)
            self._view.error(_("Repository information invalid"),
                             _("Upgrading the repository information "
                               "resulted in a invalid file. Please "
                               "report this as a bug."))
            return False
        return True

    def breezyUpgrade(self):
        # sanity check (check for ubuntu-desktop, brokenCache etc)
        self._view.updateStatus(_("Checking the system"))
        if not self.sanityCheck():
            sys.exit(1)

        # update sources.list
        self._view.updateStatus(_("Updating repository information"))
        if not self.updateSourcesList(fromDist="hoary",to="breezy"):
            sys.exit(1)

        # then update the package index files
        

        # then open the cache (again)
        self._view.updateStatus(_("Reading cache"))
        self._cache = apt.Cache(self._view.getOpCacheProgress())

        # do pre-upgrade stuff

        # calc the dist-upgrade and see if the removals are ok/expected

        # do the dist-upgrade

        # do post-upgrade stuff

        # done, ask for reboot

    def run(self):
        self.breezyUpgrade()


if __name__ == "__main__":
    view = GtkDistUpgradeView()
    app = DistUpgradeControler(view)
    app.run()
