# Copyright (c) 2009 Julian Andres Klode <jak@debian.org>
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
"""Progress reporting for text interfaces."""
import sys

import apt_pkg

__all__ = ['AcquireProgress', 'OpProgress']


class TextProgress(object):
    """Internal Base class for text progress classes."""

    def __init__(self, outfile=None):
        self._file = outfile or sys.stdout
        self._width = 0

    def _write(self, msg, newline=True):
        """Write the message on the terminal, fill remaining space."""
        self._file.write("\r")
        self._file.write(msg)
        # Fill remaining stuff with whitespace
        if self._width > len(msg):
            self._file.write((self._width - len(msg)) * ' ')
        else:
            self._width = max(self._width, len(msg))
        if newline:
            self._file.write("\n")
        else:
            self._file.write("\r")
            self._file.flush()


class OpProgress(apt_pkg.OpProgress, TextProgress):
    """Operation progress reporting.

    This closely resembles OpTextProgress in libapt-pkg.
    """

    def __init__(self, outfile=None):
        TextProgress.__init__(self, outfile)
        apt_pkg.OpProgress.__init__(self)
        self.old_op = ""

    def update(self, percent=None):
        """Called periodically to update the user interface."""
        if percent:
            self.percent = percent
        apt_pkg.OpProgress.update(self)
        if self.major_change and self.old_op:
            self._write(self.old_op)
        self._write("%s... %i%%" % (self.op, self.percent), False)
        self.old_op = self.op

    def done(self):
        """Called once an operation has been completed."""
        apt_pkg.OpProgress.done(self)
        if self.old_op:
            self._write("%s... Done" % self.old_op)
        self.old_op = ""


class AcquireProgress(apt_pkg.AcquireProgress, TextProgress):
    """AcquireProgress for the text interface."""

    def ims_hit(self, item):
        """Called when an item is update (e.g. not modified on the server)."""
        self._write("Hit   %s" % item.description)

    def done(self, item):
        """Called when an item is completely fetched."""
        self._write("Done  %s" % item.description)

    def fail(self, item):
        """Called when an item is failed."""
        self._write("Fail  %s" % item.description)

    def fetch(self, item):
        """Called when some of the item's data is fetched."""
        self._write("Fetch %s" % item.description)

    def pulse(self, owner):
        """Periodically invoked while the Acquire process is underway.

        Return False if the user asked to cancel the whole Acquire process."""

        percent = (((self.current_bytes + self.current_items) * 100.0) /
                        float(self.total_bytes + self.total_items))
        if self.current_cps > 0:
            eta = ((self.total_bytes - self.current_bytes) /
                        float(self.current_cps))
            self._write("[%2.f%%] %sB/s %s" % (percent,
                                    apt_pkg.size_to_str(int(self.current_cps)),
                                    apt_pkg.time_to_str(int(eta))), False)
        else:
            self._write("%2.f%% [Working]" % (percent), False)
        return True

    def media_change(self, medium, drive):
        """Prompt the user to change the inserted removable media."""
        print ("Media change: please insert the disc labeled "
               "'%s' in the drive '%s' and press enter") % (medium, drive)

        return raw_input() not in ('c', 'C')

    def stop(self):
        """Invoked when the Acquire process stops running."""
        self._write("Done downloading")
