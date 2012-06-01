#!/usr/bin/env python
# -*- coding: utf-8 -*-
# auth - authentication key management
#
#  Copyright (c) 2004 Canonical
#
#  Author: Michael Vogt <mvo@debian.org>
#          Sebastian Heinlein <devel@glatzor.de>
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
"""Handle GnuPG keys used to trust signed repositories."""

import atexit
import glob
import os
import os.path
import shutil
import subprocess
import tempfile

import apt_pkg
from apt_pkg import gettext as _

# Create a temporary dir to store secret keying and trust database.
# APT doesn't use a secrect key ring but GnuPG fails without it.
_TMPDIR = tempfile.mkdtemp()
atexit.register(shutil.rmtree, _TMPDIR)


class TrustedKey(object):

    """Represents a trusted key."""

    def __init__(self, name, keyid, date):
        self.raw_name = name
        # Allow to translated some known keys
        self.name = _(name)
        self.keyid = keyid
        self.date = date

    def __str__(self):
        return "%s\n%s %s" % (self.name, self.keyid, self.date)


def _get_gpg_command(keyring=None):
    """Return the gpg command"""
    cmd = [apt_pkg.config.find_file("Dir::Bin::Gpg", "/usr/bin/gpg"),
           "--ignore-time-conflict",
           "--no-default-keyring",
           "--no-options",
           "--secret-keyring", os.path.join(_TMPDIR, "secring.gpg")]
    if keyring is None:
        # Add the public keyring
        cmd.extend(["--keyring",
                    apt_pkg.config.find_file("Dir::Etc::Trusted"),
                    "--primary-keyring",
                    apt_pkg.config.find_file("Dir::Etc::Trusted")])
        # Add the public keyring parts
        trusted_parts_dir = apt_pkg.config.find_dir("Dir::Etc::TrustedParts")
        for part_name in glob.glob(os.path.join(trusted_parts_dir, "*.gpg")):
            part_path = os.path.join(trusted_parts_dir, part_name)
            if os.access(part_path, os.R_OK):
                cmd.extend(["--keyring", part_path])
        # TrustDB
        trustdb_path = os.path.join(apt_pkg.config.find_dir("Dir::Etc"),
                                    "trustdb.gpg")
        cmd.extend(["--trustdb-name", trustdb_path])
    else:
        cmd.extend(["--keyring", os.path.abspath(keyring),
                    "--primary-keyring", os.path.abspath(keyring),
                    "--trustdb-name", os.path.join(_TMPDIR, "trustdb.gpg")])
    return cmd

def _wait_and_raise(proc):
    """Wait until the given subprocess is completed and raise a
    SystemError if it failed.
    """
    if proc.wait() != 0:
        output = proc.stdout.read()
        raise SystemError("GnuPG command failed: %s" % output)

def add_key_from_file(filename, wait=True):
    """Import a GnuPG key file to trust repositores signed by it.

    Keyword arguments:
    filename -- the absolute path to the public GnuPG key file
    wait -- if the system should be blocked until the internal GnuPG call is
            completed. Otherwise the subprocess.Popen() instance will be
            returned. By default the call will be blocking.
    """
    if not os.path.abspath(filename):
        raise SystemError("An absolute path is required: %s" % filename)
    if not os.access(filename, os.R_OK):
        raise SystemError("Key file cannot be accessed: %s" % filename)
    cmd = _get_gpg_command()
    cmd.extend(["--quiet", "--batch", "--import", filename])
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            universal_newlines=True)
    if wait:
        _wait_and_raise(proc)
    else:
        return proc

def add_key_from_keyserver(keyid, keyserver, wait=True):
    """Import a GnuPG key file to trust repositores signed by it.

    Keyword arguments:
    keyid -- the identifier of the key, e.g. 0x0EB12DSA
    keyserver -- the URL or hostname of the key server
    wait -- if the system should be blocked until the internal GnuPG call is
            completed. Otherwise the subprocess.Popen() instance will be
            returned. By default the call will be blocking.
    """
    cmd = _get_gpg_command()
    cmd.extend(["--quiet", "--batch",
                "--keyserver", keyserver,
                "--recv", keyid])
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            universal_newlines=True)
    if wait:
        _wait_and_raise(proc)
    else:
        return proc

def add_key(content, wait=True):
    """Import a GnuPG key to trust repositores signed by it.

    Keyword arguments:
    content -- the content of the GnuPG public key
    wait -- if the system should be blocked until the internal GnuPG call is
            completed. Otherwise the subprocess.Popen() instance will be
            returned. By default the call will be blocking.
    """
    cmd = _get_gpg_command()
    cmd.extend(["--quiet", "--batch", "--import", "-"])
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            universal_newlines=True)
    proc.stdin.write(content)
    proc.stdin.close()
    if wait:
        _wait_and_raise(proc)
    else:
        return proc

def remove_key(fingerprint, wait=True):
    """Remove a GnuPG key to no longer trust repositores signed by it.

    Keyword arguments:
    fingerprint -- the fingerprint identifying the key
    wait -- if the system should be blocked until the internal GnuPG is
            completed. Otherwise the subprocess.Popen() instance will be
            returned. By default the call will be blocking.
    """
    cmd = _get_gpg_command()
    cmd.extend(["--quiet", "--batch", "--delete-key", "--yes", fingerprint])
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            universal_newlines=True)
    if wait:
        _wait_and_raise(proc)
    else:
        return proc

def export_key(fingerprint, wait=True):
    """Return the GnuPG key in text format.

    Keyword arguments:
    fingerprint -- the fingerprint identifying the key
    wait -- if the system should be blocked until the internal GnuPG is
            completed. Otherwise the subprocess.Popen() instance will be
            returned. By default the call will be blocking.
    """
    cmd = _get_gpg_command()
    cmd.extend(["--armor", "--export", fingerprint])
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            universal_newlines=True)
    if wait:
        _wait_and_raise(proc)
        return proc.stdout.read().strip()
    else:
        return proc

def list_keys():
    """Returns a list of TrustedKey instances for each key which is
    used to trust repositories.
    """
    cmd = _get_gpg_command()
    cmd.extend(["--with-colons", "--batch", "--list-keys"])
    res = []
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            universal_newlines=True)
    _wait_and_raise(proc)
    for line in proc.stdout.readlines():
        fields = line.split(":")
        if fields[0] == "pub":
            key = TrustedKey(fields[9], fields[4][-8:], fields[5])
            res.append(key)
    return res

if __name__ == "__main__":
    # Add some known keys we would like to see translated so that they get
    # picked up by gettext
    lambda: _("Ubuntu Archive Automatic Signing Key <ftpmaster@ubuntu.com>")
    lambda: _("Ubuntu CD Image Automatic Signing Key <cdimage@ubuntu.com>")

    apt_pkg.init()
    for trusted_key in list_keys():
        print(trusted_key)
