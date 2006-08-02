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

#import pdb

from UpdateManager.Common.DistInfo import DistInfo


# some global helpers
def is_mirror(master_uri, compare_uri):
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
  # remove the leading "<country>." (if any) and see if that helps
  if "." in compare_srv and \
         compare_srv[compare_srv.index(".")+1:] == master_srv:
    #print "Mirror"
    return True
  return False

def uniq(s):
  """ simple and efficient way to return uniq list """
  return list(set(s))



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
    self.template = None
    self.children = []

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
    # Sanity check
    if len(pieces) < 3:
        self.invalid = True
        return
    # Type, deb or deb-src
    self.type = string.strip(pieces[0])
    # Sanity check
    if self.type not in ("deb", "deb-src"):
      self.invalid = True
      return
    # URI
    self.uri = string.strip(pieces[1])
    if len(self.uri) < 1:
      self.invalid = True
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

  def __str__(self):
    """ debug helper """
    return self.str().strip()

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
    
# the SourceList file as a class
class NullMatcher(object):
  def match(self, s):
    return True

class SourcesList:
  def __init__(self, withMatcher=True):
    self.list = []      # of Type SourceEntries
    if withMatcher:
      self.matcher = SourceEntryMatcher()
    else:
      self.matcher = NullMatcher()
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
    # check if the source item fits a predefined template
    for source in self.list:
        if source.invalid == False:
            self.matcher.match(source)

  def __iter__(self):
    for entry in self.list:
      yield entry
    raise StopIteration

  def add(self, type, uri, dist, comps, comment="", pos=-1, file=None):
    """
    Add a new source to the sources.list.
    The method will search for existing matching repos and will try to 
    reuse them as far as possible
    """
    for source in self.list:
      # if there is a repo with the same (type, uri, dist) just add the
      # components
      if source.disabled == False and source.invalid == False and \
         source.type == type and uri == source.uri and \
         source.dist == dist:
        comps = uniq(source.comps + comps)
        source.comps = comps
        return source
      # if there is a corresponding repo which is disabled, enable it
      elif source.disabled == True and source.invalid == False and \
           source.type == type and uri == source.uri and \
           source.dist == dist and \
           len(set(source.comps) & set(comps)) == len(comps):
        source.disabled = False
        return source
    # there isn't any matching source, so create a new line and parse it
    line = "%s %s %s" % (type,uri,dist)
    for c in comps:
      line = line + " " + c;
    if comment != "":
      line = "%s #%s\n" %(line,comment)
    line = line + "\n"
    new_entry = SourceEntry(line)
    if file != None:
      new_entry.file = file
    self.matcher.match(new_entry)
    self.list.insert(pos, new_entry)
    return new_entry

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
    try:
      f = open(file, "r")
      lines = f.readlines()
      for line in lines:
        source = SourceEntry(line,file)
        self.list.append(source)
    except:
      print "could not open file '%s'" % file
    else:
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

  def check_for_relations(self, sources_list):
    """get all parent and child channels in the sources list"""
    parents = []
    used_child_templates = {}
    for source in sources_list:
      # try to avoid checking uninterressting sources
      if source.template == None:
        continue
      # set up a dict with all used child templates and corresponding 
      # source entries
      if source.template.child == True:
          key = source.template
          if not used_child_templates.has_key(key):
              used_child_templates[key] = []
          temp = used_child_templates[key]
          temp.append(source)
      else:
          # store each source with children aka. a parent :)
          if len(source.template.children) > 0:
              parents.append(source)
    #print self.used_child_templates
    #print self.parents
    return (parents, used_child_templates)

