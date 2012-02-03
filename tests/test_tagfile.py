#!/usr/bin/python
#
# Copyright (C) 2010 Michael Vogt <mvo@ubuntu.com>
#
# Copying and distribution of this file, with or without modification,
# are permitted in any medium without royalty provided the copyright
# notice and this notice are preserved.
"""Unit tests for verifying the correctness of apt_pkg.TagFile"""

import unittest

from test_all import get_library_dir
import sys
sys.path.insert(0, get_library_dir())

import apt_pkg

class TestTagFile(unittest.TestCase):
    """ test the apt_pkg.TagFile """

    def test_tag_file(self):
        tagfile = apt_pkg.TagFile(open("./data/tagfile/history.log"))
        for i, stanza in enumerate(tagfile):
            pass
        self.assertEqual(i, 2)

    def test_tag_file_compressed(self):
        tagfile = apt_pkg.TagFile(open("./data/tagfile/history.1.log.gz"))
        for i, stanza in enumerate(tagfile):
            #print stanza
            pass
        self.assertEqual(i, 2)

if __name__ == "__main__":
    unittest.main()
