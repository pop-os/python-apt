# apt/progress/base.py - Base classes for progress reporting.
#
# Copyright (C) 2009 Julian Andres Klode <jak@debian.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA
"""Base classes for progress reporting.

Custom progress classes should inherit from these classes. They can also be
used as dummy progress classes which simply do nothing.
"""


class AcquireProgress(object):
    """Monitor object for downloads controlled by the Acquire class.

    This is an mostly abstract class. You should subclass it and implement the
    methods to get something useful.
    """

    current_bytes = current_cps = fetched_bytes = last_bytes = total_bytes \
                  = 0.0
    current_items = elapsed_time = total_items = 0

    def done(self, item):
        """Invoked when an item is successfully and completely fetched."""

    def fail(self, item):
        """Invoked when an item could not be fetched."""

    def fetch(self, item):
        """Invoked when some of the item's data is fetched."""

    def ims_hit(self, item):
        """Invoked when an item is confirmed to be up-to-date.

        Invoked when an item is confirmed to be up-to-date. For instance,
        when an HTTP download is informed that the file on the server was
        not modified.
        """

    def media_change(self, media, drive):
        """Prompt the user to change the inserted removable media.

        The parameter 'media' decribes the name of the the media type that
        should be changed, whereas the parameter 'drive' should be the
        identifying name of the drive whose media should be changed.

        This method should not return until the user has confirmed to the user
        interface that the media change is complete. It must return True if
        the user confirms the media change, or False to cancel it.
        """
        return False

    def pulse(self, owner):
        """Periodically invoked while the Acquire process is underway.

        This method gets invoked while the Acquire progress given by the
        parameter 'owner' is underway. It should display information about
        the current state.

        This function returns a boolean value indicating whether the
        acquisition should be continued (True) or cancelled (False).
        """
        return True

    def start(self):
        """Invoked when the Acquire process starts running."""
        # Reset all our values.
        self.current_bytes = 0.0
        self.current_cps = 0.0
        self.current_items = 0
        self.elapsed_time = 0
        self.fetched_bytes = 0.0
        self.last_bytes = 0.0
        self.total_bytes = 0.0
        self.total_items = 0

    def stop(self):
        """Invoked when the Acquire process stops running."""


class CdromProgress(object):
    """Base class for reporting the progress of adding a cdrom.

    Can be used with apt_pkg.Cdrom to produce an utility like apt-cdrom. The
    attribute 'total_steps' defines the total number of steps and can be used
    in update() to display the current progress.
    """

    total_steps = 0

    def ask_cdrom_name(self):
        """Ask for the name of the cdrom.

        If a name has been provided, return it. Otherwise, return None to
        cancel the operation.
        """

    def change_cdrom(self):
        """Ask for the CD-ROM to be changed.

        Return True once the cdrom has been changed or False to cancel the
        operation.
        """

    def update(self, text, current):
        """Periodically invoked to update the interface.

        The string 'text' defines the text which should be displayed. The
        integer 'current' defines the number of completed steps.
        """


class InstallProgress(object):
    """Report the install progress.

    Subclass this class to implement install progress reporting.
    """

    def start_update(self):
        """Start update."""

    def run(self, pm):
        """Start installation."""
        return pm.do_install()

    def finish_update(self):
        """Called when update has finished."""

    def update_interface(self):
        """Called periodically to update the user interface."""


class OpProgress(object):
    """Monitor objects for operations.

    Display the progress of operations such as opening the cache."""

    major_change, op, percent, subop = False, "", 0.0, ""

    def update(self, percent=None):
        """Called periodically to update the user interface.

        You may use the optional argument 'percent' to set the attribute
        'percent' in this call.
        """
        if percent is not None:
            self.percent = percent

    def done(self):
        """Called once an operation has been completed."""