# templates for the add dialog
class SourceEntryTemplate(SourceEntry):
  def __init__(self,a_type,uri,dist,description,comps):
    self.comps_descriptions = []
    self.type = a_type
    self.uri = uri
    self.dist = dist
    self.description = description
    self.comps = comps

  def matches(self,source_entry):
    """ check if a given source_entry matches this one """
    if (self.type != source_entry.type):
      return False
    if (self.dist != source_entry.dist):
      return False
    if not is_mirror(self.uri,source_entry.uri):
      return False
    for e_comp in source_entry.comps:
      for t_comp in self.comps:
        if e_comp == t_comp.name: break
      else:
        return False
    return True

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
    self.templates = []
    # Get the human readable channel and comp names from the channel .infos
    spec_files = glob.glob("/usr/share/update-manager/channels/*.info")
    for f in spec_files:
        f = os.path.basename(f)
        i = f.find(".info")
        f = f[0:i]
        dist = DistInfo(f)
        for suite in dist.suites:
            if suite.match_uri != None:
                self.templates.append(suite)
    return

  def match(self, source):
    """Add a matching template to the source"""
    _ = gettext.gettext
    found = False
    for template in self.templates:
      #print "'%s'" %source.uri
      if re.search(template.match_uri, source.uri) and \
         re.match(template.match_name, source.dist):
        found = True
        source.template = template
        break
    return found

