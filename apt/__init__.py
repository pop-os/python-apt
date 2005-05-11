# dummy file for now

import apt_pkg

# import some fancy classes
from apt.package import Package
from apt.cache import Cache
from apt.progress import OpProgress, FetchProgress, InstallProgress, CdromProgress
from apt_pkg import SizeToStr, VersionCompare

# init the package system
apt_pkg.init()

