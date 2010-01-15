#!/usr/bin/python
# Copyright (C) 2009 Julian Andres Klode <jak@debian.org>
#
# Copying and distribution of this file, with or without modification,
# are permitted in any medium without royalty provided the copyright
# notice and this notice are preserved.
"""Run all available unit tests."""
import os
import unittest

if __name__ == '__main__':
    os.chdir(os.path.dirname(__file__))
    for path in os.listdir('.'):
        if path.endswith('.py') and os.path.isfile(path):
            exec('from %s import *' % path[:-3])

    unittest.main()
