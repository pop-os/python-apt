#!/usr/bin/python
#
# Copyright (C) 2012 Michael Vogt <mvo@ubuntu.com>
#
# Copying and distribution of this file, with or without modification,
# are permitted in any medium without royalty provided the copyright
# notice and this notice are preserved.

import apt
import unittest

class TestAptPolicy(unittest.TestCase):

    def test_apt_policy(self):
        # get a policy
        cache = apt.Cache()
        policy = cache._depcache.policy
        self.assertNotEqual(policy, None)
        # basic tests
        pkg = cache["apt"]
        self.assertEqual(policy.get_priority(pkg._pkg), 0)
        # get verfile
        ver = pkg.candidate._cand
        verfile_list = ver.file_list
        for verfile in verfile_list:
            print verfile
            self.assertEqual(policy.get_priority(verfile), 500)


if __name__ == "__main__":
    unittest.main()
