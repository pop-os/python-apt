:mod:`apt.debfile` --- Classes related to debian package files
==============================================================
The :mod:`apt.debfile` provides classes to work with locally available
debian packages, or source packages.

.. module:: apt.debfile

Binary packages
----------------
.. autoclass:: DebPackage
    :members:
    :inherited-members:
    :undoc-members:

    The :class:`DebPackage` class is a class for working with '.deb' files,
    also known as Debian packages.

    It provides methods and attributes to get a list of the files in the
    package, to install the package and much more.

    If you specify ``cache`` it has to point to an :class:`apt.cache.Cache()`
    object.

    All methods except for :meth:`open()` and the attribute :attr:`filelist` have been
    introduced in version 0.7.9.

Source packages
----------------
.. autoclass:: DscSrcPackage
    :members:
    :inherited-members:
    :undoc-members:

    Provide functionality to work with locally available source packages,
    especially with their '.dsc' file.

    .. versionadded:: 0.7.9
