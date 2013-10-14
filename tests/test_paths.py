#
# Test that both unicode and bytes path names work
#
import unittest

import apt_pkg


class TestPath(unittest.TestCase):

    def setUp(self):
        apt_pkg.init()

    def test_index_records(self):
        index = apt_pkg.IndexRecords()
        index.load(u"./data/misc/foo_Release")
        index.load(b"./data/misc/foo_Release")

        hash1, size1 = index.lookup(u"main/i18n/Index")
        hash2, size2 = index.lookup(b"main/i18n/Index")

        self.assertEqual(size1, size2)
        self.assertEqual(str(hash1), str(hash2))
        self.assertEqual(str(hash1), ("SHA256:fefed230e286d832ab6eb0fb7b72"
                                      + "442165b50df23a68402ae6e9d265a31920a2"))


if __name__ == '__main__':
    unittest.main()
