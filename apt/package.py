# package.py - apt package abstraction
#  
#  Copyright (c) 2005 Canonical
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

import httplib
import sys
import random
import re
import socket
import string
import urllib2

import apt_pkg

# Set a timeout for the changelog download
socket.setdefaulttimeout(2)

#from gettext import gettext as _
import gettext
def _(s): return gettext.dgettext("python-apt", s)

class BaseDependency(object):
    " a single dependency "
    def __init__(self, name, rel, ver, pre):
        self.name = name
        self.relation = rel
        self.version = ver
        self.preDepend = pre

class Dependency(object):
    def __init__(self, alternatives):
        self.or_dependencies = alternatives

class Record(object):
    """ represents a pkgRecord, can be accessed like a
        dictionary and gives the original package record
        if accessed as a string """
    def __init__(self, s):
        self._str = s
        self._rec = apt_pkg.ParseSection(s)
    def __str__(self):
        return self._str
    def __getitem__(self, key):
        k = self._rec.get(key)
        if k is None:
            raise KeyError
        return k
    def has_key(self, key):
        return self._rec.has_key(key)

class Package(object):
    """ This class represents a package in the cache
    """
    def __init__(self, cache, depcache, records, sourcelist, pcache, pkgiter):
        """ Init the Package object """
        self._cache = cache             # low level cache
        self._depcache = depcache
        self._records = records
        self._pkg = pkgiter
        self._list = sourcelist               # sourcelist
        self._pcache = pcache           # python cache in cache.py
        self._changelog = ""            # Cached changelog
        pass

    # helper
    def _lookupRecord(self, UseCandidate=True):
        """ internal helper that moves the Records to the right
            position, must be called before _records is accessed """
        if UseCandidate:
            ver = self._depcache.GetCandidateVer(self._pkg)
        else:
            ver = self._pkg.CurrentVer

        # check if we found a version
        if ver == None:
            #print "No version for: %s (Candidate: %s)" % (self._pkg.Name, UseCandidate)
            return False
        
        if ver.FileList == None:
            print "No FileList for: %s " % self._pkg.Name()
            return False
        f, index = ver.FileList.pop(0)
        self._records.Lookup((f,index))
        return True


    # basic information (implemented as properties)

    # FIXME once python2.3 is dropped we can use @property instead
    # of name = property(name)

    def name(self):
        """ Return the name of the package """
        return self._pkg.Name
    name = property(name)

    def id(self):
        """ Return a uniq ID for the pkg, can be used to store
            additional information about the pkg """
        return self._pkg.ID
    id = property(id)

    def installedVersion(self):
        """ Return the installed version as string """
        ver = self._pkg.CurrentVer
        if ver != None:
            return ver.VerStr
        else:
            return None
    installedVersion = property(installedVersion)

    def candidateVersion(self):
        """ Return the candidate version as string """
        ver = self._depcache.GetCandidateVer(self._pkg)
        if ver != None:
            return ver.VerStr
        else:
            return None
    candidateVersion = property(candidateVersion)

    def _getDependencies(self, ver):
        depends_list = []
        depends = ver.DependsList
        for t in ["PreDepends", "Depends"]:
            if not depends.has_key(t):
                continue
            for depVerList in depends[t]:
                base_deps = []
                for depOr in depVerList:
                    base_deps.append(BaseDependency(depOr.TargetPkg.Name, depOr.CompType, depOr.TargetVer, (t == "PreDepends")))
                depends_list.append(Dependency(base_deps))
        return depends_list
        
    def candidateDependencies(self):
        """ return a list of candidate dependencies """
        candver = self._depcache.GetCandidateVer(self._pkg)
        if candver == None:
            return []
        return self._getDependencies(candver)
    candidateDependencies = property(candidateDependencies)
    
    def installedDependencies(self):
        """ return a list of installed dependencies """
        ver = self._pkg.CurrentVer
        if ver == None:
            return []
        return self._getDependencies(ver)
    installedDependencies = property(installedDependencies)

    def architecture(self):
        if not self._lookupRecord():
            return None
        sec = apt_pkg.ParseSection(self._records.Record)
        if sec.has_key("Architecture"):
            return sec["Architecture"]
        return None
    architecture = property(architecture)

    def _downloadable(self, useCandidate=True):
        """ helper, return if the version is downloadable """
        if useCandidate:
            ver = self._depcache.GetCandidateVer(self._pkg)
        else:
            ver = self._pkg.CurrentVer
        if ver == None:
            return False
        return ver.Downloadable
    def candidateDownloadable(self):
        " returns if the canidate is downloadable "
        return self._downloadable(useCandidate=True)
    candidateDownloadable = property(candidateDownloadable)

    def installedDownloadable(self):
        " returns if the installed version is downloadable "
        return self._downloadable(useCandidate=False)
    installedDownloadable = property(installedDownloadable)

    def sourcePackageName(self):
        """ Return the source package name as string """
        if not self._lookupRecord():
            if not self._lookupRecord(UseCandidate=False):
                return self._pkg.Name
        src = self._records.SourcePkg
        if src != "":
            return src
        else:
            return self._pkg.Name
    sourcePackageName = property(sourcePackageName)

    def homepage(self):
        """ Return the homepage field as string """
        if not self._lookupRecord():
            return None
        return self._records.Homepage
    homepage = property(homepage)

    def section(self):
        """ Return the section of the package"""
        return self._pkg.Section
    section = property(section)

    def priority(self):
        """ Return the priority (of the candidate version)"""
        ver = self._depcache.GetCandidateVer(self._pkg)
        if ver:
            return ver.PriorityStr
        else:
            return None
    priority = property(priority)

    def installedPriority(self):
        """ Return the priority (of the installed version)"""
        ver = self._depcache.GetCandidateVer(self._pkg)
        if ver:
            return ver.PriorityStr
        else:
            return None
    installedPriority = property(installedPriority)

    def summary(self):
        """ Return the short description (one line summary) """
        if not self._lookupRecord():
            return ""
        ver = self._depcache.GetCandidateVer(self._pkg)
        desc_iter = ver.TranslatedDescription
        self._records.Lookup(desc_iter.FileList.pop(0))
        return self._records.ShortDesc
    summary = property(summary)

    def description(self, format=True, useDots=False):
        """
        Return the formated long description according to the Debian policy
        (Chapter 5.6.13).
        See http://www.debian.org/doc/debian-policy/ch-controlfields.html
        for more information.
        """
        if not format:
            return self.rawDescription
        if not self._lookupRecord():
            return ""
        # get the translated description
        ver = self._depcache.GetCandidateVer(self._pkg)
        desc_iter = ver.TranslatedDescription
        self._records.Lookup(desc_iter.FileList.pop(0))
        desc = ""
        try:
            s = unicode(self._records.LongDesc,"utf-8")
        except UnicodeDecodeError,e:
            s = _("Invalid unicode in description for '%s' (%s). "
                  "Please report.") % (self.name,e)
        lines = string.split(s, "\n")
        for i in range(len(lines)):
            # Skip the first line, since its a duplication of the summary
            if i == 0: continue
            raw_line = lines[i]
            if raw_line.strip() == ".":
                # The line is just line break
                if not desc.endswith("\n"):
                    desc += "\n"
                continue
            elif raw_line.startswith("  "):
                # The line should be displayed verbatim without word wrapping
                if not desc.endswith("\n"):
                    line = "\n%s\n" % raw_line[2:]
                else:
                    line = "%s\n" % raw_line[2:]
            elif raw_line.startswith(" "):
                # The line is part of a paragraph.
                if desc.endswith("\n") or desc == "":
                    # Skip the leading white space
                    line = raw_line[1:]
                else:
                    line = raw_line
            else:
                line = raw_line
            # Use dots for lists
            if useDots:
                line = re.sub(r"^(\s*)(\*|0|o|-) ", ur"\1\u2022 ", line, 1)
            # Add current line to the description
            desc += line
        return desc
    description = property(description)

    def rawDescription(self):
        """ return the long description (raw)"""
        if not self._lookupRecord():
            return ""
        return self._records.LongDesc
    rawDescription = property(rawDescription)
        
    def candidateRecord(self):
        " return the full pkgrecord as string of the candidate version "
        if not self._lookupRecord(True):
            return None
        return Record(self._records.Record)
    candidateRecord = property(candidateRecord)

    def installedRecord(self):
        " return the full pkgrecord as string of the installed version "
        if not self._lookupRecord(False):
            return None
        return Record(self._records.Record)
    installedRecord = property(installedRecord)

    # depcache states
    def markedInstall(self):
        """ Package is marked for install """
        return self._depcache.MarkedInstall(self._pkg)
    markedInstall = property(markedInstall)

    def markedUpgrade(self):
        """ Package is marked for upgrade """
        return self._depcache.MarkedUpgrade(self._pkg)
    markedUpgrade = property(markedUpgrade)

    def markedDelete(self):
        """ Package is marked for delete """
        return self._depcache.MarkedDelete(self._pkg)
    markedDelete = property(markedDelete) 

    def markedKeep(self):
        """ Package is marked for keep """
        return self._depcache.MarkedKeep(self._pkg)
    markedKeep = property(markedKeep)

    def markedDowngrade(self):
        """ Package is marked for downgrade """
        return self._depcache.MarkedDowngrade(self._pkg)
    markedDowngrade = property(markedDowngrade)

    def markedReinstall(self):
        """ Package is marked for reinstall """
        return self._depcache.MarkedReinstall(self._pkg)
    markedReinstall = property(markedReinstall)

    def isInstalled(self):
        """ Package is installed """
        return (self._pkg.CurrentVer != None)
    isInstalled = property(isInstalled)

    def isUpgradable(self):
        """ Package is upgradable """    
        return self.isInstalled and self._depcache.IsUpgradable(self._pkg)
    isUpgradable = property(isUpgradable)

    def isAutoRemovable(self):
        """ 
        Package is installed as a automatic dependency and is
        no longer required
        """
        return self.isInstalled and self._depcache.IsGarbage(self._pkg)
    isAutoRemovable = property(isAutoRemovable)

    # size
    def packageSize(self):
        """ The size of the candidate deb package """
        ver = self._depcache.GetCandidateVer(self._pkg)
        return ver.Size
    packageSize = property(packageSize)

    def installedPackageSize(self):
        """ The size of the installed deb package """
        ver = self._pkg.CurrentVer
        return ver.Size
    installedPackageSize = property(installedPackageSize)

    def candidateInstalledSize(self, UseCandidate=True):
        """ The size of the candidate installed package """
        ver = self._depcache.GetCandidateVer(self._pkg)
    candidateInstalledSize = property(candidateInstalledSize)

    def installedSize(self):
        """ The size of the currently installed package """
        ver = self._pkg.CurrentVer
        if ver is None:
            return 0
        return ver.InstalledSize
    installedSize = property(installedSize)

    def installedFiles(self):
        """
        Return the list of unicode names of the files which have
        been installed by this package
        """
        path = "/var/lib/dpkg/info/%s.list" % self.name
        try:
            list = open(path)
            files = list.read().decode().split("\n")
            list.close()
        except:
            return []
        return files
    installedFiles = property(installedFiles)

    def getChangelog(self, uri=None, cancel_lock=None):
        """
        Download the changelog of the package and return it as unicode 
        string

        uri: Is the uri to the changelog file. The following named variables
             will be substituted: src_section, prefix, src_pkg and src_ver
             For example the Ubuntu changelog:
             uri = "http://changelogs.ubuntu.com/changelogs/pool" \\
                   "/%(src_section)s/%(prefix)s/%(src_pkg)s" \\
                   "/%(src_pkg)s_%(src_ver)s/changelog"
        cancel_lock: If this threading.Lock() is set, the download will be
                     canceled
        """
        # Return a cached changelog if available
        if self._changelog != "":
            return self._changelog

        if uri == None:
            if self.candidateOrigin[0].origin == "Debian":
                uri = "http://packages.debian.org/changelogs/pool" \
                      "/%(src_section)s/%(prefix)s/%(src_pkg)s" \
                      "/%(src_pkg)s_%(src_ver)s/changelog"
            elif self.candidateOrigin[0].origin == "Ubuntu":
                uri = "http://changelogs.ubuntu.com/changelogs/pool" \
                      "/%(src_section)s/%(prefix)s/%(src_pkg)s" \
                      "/%(src_pkg)s_%(src_ver)s/changelog"
            else:
                return _("The list of changes is not available")

        # get the src package name
        src_pkg = self.sourcePackageName

        # assume "main" section 
        src_section = "main"
        # use the section of the candidate as a starting point
        section = self._depcache.GetCandidateVer(self._pkg).Section

        # get the source version, start with the binaries version
        bin_ver = self.candidateVersion
        src_ver = self.candidateVersion
        #print "bin: %s" % binver
        try:
            # try to get the source version of the pkg, this differs
            # for some (e.g. libnspr4 on ubuntu)
            # this feature only works if the correct deb-src are in the 
            # sources.list
            # otherwise we fall back to the binary version number
            src_records = apt_pkg.GetPkgSrcRecords()
            src_rec = src_records.Lookup(src_pkg)
            if src_rec:
                src_ver = src_records.Version
                #if apt_pkg.VersionCompare(binver, srcver) > 0:
                #    srcver = binver
                if not src_ver:
                    src_ver = bin_ver
                #print "srcver: %s" % src_ver
                section = src_records.Section
                #print "srcsect: %s" % section
            else:
                # fail into the error handler
                raise SystemError
        except SystemError, e:
            src_ver = bin_ver

        l = section.split("/")
        if len(l) > 1:
            src_section = l[0]

        # lib is handled special
        prefix = src_pkg[0]
        if src_pkg.startswith("lib"):
            prefix = "lib" + src_pkg[3]

        # stip epoch
        l = string.split(src_ver,":")
        if len(l) > 1:
            src_ver = "".join(l[1:])

        uri = uri % {"src_section" : src_section,
                     "prefix" : prefix,
                     "src_pkg" : src_pkg,
                     "src_ver" : src_ver}
        try:
            # Check if the download was canceled
            if cancel_lock and cancel_lock.isSet(): return ""
            changelog_file = urllib2.urlopen(uri)
            # do only get the lines that are new
            changelog = ""
            regexp = "^%s \((.*)\)(.*)$" % (re.escape(src_pkg))

            i=0
            while True:
                # Check if the download was canceled
                if cancel_lock and cancel_lock.isSet(): return ""
                # Read changelog line by line
                line_raw = changelog_file.readline()
                if line_raw == "":
                    break
                # The changelog is encoded in utf-8, but since there isn't any
                # http header, urllib2 seems to treat it as ascii
                line = line_raw.decode("utf-8")

                #print line.encode('utf-8')
                match = re.match(regexp, line)
                if match:
                    # strip epoch from installed version
                    # and from changelog too
                    installed = self.installedVersion
                    if installed and ":" in installed:
                        installed = installed.split(":",1)[1]
                    changelog_ver = match.group(1)
                    if changelog_ver and ":" in changelog_ver:
                        changelog_ver = changelog_ver.split(":", 1)[1]
                    if installed and \
                        apt_pkg.VersionCompare(changelog_ver, installed) <= 0:
                        break
                # EOF (shouldn't really happen)
                changelog += line

            # Print an error if we failed to extract a changelog
            if len(changelog) == 0:
                changelog = _("The list of changes is not available")
            self._changelog = changelog
        except urllib2.HTTPError,e:
            return _("The list of changes is not available yet.\n\n"
                     "Please use http://launchpad.net/ubuntu/+source/%s/%s/"
                     "+changelog\n"
                     "until the changes become available or try again "
                     "later.") % (srcpkg, srcver),
        except IOError, httplib.BadStatusLine:
                return _("Failed to download the list of changes. \nPlease "
                         "check your Internet connection.")
        return self._changelog

    # canidate origin
    class Origin:
        def __init__(self, pkg, VerFileIter):
            self.component = VerFileIter.Component
            self.archive = VerFileIter.Archive
            self.origin = VerFileIter.Origin
            self.label = VerFileIter.Label
            self.site = VerFileIter.Site
            # check the trust
            indexfile = pkg._list.FindIndex(VerFileIter)
            if indexfile and indexfile.IsTrusted:
                self.trusted = True
            else:
                self.trusted = False
        def __repr__(self):
            return "component: '%s' archive: '%s' origin: '%s' label: '%s' " \
                   "site '%s' isTrusted: '%s'"%  (self.component, self.archive,
                                                  self.origin, self.label,
                                                  self.site, self.trusted)
        
    def candidateOrigin(self):
        ver = self._depcache.GetCandidateVer(self._pkg)
        if not ver:
            return None
        origins = []
        for (verFileIter,index) in ver.FileList:
            origins.append(self.Origin(self, verFileIter))
        return origins
    candidateOrigin = property(candidateOrigin)

    # depcache actions
    def markKeep(self):
        """ mark a package for keep """
        self._pcache.cachePreChange()
        self._depcache.MarkKeep(self._pkg)
        self._pcache.cachePostChange()
    def markDelete(self, autoFix=True, purge=False):
        """ mark a package for delete. Run the resolver if autoFix is set.
            Mark the package as purge (remove with configuration) if 'purge'
            is set.
            """
        self._pcache.cachePreChange()
        self._depcache.MarkDelete(self._pkg, purge)
        # try to fix broken stuffsta
        if autoFix and self._depcache.BrokenCount > 0:
            Fix = apt_pkg.GetPkgProblemResolver(self._depcache)
            Fix.Clear(self._pkg)
            Fix.Protect(self._pkg)
            Fix.Remove(self._pkg)
            Fix.InstallProtect()
            Fix.Resolve()
        self._pcache.cachePostChange()
    def markInstall(self, autoFix=True, autoInst=True, fromUser=True):
        """ mark a package for install. Run the resolver if autoFix is set,
            automatically install required dependencies if autoInst is set
            record it as automatically installed when fromuser is set to false
        """
        self._pcache.cachePreChange()
        self._depcache.MarkInstall(self._pkg, autoInst, fromUser)
        # try to fix broken stuff
        if autoFix and self._depcache.BrokenCount > 0:
            fixer = apt_pkg.GetPkgProblemResolver(self._depcache)
            fixer.Clear(self._pkg)
            fixer.Protect(self._pkg)
            fixer.Resolve(True)
        self._pcache.cachePostChange()
    def markUpgrade(self):
        """ mark a package for upgrade """
        if self.isUpgradable:
            self.markInstall()
        else:
            # FIXME: we may want to throw a exception here
            sys.stderr.write("MarkUpgrade() called on a non-upgrable pkg: '%s'\n"  %self._pkg.Name)

    def commit(self, fprogress, iprogress):
        """ commit the changes, need a FetchProgress and InstallProgress
            object as argument
        """
        self._depcache.Commit(fprogress, iprogress)
        

