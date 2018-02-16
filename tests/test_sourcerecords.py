#!/usr/bin/python
#
# Copyright (C) 2018 Michael Vogt <mvo@ubuntu.com>
#
# Copying and distribution of this file, with or without modification,
# are permitted in any medium without royalty provided the copyright
# notice and this notice are preserved.
"""Unit tests for verifying the correctness of source records in apt_pkg."""

import sys
import unittest


from test_all import get_library_dir
libdir = get_library_dir()
if libdir:
    sys.path.insert(0, libdir)

import apt_pkg
import testcommon


if sys.version_info.major > 2:
    long = int


class TestSourceRecords(testcommon.TestCase):

    def test_source_records_smoke(self):
        src = apt_pkg.SourceRecords()
        while src.step():
            for f in src.files:
                # unpacking as a tuple works as before
                md5, size, path, type_ = f
                self.assertTrue(isinstance(md5, str))
                self.assertTrue(isinstance(size, long))
                self.assertTrue(isinstance(path, str))
                self.assertTrue(isinstance(type_, str))
                # access using getters
                self.assertTrue(isinstance(f.hashes, apt_pkg.HashStringList))
                self.assertTrue(isinstance(f.size, long))
                self.assertTrue(isinstance(f.path, str))
                self.assertTrue(isinstance(f.type, str))


if __name__ == "__main__":
    unittest.main()
