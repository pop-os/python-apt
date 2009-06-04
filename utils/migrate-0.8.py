#!/usr/bin/python2.6
#
# migrate-0.8.py - Find use of deprecated methods/attributes in the code.
#
# Copyright (C) 2009 Julian Andres Klode <jak@debian.org>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA
"""migrate-0.8.py - Find all occurences of funcs./attrs. deprecated in 0.8.

Usage: python2.6 migrate-0.8.py [options] <file/directory>...

This reads the list of all functions and attributes available only in
COMPAT_0_7 builds and checks for occurences in the given Python modules. Has
to be run from the python-apt source code directory.

Requires python2.6 to be installed.

Parameters:
    -h  Display this help
    -c  Colorize the matching parts in the output.
"""
import _ast
import ast
import glob
import linecache
import os
import re
import sys
import types
from collections import defaultdict
from textwrap import fill

color=False
if sys.argv[1] in ('-c', '--color', '--colour'):
    color=True
    del sys.argv[1]

if '-h' in sys.argv or '--help' in sys.argv or not sys.argv[1:]:
    print __doc__.strip()
    sys.exit(0)

if os.path.dirname(__file__).endswith('utils'):
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def do_color(string, words):
    """Colorize (red) the given words in the given string."""
    if not color:
        return string
    for word in words:
        word = re.escape(word)
        string = re.sub('([^_]*)(%s)([^_]*)' % word, "\\1\033[31m\033[1m" +
                        r"\2" + "\033[0m\\3", string)
    return string


def find_deprecated_cpp():
    """Find all the deprecated functions and attributes."""
    is_open=False
    all_old = set()
    for fname in glob.glob('python/*.cc'):
        lines = list(open(fname, 'r'))
        while lines:
            line = lines.pop(0)
            while lines and not ('static PyMethodDef' in line or
                                 'static PyGetSetDef' in line):
                line = lines.pop(0)
            if not lines:
                break

            while lines and not ';' in line:
                while lines and not 'COMPAT_0_7' in line:
                    line = lines.pop(0)
                if lines:
                    line = lines.pop(0)
                while lines and not '#endif' in line:
                    name = line.split(",")[0].strip().strip('{"')
                    if not 'module' in fname:
                        name = '.' + name
                    else:
                        all_old.add('.' + name)
                    all_old.add(name)
                    line = lines.pop(0)
    # Let's handle constants in the apt_pkg module
    lines = list(open('python/apt_pkgmodule.cc'))
    while lines:
        while lines and not 'COMPAT_0_7' in line:
            line = lines.pop(0)
        if lines:
            lines.pop(0)
        while lines and not '#endif' in line:
            if 'PyModule_Add' in line:
                name = line.split(",")[1].strip().strip('"')
                if name != '_COMPAT_0_7':
                    all_old.add('.' + name)
                    all_old.add(name)
            line = lines.pop(0)
    return all_old


def find_deprecated_py():
    """Same as find_deprecated_cpp(), but for apt and aptsources.

    We import apt_pkg, set _COMPAT_0_7 to 0, import apt and aptsources and
    create a list of all attributes.

    No we remove the imported modules, reimport them (with _COMPAT_0_7=1),
    and see which functions have been removed.
    """

    modules = ('apt', 'apt.package', 'apt.cdrom', 'apt.cache', 'apt.debfile',
               'apt.progress', 'aptsources.distinfo', 'aptsources.distro',
               'aptsources.sourceslist')

    import apt_pkg
    apt_pkg._COMPAT_0_7 = 0

    empty = set(sys.modules)
    new, deprecated = set(), set()

    for mname in sorted(modules):
        module = __import__(mname, fromlist=['*'])

        for clsname in dir(module):
            cls = getattr(module, clsname)
            if not isinstance(cls, types.TypeType):
                new.add(clsname)
                continue
            # Attributes/Methods
            new.update(clsname + '.' + name for name in dir(cls))

    for mname in sys.modules.keys():
        if not mname in empty:
            del sys.modules[mname]

    apt_pkg._COMPAT_0_7 = 1

    for mname in sorted(modules):
        module = __import__(mname, fromlist=['*'])
        for clsname in dir(module):
            cls = getattr(module, clsname)
            if not isinstance(cls, types.TypeType):
                deprecated.add(clsname)
                continue
            for name in dir(cls):
                if not clsname + '.' + name in new:
                    # Attributes/Methods, which are deprecated (not in new).
                    deprecated.add('.' + name)

    for mname in sys.modules.keys():
        if not mname in empty:
            del sys.modules[mname]

    return deprecated.difference(new)


def find_occurences(all_old, files):
    """Find all ocurrences in the given Python files."""
    for fname in files:
        if fname.endswith('setup3.py') or not fname.endswith('.py'):
            continue

        words = defaultdict(lambda: set())
        for i in ast.walk(ast.parse(open(fname).read())):
            if isinstance(i, _ast.ImportFrom):
                for alias in i.names:
                    if alias.name in all_old:
                        words[i.lineno].add(alias.name)
            if isinstance(i, _ast.Name) and i.id in all_old:
                words[i.lineno].add(i.id)

            if isinstance(i, _ast.Attribute) and ('.' + i.attr in all_old):
                words[i.lineno].add(i.attr)

        for lineno in sorted(words):
            line = do_color(linecache.getline(fname, lineno).rstrip('\n'),
                            words[lineno])
            print '%s:%s:%s' % (fname, lineno, line)

# Now, let's find them in the code.

print __doc__.split("\n")[0]
print
print fill('Information: Please verify that the results are correct before '
           'you modify any code, because there may be false positives.', 79)
print
if color:
    print fill('Information: The color is not always correct, because we '
               'simply highlight the matched words (like grep).', 79)
    print

all_old = find_deprecated_cpp()

if not '-P' in sys.argv:
    all_old |= find_deprecated_py()
else:
    sys.argv.remove('-P')

files = set()
for path in sys.argv[1:]:
    if not os.path.exists(path):
        raise ValueError('Path does not exist: %s' % path)
    if os.path.isfile(path):
        files.add(path)
    else:
        for root, dirs, files_ in os.walk(path):
            for fname in files_:
                files.add(os.path.normpath(os.path.join(root, fname)))

find_occurences(all_old, sorted(files))
