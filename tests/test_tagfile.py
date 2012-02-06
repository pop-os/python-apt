#!/usr/bin/python
#
# Copyright (C) 2010 Michael Vogt <mvo@ubuntu.com>
#
# Copying and distribution of this file, with or without modification,
# are permitted in any medium without royalty provided the copyright
# notice and this notice are preserved.
"""Unit tests for verifying the correctness of apt_pkg.TagFile"""

import glob
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
        tagfilepath = os.path.join(basepath, "./data/tagfile/*")
        # test once for compressed and uncompressed
        for testfile in glob.glob(tagfilepath):
            # test once using the open() method and once using the path
            for f in [testfile, open(testfile)]:
                tagfile = apt_pkg.TagFile(f)
                for i, stanza in enumerate(tagfile):
                    pass
                self.assertEqual(i, 2)

    def test_errors(self):
        # Raises SystemError via lbiapt
        self.assertRaises(SystemError, apt_pkg.TagFile, "not-there-no-no")
        # Raises Type error
        self.assertRaises(TypeError, apt_pkg.TagFile, object())

if __name__ == "__main__":
    unittest.main()
