# aptsource.py.in - parse sources.list
#  
#  Copyright (c) 2004,2005 Canonical
#                2004 Michiel Sikkes
#  
#  Author: Michiel Sikkes <michiel@eyesopened.nl>
#          Michael Vogt <mvo@debian.org>
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
 
import string
import gettext
import re
import apt_pkg
import glob
import shutil
import time
import os.path

from UpdateManager.Common.DistInfo import DistInfo

# actual source.list entries
class SourceEntry:

  def __init__(self, line,file=None):
    self.invalid = False
    self.disabled = False
    self.type = ""
    self.uri = ""
    self.dist = ""
    self.comps = []
    self.comment = ""
    self.line = line
    if file == None:
      file = apt_pkg.Config.FindDir("Dir::Etc")+apt_pkg.Config.Find("Dir::Etc::sourcelist")
    self.file = file
    self.parse(line)

  # works mostely like split but takes [] into account
  def mysplit(self, line):
    line = string.strip(line)
    pieces = []
    tmp = ""
    # we are inside a [..] block
    p_found = False
    space_found = False
    for i in range(len(line)):
      if line[i] == "[":
        p_found=True
        tmp += line[i]
      elif line[i] == "]":
        p_found=False
        tmp += line[i]
      elif space_found and not line[i].isspace(): # we skip one or more space
        space_found = False
        pieces.append(tmp)
        tmp = line[i]
      elif line[i].isspace() and not p_found:     # found a whitespace
        space_found = True
      else:
        tmp += line[i]
    # append last piece
    if len(tmp) > 0:
      pieces.append(tmp)
    return pieces


  # parse a given source line and split it into the fields we need
  def parse(self,line):
    line  = string.strip(self.line)
    #print line
    # check if the source is enabled/disabled
    if line == "" or line == "#": # empty line
      self.invalid = True
      return
    if line[0] == "#":
      self.disabled = True
      pieces = string.split(line[1:])
      # if it looks not like a disabled deb line return 
      if not (pieces[0] == "deb" or pieces[0] == "deb-src"):
        self.invalid = True
        return
      else:
        line = line[1:]
    # check for another "#" in the line (this is treated as a comment)
    i = line.find("#")
    if i > 0:
      self.comment = line[i+1:]
      line = line[:i]
    # source is ok, split it and see what we have
    pieces = self.mysplit(line)
    # Type, deb or deb-src
    self.type = string.strip(pieces[0])
    # URI
    self.uri = string.strip(pieces[1])
    # distro and components (optional)
    # Directory or distro
    self.dist = string.strip(pieces[2])
    if len(pieces) > 3:
      # List of components
      self.comps = pieces[3:]
    else:
      self.comps = []

    #print self.__dict__


  # set enabled/disabled
  def set_enabled(self, new_value):
    self.disabled = not new_value
    # enable, remove all "#" from the start of the line
    if new_value == True:
      i=0
      self.line = string.lstrip(self.line)
      while self.line[i] == "#":
        i += 1
      self.line = self.line[i:]
    else:
      # disabled, add a "#" 
      if string.strip(self.line)[0] != "#":
        self.line = "#" + self.line

  def str(self):
    """ return the current line as string """
    if self.invalid:
      return self.line
    line = ""
    if self.disabled:
      line = "# "
    line += "%s %s %s" % (self.type, self.uri, self.dist)
    if len(self.comps) > 0:
      line += " " + " ".join(self.comps)
    if self.comment != "":
      line += " #"+self.comment
    line += "\n"
    return line
    
def uniq(s):
  """ simple (and not efficient) way to return uniq list """
  u = []
  for x in s:
    if x not in u:
      u.append(x)
  return u 
  

