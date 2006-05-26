#! /usr/bin/env python
#
# FIXME: strip "TryExec" from the extracted menu files (and noDisplay)
#        
# TODO:
# - emacs21 ships it's icon in emacs-data, deal with this
# - some stuff needs to be blacklisted (e.g. gnome-about)
# - lots of packages have there desktop file in "-data", "-comon" (e.g. anjuta)
# - lots of packages have multiple desktop files for the same application
#   abiword, abiword-gnome, abiword-gtk

import os
import tarfile
import sys
import apt
import apt_pkg
import apt_inst
#import xdg.Menu
import os.path
import re
import tempfile
import subprocess
import string
import shutil
import urllib
import logging


# pkgs in main for the given dist
class Dist(object):
  def __init__(self,name):
    self.name = name
    self.pkgs_in_comp = {}

if __name__ == "__main__":

  # init
  apt_pkg.Config.Set("Dir::state","./apt/")
  apt_pkg.Config.Set("Dir::Etc","./apt")
  apt_pkg.Config.Set("Dir::State::status","./apt/status")
  try:
    os.makedirs("apt/lists/partial")
  except OSError:
    pass

  breezy = Dist("breezy")
  dapper = Dist("dapper")
  
  # go over the dists to find main pkgs
  for dist in [breezy, dapper]:
    
    for comp in ["main", "restricted", "universe", "multiverse"]:
      line = "deb http://archive.ubuntu.com/ubuntu %s %s\n" % (dist.name,comp)
      file("apt/sources.list","w").write(line)
      dist.pkgs_in_comp[comp] = set()

      # and the archs
      for arch in ["i386","amd64", "powerpc"]:
        apt_pkg.Config.Set("APT::Architecture",arch)
        cache = apt.Cache(apt.progress.OpTextProgress())
        prog = apt.progress.TextFetchProgress() 
        cache.update(prog)
        cache.open(apt.progress.OpTextProgress())
        map(lambda pkg: dist.pkgs_in_comp[comp].add(pkg.name), cache)

  # check what is no longer in main
  no_longer_main = breezy.pkgs_in_comp["main"] - dapper.pkgs_in_comp["main"]
  no_longer_main |= breezy.pkgs_in_comp["restricted"] - dapper.pkgs_in_comp["restricted"]

  # check what moved to universe and what was removed (or renamed)
  in_universe = lambda pkg: pkg in dapper.pkgs_in_comp["universe"] or pkg in dapper.pkgs_in_comp["multiverse"]

  # debug
  #not_in_universe = lambda pkg: not in_universe(pkg)
  #print filter(not_in_universe, no_longer_main)

  # this stuff was demoted and is no in universe
  demoted = filter(in_universe, no_longer_main)
  demoted.sort()

  outfile = "demoted.cfg"
  print "writing the demotion info to '%s'" % outfile
  # write it out
  out = open(outfile,"w")
  out.write("# demoted packages in dapper\n")
  out.write("\n".join(demoted))
