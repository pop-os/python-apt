# MetaRelease.py 
#  
#  Copyright (c) 2004,2005 Canonical
#  
#  Author: Michael Vogt <michael.vogt@ubuntu.com>
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

import pygtk
pygtk.require('2.0')
import gobject
import thread
import urllib2
import os
import string
import apt_pkg
import time
import rfc822
from subprocess import Popen,PIPE

class Dist(object):
    def __init__(self, name, version, date, supported):
        self.name = name
        self.version = version
        self.date = date
        self.supported = supported
        self.releaseNotesURI = None
        self.upgradeTool = None
        self.upgradeToolSig = None

class MetaRelease(gobject.GObject):

    # some constants
    METARELEASE_URI = "http://changelogs.ubuntu.com/meta-release"
    METARELEASE_URI_UNSTABLE = "http://changelogs.ubuntu.com/meta-release-development"
    METARELEASE_FILE = "/var/lib/update-manager/meta-release"

    __gsignals__ = { 
        'new_dist_available' : (gobject.SIGNAL_RUN_LAST,
                                gobject.TYPE_NONE,
                                (gobject.TYPE_PYOBJECT,)),
        'dist_no_longer_supported' : (gobject.SIGNAL_RUN_LAST,
                                      gobject.TYPE_NONE,
                                      ())

        }

    def __init__(self, useDevelopmentRelase=False):
        gobject.GObject.__init__(self)
        if useDevelopmentRelase:
            self.METARELEASE_URI = self.METARELEASE_URI_UNSTABLE
        self.metarelease_information = None
        self.downloading = True
        # we start the download thread here and we have a timeout
        # in the gtk space to test if the download already finished
        # this is needed because gtk is not thread-safe
        t=thread.start_new_thread(self.download, ())
        gobject.timeout_add(1000,self.check)
        
    def get_dist(self):
        " return the codename of the current runing distro "
        p = Popen(["/bin/lsb_release","-c","-s"],stdout=PIPE)
        res = p.wait()
        if res != 0:
            sys.stderr.write("lsb_release returned exitcode: %i\n" % res)
        dist = string.strip(p.stdout.readline())
        #dist = "breezy"
        return dist
    
    def check(self):
        #print "check"
        # check if we have a metarelease_information file
        if self.metarelease_information != None:
            self.parse()
            # return False makes g_timeout() stop
            return False
        # no information yet, keep runing
        return True
            
    def parse(self):
        #print "parse"
        current_dist_name = self.get_dist()
        current_dist = None
        dists = []

        # parse the metarelease_information file
        index_tag = apt_pkg.ParseTagFile(self.metarelease_information)
        step_result = index_tag.Step()
        while step_result:
            if index_tag.Section.has_key("Dist"):
                name = index_tag.Section["Dist"]
                #print name
                rawdate = index_tag.Section["Date"]
                date = time.mktime(rfc822.parsedate(rawdate))
                supported = bool(index_tag.Section["Supported"])
                version = index_tag.Section["Version"]
                # add the information to a new date object
                dist = Dist(name, version, date,supported)
                if index_tag.Section.has_key("ReleaseNotes"):
                    dist.releaseNotesURI = index_tag.Section["ReleaseNotes"]
                if index_tag.Section.has_key("UpgradeTool"):
                    dist.upgradeTool =  index_tag.Section["UpgradeTool"]
                if index_tag.Section.has_key("UpgradeToolSignature"):
                    dist.upgradeToolSig =  index_tag.Section["UpgradeToolSignature"]
                dists.append(dist)
                if name == current_dist_name:
                    current_dist = dist 
            step_result = index_tag.Step()

        # first check if the current runing distro is in the meta-release
        # information. if not, we assume that we run on something not
        # supported and silently return
        if current_dist == None:
            print "current dist not found in meta-release file"
            return False

        # then see what we can upgrade to (only upgrade to supported dists)
        upgradable_to = ""
        for dist in dists:
            if dist.date > current_dist.date and dist.supported == True: 
                upgradable_to = dist
                #print "new dist: %s" % upgradable_to
                break

        # only warn if unsupported and a new dist is available (because 
        # the development version is also unsupported)
        if upgradable_to != "" and not current_dist.supported:
            self.emit("dist_no_longer_supported",upgradabl_to)
        elif upgradable_to != "":
            self.emit("new_dist_available",upgradable_to)

        # parsing done and sucessfully
        return True

    # the network thread that tries to fetch the meta-index file
    # can't touch the gui, runs as a thread
    def download(self):
        #print "download"
        lastmodified = 0
        req = urllib2.Request(self.METARELEASE_URI)
        if os.access(self.METARELEASE_FILE, os.W_OK):
            lastmodified = os.stat(self.METARELEASE_FILE).st_mtime
        if lastmodified > 0:
            req.add_header("If-Modified-Since", lastmodified)
        try:
            uri=urllib2.urlopen(req)
            f=open(self.METARELEASE_FILE,"w+")
            for line in uri.readlines():
                f.write(line)
            f.flush()
            f.seek(0,0)
            self.metarelease_information=f
            uri.close()
        except urllib2.URLError:
            if os.path.exists(self.METARELEASE_FILE):
                f=open(self.METARELEASE_FILE,"r")

# register in the gobject system, needed for older versions of pygtk,
# never ones do this automatically
gobject.type_register(MetaRelease)