# the SourceList file as a class
class SourcesList:
  def __init__(self):
    self.list = []      # of Type SourceEntries
    self.refresh()

  def refresh(self):
    self.list = []
    # read sources.list
    dir = apt_pkg.Config.FindDir("Dir::Etc")
    file = apt_pkg.Config.Find("Dir::Etc::sourcelist")
    self.load(dir+file)
    # read sources.list.d
    partsdir = apt_pkg.Config.FindDir("Dir::Etc::sourceparts")
    for file in glob.glob("%s/*.list" % partsdir):
      self.load(file)

  def __iter__(self):
    for entry in self.list:
      yield entry
    raise StopIteration

  def is_mirror(self, master_uri, compare_uri):
    """check if the given add_url is idential or a mirror of orig_uri
       e.g. master_uri = archive.ubuntu.com
            compare_uri = de.archive.ubuntu.com
            -> True
    """
    # remove traling spaces and "/"
    compare_uri = compare_uri.rstrip("/ ")
    master_uri = master_uri.rstrip("/ ")
    # uri is identical
    if compare_uri == master_uri:
      #print "Identical"
      return True
    # add uri is a master site and orig_uri has the from "XX.mastersite"
    # (e.g. de.archive.ubuntu.com)
    try:
      compare_srv = compare_uri.split("//")[1]
      master_srv = master_uri.split("//")[1]
      #print "%s == %s " % (add_srv, orig_srv)
    except IndexError: # ok, somethings wrong here
      #print "IndexError"
      return False
    # remove the leading "<country>." and see if that helps
    if compare_srv[compare_srv.index(".")+1:] == master_srv:
      #print "Mirror"
      return True
    return False

  def add(self, type, uri, dist, comps, comment="", pos=-1):
    # if there is a repo with the same (type, uri, dist) just add the
    # components
    for i in self.list:
      if i.type == type and self.is_mirror(uri,i.uri) and i.dist == dist:
        comps = uniq(i.comps + comps)
        # set to the old position and preserve comment
        comment = i.comment
        pos = self.list.index(i)
        self.list.remove(i)
    line = "%s %s %s" % (type,uri,dist)
    for c in comps:
      line = line + " " + c;
    if comment != "":
      line = "%s #%s\n" %(line,comment)
    line = line + "\n"
    self.list.insert(pos, SourceEntry(line))

  def remove(self, source_entry):
    self.list.remove(source_entry)

  def restoreBackup(self, backup_ext):
    " restore sources.list files based on the backup extension "
    dir = apt_pkg.Config.FindDir("Dir::Etc")
    file = apt_pkg.Config.Find("Dir::Etc::sourcelist")
    if os.path.exists(dir+file+backup_ext):
      shutil.copy(dir+file+backup_ext,dir+file)
    # now sources.list.d
    partsdir = apt_pkg.Config.FindDir("Dir::Etc::sourceparts")
    for file in glob.glob("%s/*.list" % partsdir):
      if os.path.exists(file+backup_ext):
        shutil.copy(file+backup_ext,file)

  def backup(self, backup_ext=None):
    """ make a backup of the current source files, if no backup extension
        is given, the current date/time is used (and returned) """
    already_backuped = set()
    if backup_ext == None:
      backup_ext = time.strftime("%y%m%d.%H%M")
    for source in self.list:
      if not source.file in already_backuped:
        shutil.copy(source.file,"%s%s" % (source.file,backup_ext))
    return backup_ext

  def load(self,file):
    """ (re)load the current sources """
    f = open(file, "r")
    lines = f.readlines()
    for line in lines:
      source = SourceEntry(line,file)
      self.list.append(source)
    f.close()

  def save(self):
    """ save the current sources """
    files = {}
    for source in self.list:
      if not files.has_key(source.file):
        files[source.file]=open(source.file,"w")
      files[source.file].write(source.str())
    for f in files:
      files[f].close()

# templates for the add dialog
class SourceEntryTemplate(SourceEntry):
  def __init__(self,a_type,uri,dist,description,comps):
    self.comps = []
    self.comps_descriptions = []
    self.type = a_type
    self.uri = uri
    self.dist = dist
    self.description = description
    self.comps = comps

class SourceCompTemplate:
  def __init__(self, name, description, on_by_default):
    self.name = name
    self.description = description
    self.on_by_default = on_by_default

class SourceEntryTemplates:
  def __init__(self,datadir):
    _ = gettext.gettext
    self.templates = []

    dinfo = DistInfo (base_dir=datadir+"channels/")

    for suite in dinfo.suites:
      comps = []
      for comp in suite.components:
        comps.append(SourceCompTemplate(comp.name, _(comp.description),
                                        comp.enabled))
      self.templates.append (SourceEntryTemplate(suite.repository_type,
                                                 suite.base_uri,
                                                 suite.name,
                                                 suite.description,
                                                 comps))

