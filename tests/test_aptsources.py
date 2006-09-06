#!/usr/bin/env python

import UpdateManager.Common.aptsources as aptsources
import unittest
import apt_pkg
import os
import copy

class TestAptSources(unittest.TestCase):
    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)
        apt_pkg.init()
        
    def testAddComponent(self):
        pass

    def testIsMirror(self):
        self.assertTrue(aptsources.is_mirror("http://archive.ubuntu.com",
                                              "http://de.archive.ubuntu.com"))
        self.assertFalse(aptsources.is_mirror("http://archive.ubuntu.com",
                                              "http://ftp.debian.org"))

    def testSourcesListReading(self):
        sources = aptsources.SourcesList()
        # test refresh
        apt_pkg.Config.Set("Dir::Etc", os.getcwd())
        apt_pkg.Config.Set("Dir::Etc::sourcelist","data/sources.list")
        apt_pkg.Config.Set("Dir::Etc::sourceparts",".")
        sources.refresh()
        self.assertEqual(len(sources.list), 6)
        # test load
        sources.list = []
        sources.load("data/sources.list")
        self.assertEqual(len(sources.list), 6)
        # test to add something that is already there (main)
        before = copy.deepcopy(sources)
        sources.add("deb","http://de.archive.ubuntu.com/ubuntu/",
                    "edgy",
                    ["main"])
        self.assertTrue(sources.list == before.list)
        # test to add something that is already there (restricted)
        before = copy.deepcopy(sources)
        sources.add("deb","http://de.archive.ubuntu.com/ubuntu/",
                    "edgy",
                    ["restricted"])
        self.assertTrue(sources.list == before.list)
        # test to add something new: multiverse
        sources.add("deb","http://de.archive.ubuntu.com/ubuntu/",
                    "edgy",
                    ["multiverse"])
        found = False
        for entry in sources:
            if (entry.type == "deb" and
                entry.uri == "http://de.archive.ubuntu.com/ubuntu/" and
                entry.dist == "edgy" and
                "multiverse" in entry.comps):
                found = True
        self.assertTrue(found)
        # test to add something new: multiverse *and* 
        # something that is already there
        before = copy.deepcopy(sources)
        sources.add("deb","http://de.archive.ubuntu.com/ubuntu/",
                    "edgy",
                    ["universe", "something"])
        found_universe = 0
        found_something = 0
        for entry in sources:
            if (entry.type == "deb" and
                entry.uri == "http://de.archive.ubuntu.com/ubuntu/" and
                entry.dist == "edgy"):
                for c in entry.comps:
                    print c
                    if c == "universe":
                        found_universe += 1
                    if c == "something":
                        found_something += 1
        #print "\n".join([s.str() for s in sources])
        self.assertEqual(found_something, 1)
        self.assertEqual(found_universe, 1)

        
        

if __name__ == "__main__":
    unittest.main()
