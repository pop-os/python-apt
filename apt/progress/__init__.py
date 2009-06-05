# progress.py - progress reporting classes
#
#  Copyright (c) 2005-2009 Canonical
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
"""progress reporting classes.

This module provides classes for progress reporting. They can be used with
e.g., for reporting progress on the cache opening process, the cache update
progress, or the package install progress.
"""

import errno
import fcntl
import os
import re
import select
import sys

import apt_pkg
from apt.deprecation import AttributeDeprecatedBy, function_deprecated_by


__all__ = ('CdromProgress', 'DpkgInstallProgress', 'DumbInstallProgress',
          'FetchProgress', 'InstallProgress', 'OpProgress', 'OpTextProgress',
          'TextFetchProgress')


class OpProgress(object):
    """Abstract class to implement reporting on cache opening.

    Subclass this class to implement simple Operation progress reporting.
    """

    def __init__(self):
        self.op = None
        self.sub_op = None

    def update(self, percent):
        """Called periodically to update the user interface."""

    def done(self):
        """Called once an operation has been completed."""

    if apt_pkg._COMPAT_0_7:
        subOp = AttributeDeprecatedBy('sub_op')


class OpTextProgress(OpProgress):
    """A simple text based cache open reporting class."""

    def __init__(self):
        OpProgress.__init__(self)

    def update(self, percent):
        """Called periodically to update the user interface."""
        sys.stdout.write("\r%s: %.2i  " % (self.sub_op, percent))
        sys.stdout.flush()

    def done(self):
        """Called once an operation has been completed."""
        sys.stdout.write("\r%s: Done\n" % self.op)


class FetchProgress(object):
    """Report the download/fetching progress.

    Subclass this class to implement fetch progress reporting
    """

    # download status constants
    dl_done = 0
    dl_queued = 1
    dl_failed = 2
    dl_hit = 3
    dl_ignored = 4
    dl_status_str = {dl_done: "Done",
                   dl_queued: "Queued",
                   dl_failed: "Failed",
                   dl_hit: "Hit",
                   dl_ignored: "Ignored"}

    def __init__(self):
        self.eta = 0.0
        self.percent = 0.0
        # Make checking easier
        self.current_bytes = 0
        self.current_items = 0
        self.total_bytes = 0
        self.total_items = 0
        self.current_cps = 0

    def start(self):
        """Called when the fetching starts."""

    def stop(self):
        """Called when all files have been fetched."""

    def update_status(self, uri, descr, short_descr, status):
        """Called when the status of an item changes.

        This happens eg. when the downloads fails or is completed.
        """

    def pulse(self):
        """Called periodically to update the user interface.

        Return True to continue or False to cancel.
        """
        self.percent = (((self.current_bytes + self.current_items) * 100.0) /
                        float(self.total_bytes + self.total_items))
        if self.current_cps > 0:
            self.eta = ((self.total_bytes - self.current_bytes) /
                        float(self.current_cps))
        return True

    def media_change(self, medium, drive):
        """react to media change events."""

    if apt_pkg._COMPAT_0_7:
        dlDone = AttributeDeprecatedBy('dl_done')
        dlQueued = AttributeDeprecatedBy('dl_queued')
        dlFailed = AttributeDeprecatedBy('dl_failed')
        dlHit = AttributeDeprecatedBy('dl_hit')
        dlIgnored = AttributeDeprecatedBy('dl_ignored')
        dlStatusStr = AttributeDeprecatedBy('dl_status_str')
        currentBytes = AttributeDeprecatedBy('current_bytes')
        currentItems = AttributeDeprecatedBy('current_items')
        totalBytes = AttributeDeprecatedBy('total_bytes')
        totalItems = AttributeDeprecatedBy('total_items')
        currentCPS = AttributeDeprecatedBy('current_cps')
        updateStatus = function_deprecated_by(update_status)
        mediaChange = function_deprecated_by(media_change)


class TextFetchProgress(FetchProgress):
    """ Ready to use progress object for terminal windows """

    def __init__(self):
        FetchProgress.__init__(self)
        self.items = {}

    def update_status(self, uri, descr, short_descr, status):
        """Called when the status of an item changes.

        This happens eg. when the downloads fails or is completed.
        """
        if status != self.dl_queued:
            print "\r%s %s" % (self.dl_status_str[status], descr)
        self.items[uri] = status

    def pulse(self):
        """Called periodically to update the user interface.

        Return True to continue or False to cancel.
        """
        FetchProgress.pulse(self)
        if self.current_cps > 0:
            s = "[%2.f%%] %sB/s %s" % (self.percent,
                                    apt_pkg.size_to_str(int(self.current_cps)),
                                    apt_pkg.time_to_str(int(self.eta)))
        else:
            s = "%2.f%% [Working]" % (self.percent)
        print "\r%s" % (s),
        sys.stdout.flush()
        return True

    def stop(self):
        """Called when all files have been fetched."""
        print "\rDone downloading            "

    def media_change(self, medium, drive):
        """react to media change events."""
        print ("Media change: please insert the disc labeled "
               "'%s' in the drive '%s' and press enter") % (medium, drive)

        return raw_input() not in ('c', 'C')

    if apt_pkg._COMPAT_0_7:
        updateStatus = function_deprecated_by(update_status)
        mediaChange = function_deprecated_by(media_change)


