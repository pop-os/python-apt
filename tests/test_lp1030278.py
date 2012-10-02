#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Regression test for LP: #1030278"""

__author__  = "Barry Warsaw <barry@ubuntu.com>"

import unittest
import apt_pkg


class RegressionTestCase(unittest.TestCase):

    def test_no_overflow_error(self):
        # LP: #1030278 produces an overflow error in size_to_str() with a big
        # value under Python 3.
        self.assertEqual(apt_pkg.size_to_str(2147483648000000000000), '2147 E')


if __name__ == "__main__":
    unittest.main()

# vim: ts=4 et sts=4