# self-test
if __name__ == "__main__":
    print "Self-test for the Package modul"
    apt_pkg.init()
    cache = apt_pkg.GetCache()
    depcache = apt_pkg.GetDepCache(cache)
    records = apt_pkg.GetPkgRecords(cache)
    sourcelist = apt_pkg.GetPkgSourceList()

    pkgiter = cache["apt-utils"]
    pkg = Package(cache, depcache, records, sourcelist, None, pkgiter)
    print "Name: %s " % pkg.name
    print "ID: %s " % pkg.id
    print "Priority (Candidate): %s " % pkg.priority
    print "Priority (Installed): %s " % pkg.installedPriority
    print "Installed: %s " % pkg.installedVersion
    print "Candidate: %s " % pkg.candidateVersion
    print "CandidateDownloadable: %s" % pkg.candidateDownloadable
    print "CandidateOrigins: %s" % pkg.candidateOrigin
    print "SourcePkg: %s " % pkg.sourcePackageName
    print "Section: %s " % pkg.section
    print "Summary: %s" % pkg.summary
    print "Description (formated) :\n%s" % pkg.description
    print "Description (unformated):\n%s" % pkg.rawDescription
    print "InstalledSize: %s " % pkg.installedSize
    print "PackageSize: %s " % pkg.packageSize
    print "Dependencies: %s" % pkg.installedDependencies
    for dep in pkg.candidateDependencies:
        print ",".join(["%s (%s) (%s) (%s)" % (o.name,o.version,o.relation, o.preDepend) for o in dep.or_dependencies])
    print "arch: %s" % pkg.architecture
    print "homepage: %s" % pkg.homepage
    print "rec: ",pkg.candidateRecord

    # now test install/remove
    import apt
    progress = apt.progress.OpTextProgress()
    cache = apt.Cache(progress)
    for i in [True, False]:
        print "Running install on random upgradable pkgs with AutoFix: %s " % i
        for name in cache.keys():
            pkg = cache[name]
            if pkg.isUpgradable:
                if random.randint(0,1) == 1:
                    pkg.markInstall(i)
        print "Broken: %s " % cache._depcache.BrokenCount
        print "InstCount: %s " % cache._depcache.InstCount

    print
    # get a new cache
    for i in [True, False]:
        print "Randomly remove some packages with AutoFix: %s" % i
        cache = apt.Cache(progress)
        for name in cache.keys():
            if random.randint(0,1) == 1:
                try:
                    cache[name].markDelete(i)
                except SystemError:
                    print "Error trying to remove: %s " % name
        print "Broken: %s " % cache._depcache.BrokenCount
        print "DelCount: %s " % cache._depcache.DelCount
