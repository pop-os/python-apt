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

    def _write(self, msg, newline=True, maximize=False):
        """Write the message on the terminal, fill remaining space."""
        self._file.write("\r")
        self._file.write(msg)
        # Fill remaining stuff with whitespace
        if self._width > len(msg):
            self._file.write((self._width - len(msg)) * ' ')
        elif maximize: # Needed for OpProgress.
            self._width = max(self._width, len(msg))
        if newline:
            self._file.write("\n")
        else:
            #self._file.write("\r")
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
        self._write("%s... %i%%\r" % (self.op, self.percent), False, True)
        self.old_op = self.op

    def done(self):
        """Called once an operation has been completed."""
        apt_pkg.OpProgress.done(self)
        if self.old_op:
            self._write("%s... Done" % self.old_op, True, True)
        self.old_op = ""


class AcquireProgress(apt_pkg.AcquireProgress, TextProgress):
    """AcquireProgress for the text interface."""

    def __init__(self, outfile=None):
        TextProgress.__init__(self, outfile)
        apt_pkg.AcquireProgress.__init__(self)
        import signal
        self._signal = signal.signal(signal.SIGWINCH, self._winch)
        self._winch()
        self._id = 1L

    def _winch(self, *a):
        import fcntl
        import termios
        import struct
        buf = fcntl.ioctl(self._file.fileno(),termios.TIOCGWINSZ, 8 * ' ')
        row, col, rpx, cpx = struct.unpack('hhhh', buf)
        self._width = col - 1 # 1 for the cursor

    def ims_hit(self, item):
        """Called when an item is update (e.g. not modified on the server)."""
        line = 'Hit %s' % item.description
        if (item.owner.filesize != 0):
            line+= ' [%sB]' % apt_pkg.size_to_str(item.owner.filesize)
        self._write(line)

    def fail(self, item):
        """Called when an item is failed."""
        if item.owner.status == item.owner.stat_done:
            self._write("Ign %s" % item.description)
        else:
            self._write("Err %s" % item.description)
            self._write("  %s" % item.owner.error_text)

    def fetch(self, item):
        """Called when some of the item's data is fetched."""
        item.owner.id = self._id
        self._id += 1
        line = "Get:%s %s" % (item.owner.id, item.description)
        if item.owner.filesize != 0:
            line += (" [%sB]" % apt_pkg.size_to_str(item.owner.filesize))

        self._write(line)

    def pulse(self, owner):
        """Periodically invoked while the Acquire process is underway.

        Return False if the user asked to cancel the whole Acquire process."""

        percent = (((self.current_bytes + self.current_items) * 100.0) /
                        float(self.total_bytes + self.total_items))

        shown = False
        mode = 'long'
        tval = '%i%%' % percent

        end = ""
        if self.current_cps:
            eta = int(float(self.total_bytes - self.current_bytes) / self.current_cps)
            end = " %sB/s %s" % (apt_pkg.size_to_str(self.current_cps),
                            apt_pkg.time_to_str(eta))

        for worker in owner.workers:
            val = ''
            if not worker.current_item:
                if worker.status:
                    tval += ' [%s]' % worker.status
                    shown = True
                continue
            shown = True

            if worker.current_item.owner.id != 0:
                val += " [%i %s" % (worker.current_item.owner.id, worker.current_item.shortdesc)
            else:
                val += ' [%s' % worker.current_item.description
            if worker.current_item.owner.mode:
                val += ' %s' % worker.current_item.owner.mode
            if mode == 'long' and False:
                val += ' %i' % worker.current_size
            elif mode == 'medium' or worker.total_size == 0 or True:
                val += ' %sB' % apt_pkg.size_to_str(worker.current_size)

            # Add the total size and percent
            if worker.total_size > 0 and worker.current_item.owner.complete == False:
                if mode == 'short':
                    val += ' %i%%' % worker.current_size*100.0/worker.total_size
                else:
                    val += "/%sB %i%%" % ( apt_pkg.size_to_str(worker.total_size),
                            worker.current_size*100.0/worker.total_size )

            val += ']'

            tval += val

        if not shown:
            tval += ' [Working]'

        if self.current_cps:
            tval += (self._width - len(end) - len(tval)) * ' ' + end

        if len(tval) <= self._width:
            self._write(tval, False)
        else:
            self._write(tval)
        return True

    def media_change(self, medium, drive):
        """Prompt the user to change the inserted removable media."""
        print ("Media change: please insert the disc labeled "
               "'%s' in the drive '%s' and press enter") % (medium, drive)

        return raw_input() not in ('c', 'C')

    def stop(self):
        """Invoked when the Acquire process stops running."""
        if self.fetched_bytes != 0:
            self._write("Fetched %sB in %s (%sB/s)" % (
	                    apt_pkg.size_to_str(self.fetched_bytes),
                        apt_pkg.time_to_str(self.elapsed_time),
                        apt_pkg.size_to_str(self.current_cps)))
