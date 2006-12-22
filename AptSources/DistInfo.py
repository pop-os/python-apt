#!/usr/bin/env python
# DistInfo.py - simple parser for a xml-based metainfo file
#  
#  Copyright (c) 2005 Gustavo Noronha Silva
#  
#  Author: Gustavo Noronha Silva <kov@debian.org>
# 
#  This program is free software; you can redistribute it and/or 
#  modify it under the terms of the GNU General Public License as 
#  published by the Free Software Foundation; either version 2 of the
#  License, or (at your option) any later version.
# 
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
# 
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
#  USA

import os
import gettext
from os import getenv
import ConfigParser
import string

from gettext import gettext as _

class Suite:
    def __init__(self):
        self.name = None
        self.child = False
        self.match_name = None
        self.description = None
        self.base_uri = None
        self.type = None
        self.components = []
        self.children = []
        self.match_uri = None
        self.mirrors = []
        self.distribution = None
        self.available = True

    def has_component(self, comp):
        ''' Check if the distribution provides the given component '''
        return comp in map(lambda c: c.name, self.components)

class Component:
    def __init__(self, name, desc=None, short_desc=None):
        self.name = name
        self.description = desc
        self.short_description = short_desc
    def get_description(self):
        if self.description != None:
            return self.description
        elif self.short_description != None:
            return self.short_description
        else:
            return None
    def set_description(self, desc):
        self.description = desc
    def set_short_description(self, desc):
        self.short_description = desc
    def get_description(self):
        return self.description
    def get_short_description(self):
        return self.short_description

class Mirror:
    ''' Storage for mirror related information '''
    def __init__(self, hostname, proto="http", dir="/"):
        self.hostname = hostname
        self.repositories = []
        self.add_repository(proto, dir)
    def add_repository(self, proto, dir):
        self.repositories.append(Repository(proto, dir))
    def get_repositories_for_proto(self, proto):
        return filter(lambda r: r.proto == proto, self.repositories)
    def has_repository(self, proto, dir):
        return len(filter(lambda r: (r.proto == proto) and dir in r.dir, 
                          self.repositories)) > 0

class Repository:
    def __init__(self, proto, dir):
        self.proto = proto
        self.dir = dir

class DistInfo:
    def __init__(self,
                 dist = None,
                 base_dir = "/usr/share/python-aptsources/templates"):
        self.metarelease_uri = ''
        self.suites = []

        if not dist:
            pipe = os.popen("lsb_release -i -s")
            dist = pipe.read().strip()
            pipe.close()
            del pipe

        self.dist = dist

        dist_fname = "%s/%s.info" % (base_dir, dist)
        dist_file = open (dist_fname)
        if not dist_file:
            return
        suite = None
        component = None
        for line in dist_file:
            tokens = line.split (':', 1)
            if len (tokens) < 2:
                continue
            field = tokens[0].strip ()
            value = tokens[1].strip ()
            if field == 'ChangelogURI':
                self.changelogs_uri = _(value)
            elif field == 'MetaReleaseURI':
                self.metarelease_uri = value
            elif field == 'Suite':
                if suite:
                    if component and not suite.has_component(component.name):
                        suite.components.append(component)
                        component = None
                    self.suites.append (suite)
                suite = Suite ()
                suite.name = value
                suite.distribution = dist
                suite.match_name = "^%s$" % value
            elif field == 'MatchName':
                suite.match_name = value
            elif field == 'ParentSuite':
                suite.child = True
                for nanny in self.suites:
                    if nanny.name == value:
                        nanny.children.append(suite)
                        # reuse some properties of the parent suite
                        if suite.match_uri == None:
                            suite.match_uri = nanny.match_uri
                        if suite.mirrors == []:
                            suite.mirrors = nanny.mirrors
                        if suite.base_uri == None:
                            suite.base_uri = nanny.base_uri
            elif field == 'Available':
                suite.available = value
            elif field == 'RepositoryType':
                suite.type = value
            elif field == 'BaseURI':
                suite.base_uri = value
                suite.match_uri = value
            elif field == 'MatchURI':
                suite.match_uri = value
            elif field == 'MirrorsFile':
                if os.path.exists(value):
                    suite.mirrors = filter(lambda s:
                                                 ((s != "") and
                                                  (not s.startswith("#"))),
                                                 map(string.strip,
                                                     open(value)))
                else:
                    print "WARNING: can't read '%s'" % value
            elif field == 'Description':
                suite.description = _(value)
            elif field == 'Component':
                if component and not suite.has_component(component.name):
                    suite.components.append(component)
                component = Component(value)
            elif field == 'CompDescription':
                component.set_description(_(value))
            elif field == 'CompDescriptionLong':
                component.set_short_description(_(value))
        if suite:
            if component:
                suite.components["%s" % component.name] = \
                    (component.description,
                     component.description_long)
                component = None
            self.suites.append (suite)
            suite = None

if __name__ == "__main__":
    d = DistInfo ("Ubuntu", "/usr/share/python-aptsources/templates")
    print d.changelogs_uri
    for suite in d.suites:
        print "\nSuite: %s" % suite.name
        print "Desc: %s" % suite.description
        print "BaseURI: %s" % suite.base_uri
        print "MatchURI: %s" % suite.match_uri
        print "Mirrors: %s" % suite.mirrors
        for comp in suite.components:
            print " %s -%s -%s" % (comp.name, 
                                   comp.description, 
                                   comp.short_description)
        for child in suite.children:
            print "  %s" % child.description
