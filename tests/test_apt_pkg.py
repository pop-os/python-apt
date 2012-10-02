#!/usr/bin/env python

import sys
import unittest

import apt_pkg

data = {
        # XXX: note the trailing spaces for some of these entries!
    10 ** 1                  : "10 ",
    10 ** 2                  : "100 ",
    10 ** 3                  : "1000 ",
    10 ** 4                  : "10.0 k",
    10 ** 5                  : "100 k",
    10 ** 6                  : "1000 k",
    10 ** 7                  : "10.0 M",
    10 ** 8                  : "100 M",
    10 ** 9                  : "1000 M",
    10 ** 10                 : "10.0 G",
    10 ** 11                 : "100 G",
    10 ** 12                 : "1000 G",
    10 ** 13                 : "10.0 T",
    10 ** 14                 : "100 T",
    10 ** 15                 : "1000 T",
    10 ** 16                 : "10.0 P",
    10 ** 17                 : "100 P",
    10 ** 18                 : "1000 P",
    10 ** 19                 : "10.0 E",
    10 ** 20                 : "100 E",
    10 ** 21                 : "1000 E",
    10 ** 22                 : "10.0 Z",
    10 ** 23                 : "100.0 Z",
    10 ** 24                 : "1000 Z",
    10 ** 25                 : "10.0 Y",
    10 ** 26                 : "100 Y",
    10 ** 27                 : "1000 Y",

    # That's our limit :)
    10 ** 28                 : "10000 Y",

    0                        : "0 ",
    1                        : "1 ",
    1024                     : "1024 ",
    10240                    : "10.2 k",
    102400                   : "102 k",
    1024000                  : "1024 k",
    10240000                 : "10.2 M",
    102400000                : "102 M",
    2147483647               : "2147 M",
    2147483648               : "2147 M",
    1024000000               : "1024 M",
    10240000000              : "10.2 G",

    9                        : "9 ",
    99                       : "99 ",
    999                      : "999 ",
    9999                     : "9999 ",
    99999                    : "100.0 k",
    999999                   : "1000 k",
    9999999                  : "10000 k",
    99999999                 : "100.0 M",
    999999999                : "1000 M",
    9999999999               : "10000 M",
    99999999999              : "100.0 G",
    999999999999             : "1000 G",
    9999999999999            : "10000 G",
    99999999999999           : "100.0 T",
    999999999999999          : "1000 T",
    9999999999999999         : "10.0 P",
    99999999999999999        : "100 P",
    999999999999999999       : "1000 P",
    9999999999999999999      : "10.0 E",
    99999999999999999999     : "100 E",
    999999999999999999999    : "1000 E",
    9999999999999999999999   : "10.0 Z",
    999999999999999999999999 : "1000 Z",
}

class TestAptPkg(unittest.TestCase):
    """Test apt_pkg."""

    def setUp(self):
        pass

    def test_size_to_str(self):
        try:
            for k, v in data.items():
                size = apt_pkg.size_to_str(k)
                msg = "size_to_str(%s) returned '%s', expected '%s'" % (k, size, v)
                self.assertEqual(size, v, msg)
        except:
            self.fail(sys.exc_info())

        with self.assertRaises(TypeError):
            apt_pkg.size_to_str("hello")

        with self.assertRaises(TypeError):
            apt_pkg.size_to_str(None)

        with self.assertRaises(TypeError):
            apt_pkg.size_to_str({})

        with self.assertRaises(TypeError):
            apt_pkg.size_to_str([])

        with self.assertRaises(TypeError):
            apt_pkg.size_to_str(())


if __name__ == "__main__":
    unittest.main()
