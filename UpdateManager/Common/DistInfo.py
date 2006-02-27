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

_ = gettext.gettext

class Suite:
    name = None
    description = None
    base_uri = None
    repository_type = None
    components = None

class Component:
    name = None
    description = None
    enabled = None

class DistInfo:
    def __init__(self,
                 dist = None,
                 base_dir = "/usr/share/update-manager/dists"):
        self.metarelease_uri = ''
        self.suites = []

        if not dist:
            pipe = os.popen("lsb_release -i | cut -d : -f 2-")
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
                    if component:
                        suite.components.append (component)
                        component = None
                    self.suites.append (suite)
                suite = Suite ()
                suite.name = value
                suite.components = []
            elif field == 'RepositoryType':
                suite.repository_type = value
            elif field == 'BaseURI':
                suite.base_uri = value
            elif field == 'Description':
                suite.description = _(value)
            elif field == 'Component':
                if component:
                    suite.components.append (component)
                component = Component ()
                component.name = value
            elif field == 'Enabled':
                component.enabled = bool(int(value))
            elif field == 'CompDescription':
                component.description = _(value)
        if suite:
            if component:
                suite.components.append (component)
                component = None
            self.suites.append (suite)
            suite = None


if __name__ == "__main__":
    d = DistInfo ("Debian", "../../channels")
    print d.changelogs_uri
    for suite in d.suites:
        print suite.name
        print suite.description
        print suite.base_uri
        for component in suite.components:
            print component.name
            print component.description
            print component.enabled
