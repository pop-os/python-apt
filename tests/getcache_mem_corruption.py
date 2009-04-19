#!/usr/bin/python
import apt
import apt_pkg
import re

import unittest

class TestGetCache(unittest.TestCase):

    def setUp(self):
        apt_pkg.InitConfig()
        apt_pkg.InitSystem()

    def testWrongInvocation(self):
        # wrongly invoke GetCache() rather than GetDepCache()
        apt_cache = apt_pkg.Cache()
        self.assertRaises(ValueError, apt_pkg.Cache, apt_cache)

    def testProperInvocation(self):
        apt_cache = apt_pkg.Cache(apt.progress.OpTextProgress())
        apt_depcache = apt_pkg.DepCache(apt_cache)

if __name__ == "__main__":
    unittest.main()
