# import the core of apt_pkg
import apt_pkg
import sys
import os

# import some fancy classes
from apt.package import Package
from apt.cache import Cache
from apt.progress import OpProgress, FetchProgress, InstallProgress, CdromProgress
from apt_pkg import SizeToStr, VersionCompare

# init the package system
apt_pkg.init()


if not os.environ.has_key("PYTHON_APT_API_NOT_STABLE"):
    import warnings
    warnings.warn("Module apt is 100% API stable yet; ", FutureWarning)
    del warnings
