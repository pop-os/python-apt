#!/usr/bin/python
#
# Copyright (C) 2010 Michael Vogt <mvo@ubuntu.com>
#
# Copying and distribution of this file, with or without modification,
# are permitted in any medium without royalty provided the copyright
# notice and this notice are preserved.
"""Unit tests for verifying the correctness of apt_pkg.TagFile"""

import os
import unittest

from test_all import get_library_dir
import sys
sys.path.insert(0, get_library_dir())

import apt_pkg

class TestTagFile(unittest.TestCase):
    """ test the apt_pkg.TagFile """

    def test_tag_file(self):
        basepath = os.path.dirname(__file__)
        tagfilepath = os.path.join(
            basepath, "./data/tagfile/history.log")
        tagfile = apt_pkg.TagFile(open(tagfilepath))
        for i, stanza in enumerate(tagfile):
            pass
        self.assertEqual(i, 2)

    def test_tag_file_compressed(self):
        basepath = os.path.dirname(__file__)
        tagfilepath = os.path.join(
            basepath, "./data/tagfile/history.1.log.gz")
        tagfile = apt_pkg.TagFile(open(tagfilepath))
        for i, stanza in enumerate(tagfile):
            #print stanza
            pass
        self.assertEqual(i, 2)

if __name__ == "__main__":
    unittest.main()
