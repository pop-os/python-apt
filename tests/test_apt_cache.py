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

from test_all import get_library_dir
import sys
sys.path.insert(0, get_library_dir())

import apt
import apt_pkg
import shutil
import glob

class TestAptCache(unittest.TestCase):
    """ test the apt cache """

    def setUp(self):
        # reset any config manipulations done in the individual tests
        apt_pkg.init_config()

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
                self.assertEqual(r['Package'], pkg.shortname)
                self.assert_('Version' in r)
                self.assert_(len(r['Description']) > 0)
                self.assert_(str(r).startswith('Package: %s\n' % pkg.shortname))

    def test_get_provided_packages(self):
        cache = apt.Cache()
        # a true virtual pkg
        l = cache.get_providing_packages("mail-transport-agent")
        self.assertTrue(len(l) > 0)
        self.assertTrue("postfix" in [p.name for p in l])
        # this is a not virtual (transitional) package provided by another 
        l = cache.get_providing_packages("git-core")
        self.assertEqual(l, [])
        # now inlcude nonvirtual packages in the search (rarian-compat
        # provides scrollkeeper)
        l = cache.get_providing_packages("git-core",
                                         include_nonvirtual=True)
        self.assertEqual([p.name for p in l], ["git"])
        self.assertTrue("mail-transport-agent" in cache["postfix"].candidate.provides)

    def test_low_level_pkg_provides(self):
        # low level cache provides list of the pkg
        cache = apt_pkg.Cache()
        l = cache["mail-transport-agent"].provides_list
        # arbitrary number, just needs to be higher enough
        self.assertTrue(len(l), 5)
        for (providesname, providesver, version) in l:
            self.assertEqual(providesname, "mail-transport-agent")
            if version.parent_pkg.name == "postfix":
                break
        else:
            self.assertNotReached()
   

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
        rootdir = "./data/tmp"
        if os.path.exists(rootdir):
            shutil.rmtree(rootdir)
        try:
            os.makedirs(os.path.join(rootdir, "var/lib/apt/lists/partial"))
        except OSError:
            pass
        state_dir = os.path.join(rootdir, "var/lib/apt")
        lists_dir = os.path.join(rootdir, "var/lib/apt/lists")
        apt_pkg.config.set("dir::state", state_dir)
        # set a local sources.list that does not need the network
        base_sources = os.path.abspath(os.path.join(rootdir, "sources.list"))
        apt_pkg.config.set("dir::etc::sourcelist", base_sources)
        apt_pkg.config.set("dir::etc::sourceparts", "xxx")
        # main sources.list
        sources_list = base_sources
        f=open(sources_list, "w")
        repo = os.path.abspath("./data/test-repo2")
        f.write("deb copy:%s /\n" % repo)
        f.close()

        # test single sources.list fetching
        sources_list = os.path.join(rootdir, "test.list")
        f=open(sources_list, "w")
        repo_dir = os.path.abspath("./data/test-repo")
        f.write("deb copy:%s /\n" % repo_dir)
        f.close()
        self.assertTrue(os.path.exists(sources_list))
        # write marker to ensure listcleaner is not run
        open("./data/tmp/var/lib/apt/lists/marker", "w")

        # update a single sources.list
        cache = apt.Cache()
        cache.update(sources_list=sources_list)
        # verify we just got the excpected package file 
        needle_packages = glob.glob(
            lists_dir+"/*tests_data_test-repo_Packages*")
        self.assertEqual(len(needle_packages), 1)
        # verify that we *only* got the Packages file from a single source
        all_packages = glob.glob(lists_dir+"/*_Packages*")
        self.assertEqual(needle_packages, all_packages)
        # verify that the listcleaner was not run and the marker file is
        # still there
        self.assertTrue("marker" in os.listdir(lists_dir))
        
        # now run update again (without the "normal" sources.list that
        # contains test-repo2 and verify that we got the normal sources.list
        cache.update()
        needle_packages = glob.glob(lists_dir+"/*tests_data_test-repo2_Packages*")
        self.assertEqual(len(needle_packages), 1)
        all_packages = glob.glob(lists_dir+"/*_Packages*")
        self.assertEqual(needle_packages, all_packages)

        # and another update with a single source only
        cache = apt.Cache()
        cache.update(sources_list=sources_list)
        all_packages = glob.glob(lists_dir+"/*_Packages*")
        self.assertEqual(len(all_packages), 2)

if __name__ == "__main__":
    unittest.main()
