# histoy.py - apt package abstraction
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
"""Functionality related to the apt history file."""

import apt_pkg
apt_pkg.InitConfig()

import gzip
import string

class Transaction(object):
    def __init__(self, sec):
        self.start_date = sec.has_key("Start-Date")
        for k in ["Install", "Upgrade", "Downgrade" "Remove", "Purge","Error"]:
            if sec.has_key(k):
                setattr(self, k.lower(), map(string.strip, sec[k].split(",")))
            else:
                setattr(self, k.lower(), None)

               
class AptHistory(dict):
    def __init__(self, history_file=None):
        if not history_file:
            history_file = apt_pkg.Config.FindFile("Dir::Log::History")
        # FIXME: test for .gz ending
        f = open(history_file)
        self._tagfile = apt_pkg.ParseTagFile(f)
        while self._tagfile.Step():
            sec = self._tagfile.Section
            start_date = sec['Start-Date']
            self[start_date] = Transaction(sec)

if __name__ == "__main__":
    #h = AptHistory("/var/log/apt/history.log.1.gz")
    history = AptHistory()
    for date in history:
        print "'%s' - '%s'" % (date, history[date].install)
