#!/usr/bin/python
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

    def testDebFile(self):
        deb = apt.debfile.DebPackage()
        for (filename, expected_res) in self.TEST_DEBS:
            logging.debug("testing %s, expecting %s" % (filename, expected_res))
            deb.open(os.path.join("test_debs", filename))
            res = deb.check()
            self.assertEqual(res, expected_res)

if __name__ == "__main__":
    #logging.basicConfig(level=logging.DEBUG)
    unittest.main()
