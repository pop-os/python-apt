#!/usr/bin/python
#
# Copyright (C) 2010 Julian Andres Klode <jak@debian.org>
#
# Copying and distribution of this file, with or without modification,
# are permitted in any medium without royalty provided the copyright
# notice and this notice are preserved.
"""Unit tests for verifying the correctness of check_dep, etc in apt_pkg."""
import os
import tempfile
import unittest

from test_all import get_library_dir
import sys
sys.path.insert(0, get_library_dir())

import apt
import apt_pkg


class TestAptCache(unittest.TestCase):
    """ test the apt cache """

    def testAptCache(self):
        """cache: iterate all packages and all dependencies """
        cache = apt.Cache()
        # number is not meaningful and just need to be "big enough",
        # the important bit is the test against __len__
        self.assertTrue(len(cache) > 100)
        # go over the cache and all dependencies, just to see if
        # that is possible and does not crash
        for pkg in cache:
            if pkg.candidate:
                for or_dep in pkg.candidate.dependencies:
                    for dep in or_dep.or_dependencies:
                        self.assertTrue(dep.name)
                        self.assertTrue(isinstance(dep.relation, str))
                        self.assertTrue(dep.pre_depend in (True, False))

                # accessing record should take a reasonable time; in
                # particular, when using compressed indexes, it should not use
                # tons of seek operations
                r = pkg.candidate.record
                self.assertEqual(r['Package'], pkg.name)
                self.assert_('Version' in r)
                self.assert_(len(r['Description']) > 0)
                self.assert_(str(r).startswith('Package: %s\n' % pkg.name))

    def test_get_provided_packages(self):
        cache = apt.Cache()
        # a true virtual pkg
        l = cache.get_providing_packages("mail-transport-agent")
        self.assertTrue(len(l) > 0)
        # this is a not virtual (transitional) package provided by another 
        l = cache.get_providing_packages("scrollkeeper")
        self.assertEqual(l, [])
        # now inlcude nonvirtual packages in the search (rarian-compat
        # provides scrollkeeper)
        l = cache.get_providing_packages("scrollkeeper", 
                                         include_nonvirtual=True)
        self.assertTrue(len(l), 1)
        

    def test_dpkg_journal_dirty(self):
        # backup old value
        old_status = apt_pkg.config.find_file("Dir::State::status")
        # create tmp env
        tmpdir = tempfile.mkdtemp()
        dpkg_dir = os.path.join(tmpdir,"var","lib","dpkg")
        os.makedirs(os.path.join(dpkg_dir,"updates"))
        open(os.path.join(dpkg_dir,"status"), "w")
        apt_pkg.config.set("Dir::State::status",
                       os.path.join(dpkg_dir,"status"))
        cache = apt.Cache()
        # test empty
        self.assertFalse(cache.dpkg_journal_dirty)
        # that is ok, only [0-9] are dpkg jounral entries
        open(os.path.join(dpkg_dir,"updates","xxx"), "w")
        self.assertFalse(cache.dpkg_journal_dirty)        
        # that is a dirty journal
        open(os.path.join(dpkg_dir,"updates","000"), "w")
        self.assertTrue(cache.dpkg_journal_dirty)
        # reset config value
        apt_pkg.config.set("Dir::State::status", old_status)
        

if __name__ == "__main__":
    unittest.main()
