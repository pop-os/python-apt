# Copyright (C) 2009 Canonical
#
# Authors:
#  Michael Vogt
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License as
#  published by the Free Software Foundation; either version 2 of the
#  License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

import apt_pkg
import os.path

def get_maintenance_end_date(release_date, m_months):
    """
    get the (year, month) tuple when the maintenance for the distribution
    ends. Needs the data of the release and the number of months that
    its is supported as input
    """
    years = m_months / 12
    months = m_months % 12
    support_end_year = release_date.year + years + (release_date.month + months)/12
    support_end_month = (release_date.month + months) % 12
    return (support_end_year, support_end_month)

def get_release_date_from_release_file(path):
    """
    return the release date as time_t for the given release file
    """
    if not path or not os.path.exists(path):
        return None
    tag = apt_pkg.ParseTagFile(open(path))
    tag.Step()
    if not tag.Section.has_key("Date"):
        return None
    date = tag.Section["Date"]
    return apt_pkg.StrToTime(date)

def get_release_filename_for_pkg(cache, pkgname, label, release):
    " get the release file that provides this pkg "
    if not cache.has_key(pkgname):
        return None
    pkg = cache[pkgname]
    ver = None
    # look for the version that comes from the repos with
    # the given label and origin
    for aver in pkg._pkg.VersionList:
        if aver == None or aver.FileList == None:
            continue
        for verFile, index in aver.FileList:
            #print verFile
            if (verFile.Origin == label and
                verFile.Label == label and
                verFile.Archive == release):
                ver = aver
    if not ver:
        return None
    indexfile = cache._list.FindIndex(ver.FileList[0][0])
    for metaindex in cache._list.List:
        for m in metaindex.IndexFiles:
            if (indexfile and
                indexfile.Describe == m.Describe and
                indexfile.IsTrusted):
                dir = apt_pkg.Config.FindDir("Dir::State::lists")
                name = apt_pkg.URItoFileName(metaindex.URI)+"dists_%s_Release" % metaindex.Dist
                return dir+name
    return None