class Distribution:
  def __init__(self):
    """"
    Container for distribution specific informations
    """
    # LSB information
    self.id = ""
    self.codename = ""
    self.description = ""
    self.release = ""

    # get the LSB information
    lsb_info = []
    for lsb_option in ["-i", "-c", "-d", "-r"]:
        pipe = os.popen("lsb_release %s | cut -d : -f 2-" % lsb_option)
        lsb_info.append(pipe.read().strip())
        del pipe
    (self.id, self.codename, self.description, self.release) = lsb_info

    # get a list of country codes and real names
    self.countries = {}
    try:
        f = open("/usr/share/iso-codes/iso_3166.tab", "r")
        lines = f.readlines()
        for line in lines:
            parts = line.split("\t")
            self.countries[parts[0].lower()] = parts[1]
    except:
        print "could not open file '%s'" % file
    else:
        f.close()

  def get_sources(self, sources_list):
    """
    Find the corresponding template, main and child sources 
    for the distribution 
    """
    # corresponding sources
    self.source_template = None
    self.child_sources = []
    self.main_sources = []
    self.disabled_sources = []
    self.cdrom_sources = []
    self.download_comps = []
    self.enabled_comps = []
    self.cdrom_comps = []
    self.used_media = []
    self.get_source_code = False
    self.source_code_sources = []

    # location of the sources
    self.default_server = ""
    self.main_server = ""
    self.nearest_server = ""
    self.used_servers = []

    # find the distro template
    for template in sources_list.matcher.templates:
        if template.name == self.codename and\
           template.distribution == self.id:
            #print "yeah! found a template for %s" % self.description
            #print template.description, template.base_uri, template.components
            self.source_template = template
            break
    if self.source_template == None:
        print "Error: could not find a distribution template"
        # FIXME: will go away - only for debugging issues
        sys.exit(1)

    # find main and child sources
    media = []
    comps = []
    cdrom_comps = []
    enabled_comps = []
    source_code = []
    for source in sources_list.list:
        if source.invalid == False and\
           source.dist == self.codename and\
           source.template and\
           source.template.name == self.codename:
            #print "yeah! found a distro repo:  %s" % source.line
            # cdroms need do be handled differently
            if source.uri.startswith("cdrom:") and \
               source.disabled == False:
                self.cdrom_sources.append(source)
                cdrom_comps.extend(source.comps)
            elif source.uri.startswith("cdrom:") and \
                 source.disabled == True:
                self.cdrom_sources.append(source)
            elif source.type == "deb" and source.disabled == False:
                self.main_sources.append(source)
                comps.extend(source.comps)
                media.append(source.uri)
            elif source.type == "deb" and source.disabled == True:
                self.disabled_sources.append(source)
            elif source.type.endswith("-src") and source.disabled == False:
                self.source_code_sources.append(source)
            elif source.type.endswith("-src") and source.disabled == True:
                self.disabled_sources.append(source)
        if source.template in self.source_template.children:
            #print "yeah! child found: %s" % source.template.name
            if source.type == "deb":
                self.child_sources.append(source)
            elif source.type == "deb-src":
                self.source_code_sources.append(source)
    self.download_comps = set(comps)
    self.cdrom_comps = set(cdrom_comps)
    enabled_comps.extend(comps)
    enabled_comps.extend(cdrom_comps)
    self.enabled_comps = set(enabled_comps)
    self.used_media = set(media)

    self.get_mirrors()
  
  def get_mirrors(self):
    """
    Provide a set of mirrors where you can get the distribution from
    """
    # the main server is stored in the template
    self.main_server = self.source_template.base_uri

    # try to guess the nearest mirror from the locale
    # FIXME: for debian we need something different
    if self.id == "Ubuntu":
        locale = os.getenv("LANG", default="en.UK")
        a = locale.find("_")
        z = locale.find(".")
        if z == -1:
            z = len(locale)
        country_code = locale[a+1:z].lower()
        self.nearest_server = "http://%s.archive.ubuntu.com/ubuntu/" % \
                              country_code
        if self.countries.has_key(country_code):
            self.country = self.countries[country_code]
        else:
            self.country = None

    # other used servers
    for medium in self.used_media:
        if not medium.startswith("cdrom:"):
            # seems to be a network source
            self.used_servers.append(medium)

    if len(self.main_sources) == 0:
        self.default_server = self.main_server
    else:
        self.default_server = self.main_sources[0].uri

  def add_source(self, sources_list, type=None, 
                 uri=None, dist=None, comps=None, comment=""):
    """
    Add distribution specific sources
    """
    if uri == None:
        # FIXME: Add support for the server selector
        uri = self.default_server
    if dist == None:
        dist = self.codename
    if comps == None:
        comps = list(self.enabled_comps)
    if type == None:
        type = "deb"
    if comment == "":
        comment == "Added by software-properties"
    new_source = sources_list.add(type, uri, dist, comps, comment)
    # if source code is enabled add a deb-src line after the new
    # source
    if self.get_source_code == True and not type.endswith("-src"):
        sources_list.add("%s-src" % type, uri, dist, comps, comment, 
                         file=new_source.file,
                         pos=sources_list.list.index(new_source)+1)

  def enable_component(self, sourceslist, comp):
    """
    Disable a component in all main, child and source code sources
    (excluding cdrom based sources)

    sourceslist:  an aptsource.sources_list
    comp:         the component that should be enabled
    """
    sources = []
    sources.extend(self.main_sources)
    sources.extend(self.child_sources)
    sources.extend(self.source_code_sources)
    # check if there is a main source at all
    if len(self.main_sources) < 1:
        # create a new main source
        self.add_source(sourceslist, comps=["%s"%comp])
    else:
        # add the comp to all main, child and source code sources
        for source in sources:
            if comp not in source.comps:
                source.comps.append(comp)
    if self.get_source_code == True:
        for source in self.source_code_sources:
            if comp not in source.comps: source.comps.append(comp)

  def disable_component(self, sourceslist, comp):
    """
    Disable a component in all main, child and source code sources
    (excluding cdrom based sources)
    """
    sources = []
    sources.extend(self.main_sources)
    sources.extend(self.child_sources)
    sources.extend(self.source_code_sources)
    if comp in self.cdrom_comps:
        sources = []
        sources.extend(self.main_sources)

    for source in sources:
        if comp in source.comps: 
            source.comps.remove(comp)
            if len(source.comps) < 1: 
               sourceslist.remove(source)


# some simple tests
if __name__ == "__main__":
  apt_pkg.InitConfig()
  sources = SourcesList()

  for entry in sources:
    print entry.str()
    #print entry.uri

  mirror = is_mirror("http://archive.ubuntu.com/ubuntu/",
                     "http://de.archive.ubuntu.com/ubuntu/")
  print "is_mirror(): %s" % mirror
  
  print is_mirror("http://archive.ubuntu.com/ubuntu",
                  "http://de.archive.ubuntu.com/ubuntu/")