# matcher class to make a source entry look nice
# lots of predefined matchers to make it i18n/gettext friendly
class SourceEntryMatcher:
  class MatchType:
    def __init__(self, a_type,a_descr):
      self.type = a_type
      self.description = a_descr
  
  class MatchDist:
    def __init__(self,a_uri,a_dist, a_descr,l_comps, l_comps_descr):
      self.uri = a_uri
      self.dist = a_dist
      self.description = a_descr
      self.comps = l_comps
      self.comps_descriptions = l_comps_descr

  def __init__(self):
    _ = gettext.gettext
    self.type_list = []
    self.type_list.append(self.MatchType("^deb$",_("Binary")))
    self.type_list.append(self.MatchType("^deb-src$",_("Source")))

    self.dist_list = []

    ubuntu_comps = ["^main$","^restricted$","^universe$","^multiverse$"]
    ubuntu_comps_descr = [_("Officially supported"),
                          _("Restricted copyright"),
                          _("Community maintained (Universe)"),
                          _("Non-free (Multiverse)")]
    # CDs
    self.dist_list.append(self.MatchDist("cdrom:\[Ubuntu.*5.10",
                                         ".*",
                                        _("CD disk with Ubuntu 5.10 \"Breezy Badger\""),
                                         ubuntu_comps, ubuntu_comps_descr))
    self.dist_list.append(self.MatchDist("cdrom:\[Ubuntu.*5.04",
                                         ".*",
                                        _("CD disk with Ubuntu 5.04 \"Hoary Hedgehog\""),
                                         ubuntu_comps, ubuntu_comps_descr))
    self.dist_list.append(self.MatchDist("cdrom:\[Ubuntu.*4.10",
                                         ".*",
                                        _("CD disk with Ubuntu 4.10 \"Warty Warthog\""),
                                         ubuntu_comps, ubuntu_comps_descr))
    # URIs
    # Warty
    self.dist_list.append(self.MatchDist(".*archive.ubuntu.com/ubuntu",
                                         "^warty$",
                                         "Ubuntu 4.10 \"Warty Warthog\"",
                                         ubuntu_comps, ubuntu_comps_descr))
    self.dist_list.append(self.MatchDist(".*security.ubuntu.com/ubuntu",
                                         "^warty-security$",
                                         _("Ubuntu 4.10 Security Updates"),
                                         ubuntu_comps, ubuntu_comps_descr))
    self.dist_list.append(self.MatchDist(".*archive.ubuntu.com/ubuntu",
                                         "^warty-security$",
                                         _("Ubuntu 4.10 Security Updates"),
                                         ubuntu_comps, ubuntu_comps_descr))
    self.dist_list.append(self.MatchDist(".*archive.ubuntu.com/ubuntu",
                                         "^warty-updates$",
                                         _("Ubuntu 4.10 Updates"),
                                         ubuntu_comps, ubuntu_comps_descr))
    # Hoary
    self.dist_list.append(self.MatchDist(".*archive.ubuntu.com/ubuntu",
                                         "^hoary-security$",
                                         _("Ubuntu 5.04 Security Updates"),
                                         ubuntu_comps, ubuntu_comps_descr))
    self.dist_list.append(self.MatchDist(".*security.ubuntu.com/ubuntu",
                                         "^hoary-security$",
                                         _("Ubuntu 5.04 Security Updates"),
                                         ubuntu_comps, ubuntu_comps_descr))
    self.dist_list.append(self.MatchDist(".*archive.ubuntu.com/ubuntu",
                                         "^hoary$",
                                         "Ubuntu 5.04 \"Hoary Hedgehog\"",
                                         ubuntu_comps, ubuntu_comps_descr))
    self.dist_list.append(self.MatchDist(".*archive.ubuntu.com/ubuntu",
                                         "^hoary-updates$",
                                         _("Ubuntu 5.04 Updates"),
                                         ubuntu_comps, ubuntu_comps_descr))
    # Breezy
    self.dist_list.append(self.MatchDist(".*archive.ubuntu.com/ubuntu",
                                         "^breezy-security$",
                                         _("Ubuntu 5.10 Security Updates"),
                                         ubuntu_comps, ubuntu_comps_descr))
    self.dist_list.append(self.MatchDist(".*security.ubuntu.com/ubuntu",
                                         "^breezy-security$",
                                         _("Ubuntu 5.10 Security Updates"),
                                         ubuntu_comps, ubuntu_comps_descr))
    self.dist_list.append(self.MatchDist(".*archive.ubuntu.com/ubuntu",
                                         "^breezy$",
                                         "Ubuntu 5.10 \"Breezy Badger\"",
                                         ubuntu_comps, ubuntu_comps_descr))
    self.dist_list.append(self.MatchDist(".*archive.ubuntu.com/ubuntu",
                                         "^breezy-updates$",
                                         _("Ubuntu 5.10 Updates"),
                                         ubuntu_comps, ubuntu_comps_descr))
    # dapper
    self.dist_list.append(self.MatchDist(".*archive.ubuntu.com/ubuntu",
                                         "^dapper-security$",
                                         _("Ubuntu 6.04 Security Updates"),
                                         ubuntu_comps, ubuntu_comps_descr))
    self.dist_list.append(self.MatchDist(".*security.ubuntu.com/ubuntu",
                                         "^dapper-security$",
                                         _("Ubuntu 6.04 Security Updates"),
                                         ubuntu_comps, ubuntu_comps_descr))
    self.dist_list.append(self.MatchDist(".*archive.ubuntu.com/ubuntu",
                                         "^dapper$",
                                         "Ubuntu 6.04 \"Dapper Drake\"",
                                         ubuntu_comps, ubuntu_comps_descr))
    self.dist_list.append(self.MatchDist(".*archive.ubuntu.com/ubuntu",
                                         "^dapper-updates$",
                                         _("Ubuntu 6.04 Updates"),
                                         ubuntu_comps, ubuntu_comps_descr))


    # DEBIAN
    debian_comps =  ["^main$","^contrib$","^non-free$","^non-US$"]
    debian_comps_descr = [_("Officially supported"),
                          _("Contributed software"),
                          _("Non-free software"),
                          _("US export restricted software")
                          ]

    # dists by name
    self.dist_list.append(self.MatchDist(".*debian.org/debian",
                                         "^sarge$",
                                         _("Debian 3.1 \"Sarge\""),
                                         debian_comps, debian_comps_descr))
    self.dist_list.append(self.MatchDist(".*debian.org/debian",
                                         "^woody$",
                                         _("Debian 3.0 \"Woody\""),
                                         debian_comps, debian_comps_descr))
    # securtiy
    self.dist_list.append(self.MatchDist(".*security.debian.org",
                                         "^stable.*$",
                                         _("Debian Stable Security Updates"),
                                         debian_comps, debian_comps_descr))
    # dists by status
    self.dist_list.append(self.MatchDist(".*debian.org/debian",
                                         "^stable$",
                                         _("Debian Stable"),
                                         debian_comps, debian_comps_descr))
    self.dist_list.append(self.MatchDist(".*debian.org/debian",
                                         "^testing$",
                                         _("Debian Testing"),
                                         debian_comps, debian_comps_descr))
    self.dist_list.append(self.MatchDist(".*debian.org/debian",
                                         "^unstable$",
                                         _("Debian Unstable \"Sid\""),
                                         debian_comps, debian_comps_descr))

    # non-us
    self.dist_list.append(self.MatchDist(".*debian.org/debian-non-US",
                                         "^stable.*$",
                                         _("Debian Non-US (Stable)"),
                                         debian_comps, debian_comps_descr))
    self.dist_list.append(self.MatchDist(".*debian.org/debian-non-US",
                                         "^testing.*$",
                                         _("Debian Non-US (Testing)"),
                                         debian_comps, debian_comps_descr))
    self.dist_list.append(self.MatchDist(".*debian.org/debian-non-US",
                                         "^unstable.*$",
                                         _("Debian Non-US (Unstable)"),
                                         debian_comps, debian_comps_descr))



  
  def match(self,source):
    _ = gettext.gettext
    # some sane defaults first
    type_description = source.type
    dist_description = source.uri + " " + source.dist
    comp_description = ""
    for c in source.comps:
      comp_description = comp_description + " " + c 
    
    for t in self.type_list:
      if re.match(t.type, source.type):
        type_description = _(t.description)
        break

    for d in self.dist_list:
      #print "'%s'" %source.uri
      if re.match(d.uri, source.uri) and re.match(d.dist,source.dist):
        dist_description = d.description
        comp_description = ""
        for c in source.comps:
          found = False
          for i in range(len(d.comps)):
            if re.match(d.comps[i], c):
              comp_description = comp_description+"\n"+d.comps_descriptions[i]
              found = True
          if found == False:
            comp_description = comp_description+" "+c
        break
      
      
    return (type_description,dist_description,comp_description)


# some simple tests
if __name__ == "__main__":
  apt_pkg.InitConfig()
  sources = SourcesList()

  for entry in sources:
    print entry.str()
    #print entry.uri

  mirror = sources.is_mirror("http://archive.ubuntu.com/ubuntu/",
                             "http://de.archive.ubuntu.com/ubuntu/")
  print "is_mirror(): %s" % mirror
  
  print sources.is_mirror("http://archive.ubuntu.com/ubuntu",
                             "http://de.archive.ubuntu.com/ubuntu/")
