#!/usr/bin/python
import unittest

import apt_pkg


class TestCache(unittest.TestCase):
    """Test invocation of apt_pkg.Cache()"""

    def setUp(self):
        apt_pkg.init_config()
        apt_pkg.init_system()

    def test_wrong_invocation(self):
        """cache_invocation: Test wrong invocation."""
        apt_cache = apt_pkg.Cache(apt_pkg.OpProgress())
        if apt_pkg._COMPAT_0_7:
            self.assertRaises(ValueError, apt_pkg.Cache, apt_cache)
            self.assertRaises(ValueError, apt_pkg.Cache,
                              apt_pkg.AcquireProgress())
            self.assertRaises(ValueError, apt_pkg.Cache, 0)
        else:
            self.assertRaises(TypeError, apt_pkg.Cache, apt_cache)
            self.assertRaises(TypeError, apt_pkg.Cache,
                              apt_pkg.AcquireProgress())
            self.assertRaises(TypeError, apt_pkg.Cache, 0)

    def test_proper_invocation(self):
        """cache_invocation: Test correct invocation."""
        apt_cache = apt_pkg.Cache(apt_pkg.OpProgress())
        apt_depcache = apt_pkg.DepCache(apt_cache)

if __name__ == "__main__":
    unittest.main()