class DumbInstallProgress(object):
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
        """Called periodically to update the user interface"""

    if apt_pkg._COMPAT_0_7:
        startUpdate = function_deprecated_by(start_update)
        finishUpdate = function_deprecated_by(finish_update)
        updateInterface = function_deprecated_by(update_interface)


class InstallProgress(DumbInstallProgress):
    """An InstallProgress that is pretty useful.

    It supports the attributes 'percent' 'status' and callbacks for the dpkg
    errors and conffiles and status changes.
    """

    def __init__(self):
        DumbInstallProgress.__init__(self)
        self.select_timeout = 0.1
        (read, write) = os.pipe()
        self.writefd = write
        self.statusfd = os.fdopen(read, "r")
        fcntl.fcntl(self.statusfd.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
        self.read = ""
        self.percent = 0.0
        self.status = ""

    def error(self, pkg, errormsg):
        """Called when a error is detected during the install."""

    def conffile(self, current, new):
        """Called when a conffile question from dpkg is detected."""

    def status_change(self, pkg, percent, status):
        """Called when the status changed."""

    def update_interface(self):
        """Called periodically to update the interface."""
        if self.statusfd is None:
            return
        try:
            while not self.read.endswith("\n"):
                self.read += os.read(self.statusfd.fileno(), 1)
        except OSError, (errno_, errstr):
            # resource temporarly unavailable is ignored
            if errno_ != errno.EAGAIN and errno_ != errno.EWOULDBLOCK:
                print errstr
        if not self.read.endswith("\n"):
            return

        s = self.read
        #print s
        try:
            (status, pkg, percent, status_str) = s.split(":", 3)
        except ValueError:
            # silently ignore lines that can't be parsed
            self.read = ""
            return
        #print "percent: %s %s" % (pkg, float(percent)/100.0)
        if status == "pmerror":
            self.error(pkg, status_str)
        elif status == "pmconffile":
            # we get a string like this:
            # 'current-conffile' 'new-conffile' useredited distedited
            match = re.match("\s*\'(.*)\'\s*\'(.*)\'.*", status_str)
            if match:
                self.conffile(match.group(1), match.group(2))
        elif status == "pmstatus":
            if float(percent) != self.percent or status_str != self.status:
                self.status_change(pkg, float(percent),
                                  status_str.strip())
                self.percent = float(percent)
                self.status = status_str.strip()
        self.read = ""

    def fork(self):
        """Fork."""
        return os.fork()

    def wait_child(self):
        """Wait for child progress to exit."""
        while True:
            select.select([self.statusfd], [], [], self.select_timeout)
            self.update_interface()
            (pid, res) = os.waitpid(self.child_pid, os.WNOHANG)
            if pid == self.child_pid:
                break
        return res

    def run(self, pm):
        """Start installing."""
        pid = self.fork()
        if pid == 0:
            # child
            res = pm.do_install(self.writefd)
            os._exit(res)
        self.child_pid = pid
        res = self.wait_child()
        return os.WEXITSTATUS(res)

    if apt_pkg._COMPAT_0_7:
        selectTimeout = AttributeDeprecatedBy('select_timeout')
        statusChange = function_deprecated_by(status_change)
        waitChild = function_deprecated_by(wait_child)
        updateInterface = function_deprecated_by(update_interface)


class CdromProgress(object):
    """Report the cdrom add progress.

    Subclass this class to implement cdrom add progress reporting.
    """

    def __init__(self):
        pass

    def update(self, text, step):
        """Called periodically to update the user interface."""

    def ask_cdrom_name(self):
        """Called to ask for the name of the cdrom."""

    def change_cdrom(self):
        """Called to ask for the cdrom to be changed."""

    if apt_pkg._COMPAT_0_7:
        askCdromName = function_deprecated_by(ask_cdrom_name)
        changeCdrom = function_deprecated_by(change_cdrom)


class DpkgInstallProgress(InstallProgress):
    """Progress handler for a local Debian package installation."""

    def run(self, debfile):
        """Start installing the given Debian package."""
        self.debfile = debfile
        self.debname = os.path.basename(debfile).split("_")[0]
        pid = self.fork()
        if pid == 0:
            # child
            res = os.system("/usr/bin/dpkg --status-fd %s -i %s" % \
                            (self.writefd, self.debfile))
            os._exit(os.WEXITSTATUS(res))
        self.child_pid = pid
        res = self.wait_child()
        return res

    def update_interface(self):
        """Process status messages from dpkg."""
        if self.statusfd is None:
            return
        while True:
            try:
                self.read += os.read(self.statusfd.fileno(), 1)
            except OSError, (errno_, errstr):
                # resource temporarly unavailable is ignored
                if errno_ != 11:
                    print errstr
                break
            if not self.read.endswith("\n"):
                continue

            statusl = self.read.split(":")
            if len(statusl) < 3:
                print "got garbage from dpkg: '%s'" % self.read
                self.read = ""
                break
            status = statusl[2].strip()
            #print status
            if status == "error":
                self.error(self.debname, status)
            elif status == "conffile-prompt":
                # we get a string like this:
                # 'current-conffile' 'new-conffile' useredited distedited
                match = re.match("\s*\'(.*)\'\s*\'(.*)\'.*", statusl[3])
                if match:
                    self.conffile(match.group(1), match.group(2))
            else:
                self.status = status
            self.read = ""

    if apt_pkg._COMPAT_0_7:
        updateInterface = function_deprecated_by(update_interface)
