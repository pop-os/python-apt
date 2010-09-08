#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2010 Michael Vogt <mvo@ubuntu.com>
#
# Copying and distribution of this file, with or without modification,
# are permitted in any medium without royalty provided the copyright
# notice and this notice are preserved.
"""Unit tests for verifying the correctness of DebPackage in apt.debfile."""
import os
import logging
import unittest

from test_all import get_library_dir
import sys
sys.path.insert(0, get_library_dir())
import apt_pkg
import apt.debfile

class TestDebfilee(unittest.TestCase):
    """ test the apt cache """

    TEST_DEBS = [
        # conflicts with apt
        ('gdebi-test1.deb', False),
        # impossible dependency
        ('gdebi-test2.deb', False),
        #  or-group (impossible-dependency|apt)
        ('gdebi-test3.deb', True),
        # Conflicts: apt (<= 0.1)
        ('gdebi-test4.deb', True),
        # Conflicts: apt (>= 0.1)
        ('gdebi-test5.deb', False), 
        # invalid unicode  in descr
        ('gdebi-test6.deb', True),
        # provides/conflicts against "foobarbaz"
        ('gdebi-test7.deb', True),
        # provides/conflicts/replaces against "mail-transport-agent"
        # (should fails if mail-transport-agent is installed)
        ('gdebi-test8.deb', False), 
        # provides/conflicts against real pkg
        ('gdebi-test9.deb', True),
        # provides debconf-tiny and the real debconf conflicts with 
        ('gdebi-test10.deb', False),
    ]

    def setUp(self):
        apt_pkg.init_config()
        apt_pkg.config.set("APT::Architecture","i386")
        apt_pkg.config.set("Dir::State::status", 
                           "./data/test_debs/var/lib/dpkg/status")
        apt_pkg.config.set("Dir::State::lists", 
                           "./data/test_debs/var/lib/apt/lists")
        apt_pkg.config.set("Dir::Etc::sourcelist", 
                           "./data/test_debs/etc/apt/sources.list")
        apt_pkg.init_system()
        self.cache = apt.Cache()

    def testDscFile(self):
        filename = "hello_2.5-1.dsc"
        deb = apt.debfile.DscSrcPackage(cache=self.cache)
        deb.open(os.path.join("data", "test_debs", filename))
        self.assertTrue(deb.check(), "got failure '%s'" % deb._failure_string)
        missing = set(['autotools-dev'])
        self.assertEqual(set(deb.missing_deps), missing)
        filename = "impossible-build-depends_2.5-1.dsc"
        deb = apt.debfile.DscSrcPackage(cache=self.cache)
        deb.open(os.path.join("data", "test_debs", filename))
        self.assertFalse(deb.check())

    def testDebFile(self):
        deb = apt.debfile.DebPackage(cache=self.cache)
        for (filename, expected_res) in self.TEST_DEBS:
            logging.debug("testing %s, expecting %s" % (filename, expected_res))
            deb.open(os.path.join("data", "test_debs", filename))
            res = deb.check()
            self.assertEqual(res, expected_res,
                "Unexpected result for package '%s' (got %s wanted %s)\n%s" % (
                    filename, res, expected_res, deb._failure_string))

    def test_utf8_sections(self):
        deb = apt.debfile.DebPackage(cache=self.cache)
        deb.open(os.path.join("data","test_debs","utf8-package_1.0-1_all.deb"))
        self.assertEqual(deb["Maintainer"],
                         "Samuel Lidén Borell <samuel@slbdata.se>")

    def testContent(self):
        # no python-debian for python3 yet, so fail gracefully
        try:
            import debian
        except ImportError:
            return
        # normal
        deb = apt.debfile.DebPackage(cache=self.cache)
        deb.open(os.path.join("data", "test_debs", "gdebi-test11.deb"))
        self.assertEqual('#!/bin/sh\necho "test"\n',
                         deb.data_content("usr/bin/test"))
        # binary
        deb = apt.debfile.DebPackage(cache=self.cache)
        deb.open(os.path.join("data", "test_debs", "gdebi-test12.deb"))
        content = deb.data_content("usr/bin/binary")
        self.assertTrue(content.startswith("Automatically converted to printable ascii:\n\x7fELF "))
                  

if __name__ == "__main__":
    #logging.basicConfig(level=logging.DEBUG)
    unittest.main()
