#!/usr/bin/env python
# -*- coding: utf-8 -*-
# auth - authentication key management
#
#  Copyright (c) 2004 Canonical
#  Copyright (c) 2012 Sebastian Heinlein
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
import os
import os.path
import subprocess
import tempfile

import apt_pkg
from apt_pkg import gettext as _


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


def _call_apt_key_script(*args, **kwargs):
    """Run the apt-key script with the given arguments."""
    conf = None
    cmd = [apt_pkg.config.find_file("Dir::Bin::Apt-Key", "/usr/bin/apt-key")]
    cmd.extend(args)
    env = os.environ.copy()
    env["LANG"] = "C"
    try:
        if apt_pkg.config.find_dir("Dir") != "/":
            # If the key is to be installed into a chroot we have to export the
            # configuration from the chroot to the apt-key script by using
            # a temporary APT_CONFIG file. The apt-key script uses apt-config
            # shell internally
            conf = tempfile.NamedTemporaryFile(prefix="apt-key", suffix=".conf")
            conf.write(apt_pkg.config.dump().encode("UTF-8"))
            conf.flush()
            env["APT_CONFIG"] = conf.name
        proc = subprocess.Popen(cmd, env=env, universal_newlines=True,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)

        content = kwargs.get("stdin", None)
        if isinstance(content, unicode):
            content = content.encode("utf-8")

        output, stderr = proc.communicate(content)

        assert stderr == None

        if proc.returncode:
            raise SystemError("The apt-key script failed with return code %s:\n"
                              "%s\n%s" % (proc.returncode, " ".join(cmd),
                                          output))
        return output.strip()
    finally:
        if conf is not None:
            conf.close()

def add_key_from_file(filename):
    """Import a GnuPG key file to trust repositores signed by it.

    Keyword arguments:
    filename -- the absolute path to the public GnuPG key file
    """
    if not os.path.abspath(filename):
        raise SystemError("An absolute path is required: %s" % filename)
    if not os.access(filename, os.R_OK):
        raise SystemError("Key file cannot be accessed: %s" % filename)
    _call_apt_key_script("add", filename)

def add_key_from_keyserver(keyid, keyserver):
    """Import a GnuPG key file to trust repositores signed by it.

    Keyword arguments:
    keyid -- the identifier of the key, e.g. 0x0EB12DSA
    keyserver -- the URL or hostname of the key server
    """
    _call_apt_key_script("adv", "--quiet", "--keyserver", keyserver,
                         "--recv", keyid)

def add_key(content):
    """Import a GnuPG key to trust repositores signed by it.

    Keyword arguments:
    content -- the content of the GnuPG public key
    """
    _call_apt_key_script("adv", "--quiet", "--batch",
                         "--import", "-", stdin=content)

def remove_key(fingerprint):
    """Remove a GnuPG key to no longer trust repositores signed by it.

    Keyword arguments:
    fingerprint -- the fingerprint identifying the key
    """
    _call_apt_key_script("rm", fingerprint)

def export_key(fingerprint):
    """Return the GnuPG key in text format.

    Keyword arguments:
    fingerprint -- the fingerprint identifying the key
    """
    return _call_apt_key_script("export", fingerprint)

def update():
    """Update the local keyring with the archive keyring and remove from
    the local keyring the archive keys which are no longer valid. The
    archive keyring is shipped in the archive-keyring package of your
    distribution, e.g. the debian-archive-keyring package in Debian.
    """
    return _call_apt_key_script("update")

def net_update():
    """Work similar to the update command above, but get the archive
    keyring from an URI instead and validate it against a master key.
    This requires an installed wget(1) and an APT build configured to
    have a server to fetch from and a master keyring to validate. APT
    in Debian does not support this command and relies on update
    instead, but Ubuntu's APT does.
    """
    return _call_apt_key_script("net-update")

def list_keys():
    """Returns a list of TrustedKey instances for each key which is
    used to trust repositories.
    """
    # The output of `apt-key list` is difficult to parse since the
    # --with-colons parameter isn't user
    output = _call_apt_key_script("adv", "--with-colons", "--batch",
                                  "--list-keys")
    res = []
    for line in output.split("\n"):
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
