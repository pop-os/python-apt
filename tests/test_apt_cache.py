#!/usr/bin/python
#
# Copyright (C) 2010 Julian Andres Klode <jak@debian.org>
#               2010 Michael Vogt <mvo@ubuntu.com>
#
# Copying and distribution of this file, with or without modification,
# are permitted in any medium without royalty provided the copyright
# notice and this notice are preserved.
"""Unit tests for verifying the correctness of check_dep, etc in apt_pkg."""
import os
import tempfile
import unittest

import sys
sys.path.insert(0, "..")

import apt
import apt_pkg
import shutil

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
        self.assertTrue("postfix" in [p.name for p in l])
        # this is a not virtual (transitional) package provided by another 
        l = cache.get_providing_packages("scrollkeeper")
        self.assertEqual(l, [])
        # now inlcude nonvirtual packages in the search (rarian-compat
        # provides scrollkeeper)
        l = cache.get_providing_packages("scrollkeeper", 
                                         include_nonvirtual=True)
        self.assertTrue(len(l), 1)
        self.assertTrue("mail-transport-agent" in cache["postfix"].candidate.provides)
        

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

    def test_apt_update(self):
        try:
            os.makedirs("./data/tmp/var/lib/apt/lists/partial")
        except OSError, e:
            pass
        apt_pkg.config.set("dir::state", "./data/tmp/var/lib/apt")

        # test single sources.list fetching
        sources_list = "./data/tmp/test.list"
        f=open(sources_list,"w")
        f.write("deb http://archive.ubuntu.com/ubuntu lucid restricted\n")
        f.close()
        self.assertTrue(os.path.exists(sources_list))
        # write marker to ensure listcleaner is not run
        open("./data/tmp/var/lib/apt/lists/marker","w")

        # update a single sources.list
        cache = apt.Cache()
        cache.update(sources_list=sources_list)
        # verify we just got a single source
        files = filter(lambda f: not (f == "lock" or f == "partial"),
                       os.listdir("./data/tmp/var/lib/apt/lists"))
        self.assertTrue("archive.ubuntu.com_ubuntu_dists_lucid_Release" in files)
        # ensure the listcleaner was not run
        self.assertTrue("marker" in files)
        # ensure we don't get additional stuff from /etc/apt/sources.list
        self.assertTrue(len(files) < 5)
        
        # now run update again and verify that we got the normal sources.list
        cache.update()
        full_update = filter(lambda f: not (f == "lock" or f == "partial"),
                       os.listdir("./data/tmp/var/lib/apt/lists"))
        self.assertTrue(len(files) < len(full_update))

        # cleanup
        shutil.rmtree("./data/tmp/")

if __name__ == "__main__":
    unittest.main()
