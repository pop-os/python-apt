:mod:`apt_pkg` --- The low-level bindings for apt-pkg
=====================================================
.. module:: apt_pkg

The apt_pkg extensions provides a more low-level way to work with apt. It can
do everything apt can, and is written in C++. It has been in python-apt since
the beginning.


.. toctree::
    :maxdepth: 2
    :glob:

    *


Module Initialization
---------------------


.. function:: initConfig

    Initialize the configuration of apt. This is needed for most operations.

.. function:: initSystem

    Initialize the system.

.. function:: init

    Deprecated function. Use initConfig() and initSystem() instead.

Object initialization
----------------------
.. function:: GetCache([progress])

    Return a :class:`pkgCache` object. The optional parameter ``progress``
    specifies an instance of :class:`apt.progress.OpProgress()` which will
    display the open progress.

.. function:: GetCdrom()

    Return a Cdrom object with the following methods:

    .. method:: Cdrom.Ident(progress)

        Identify the cdrom. The parameter ``progress`` refers to an
        :class:`apt.progress.CdromProgress()` object.

    .. method:: Cdrom.Add(progress)

        Add the cdrom to the sources.list file. The parameter ``progress``
        refers to an :class:`apt.progress.CdromProgress()` object.



.. function:: GetDepCache(cache)

    Return a :class:`pkgDepCache` object. The parameter ``cache`` specifies an
    instance of :class:`pkgCache` (see :func:`GetCache()`).


.. function:: GetPkgSourceList()

    Return a :class:`pkgSourceList` object.


The Acquire interface
----------------------
.. function:: GetAcquire([progress])

    Return an :class:`Acquire` object. This is a class which allows you
    to fetch files, or archive contents. The parameter ``progress`` refers to
    an :class:`apt.progress.FetchProgress()` object.

    Acquire items have multiple methods:

    .. method:: Acquire.Run()

        Fetch all the items which have been added by :func:`GetPkgAcqFile`.

    .. method:: Acquire.Shutdown()

        Shut the fetcher down.

    .. attribute:: Acquire.TotalNeeded

        The total amount of bytes needed (including those of files which are
        already present)

    .. attribute:: Acquire.FetchNeeded

        The total amount of bytes which need to be fetched.

    .. attribute:: Acquire.PartialPresent

        Whether some files have been acquired already. (???)


.. function:: GetPkgAcqFile(aquire, uri[, md5, size, descr, shortDescr, destDir, destFile])

    The parameter ``acquire`` refers to an :class:`Acquire()` object as returned
    by :func:`GetAcquire`. The file will be added to the Acquire queue
    automatically.

    The parameter ``uri`` refers to the location of the file, any protocol
    of apt is supported.

    The parameter ``md5`` refers to the md5sum of the file. This can be used
    for checking the file.

    The parameter ``size`` can be used to specify the size of the package,
    which can then be used to calculate the progress and validate the download.

    The parameter ``descr`` is a descripition of the download. It may be
    used to describe the item in the progress class. ``shortDescr`` is the
    short form of it.

    You can use ``destDir`` to manipulate the directory where the file will
    be saved in. Together with ``destFile`` you can specify the complete target
    path.



Hash functions
--------------
The apt_pkg module also provides several hash functions. If you develop
applications with python-apt it is often easier to use these functions instead
of the ones provides in Python's :mod:`hashlib` module.

.. function:: md5sum(object)

    Return the md5sum of the object. ``object`` may either be a string, in
    which case the md5sum of the string is returned, or a :class:`file()`
    object, in which case the md5sum of its contents is returned.

.. function:: sha1sum(object)

    Return the sha1sum of the object. ``object`` may either be a string, in
    which case the sha1sum of the string is returned, or a :class:`file()`
    object, in which case the sha1sum of its contents is returned.

.. function:: sha256sum(object)

    Return the sha256sum of the object. ``object`` may either be a string, in
    which case the sha256sum of the string is returned, or a :class:`file()`
    object, in which case the sha256sum of its contents is returned.

Other functions
----------------

.. note::

    This documentation is created automatically and should be rewritten.

.. autofunction:: Base64Encode
.. autofunction:: CheckDep
.. autofunction:: CheckDomainList
.. autofunction:: DeQuoteString
.. autofunction:: GetLock
.. autofunction:: GetPackageManager
.. autofunction:: GetPkgActionGroup
.. autofunction:: GetPkgProblemResolver
.. autofunction:: GetPkgRecords
.. autofunction:: GetPkgSrcRecords
.. autofunction:: newConfiguration
.. autofunction:: ParseCommandLine
.. autofunction:: ParseDepends
.. autofunction:: ParseSection
.. autofunction:: ParseSrcDepends
.. autofunction:: ParseTagFile
.. autofunction:: PkgSystemLock
.. autofunction:: PkgSystemUnLock
.. autofunction:: QuoteString
.. autofunction:: ReadConfigFile
.. autofunction:: ReadConfigFileISC
.. autofunction:: RewriteSection
.. autofunction:: SizeToStr
.. autofunction:: StringToBool
.. autofunction:: StrToTime
.. autofunction:: TimeRFC1123
.. autofunction:: TimeToStr
.. autofunction:: UpstreamVersion
.. autofunction:: URItoFileName
.. autofunction:: VersionCompare


Data
-----

.. data:: Config

    An :class:`Configuration()` object with the default configuration. Actually,
    this is a bit different object, but it is compatible.

.. data:: RewritePackageOrder

.. data:: RewriteSourceOrder


.. _CurStates:

Package States
^^^^^^^^^^^^^^^
.. data:: CurStateConfigFiles
.. data:: CurStateHalfConfigured
.. data:: CurStateHalfInstalled
.. data:: CurStateInstalled
.. data:: CurStateNotInstalled
.. data:: CurStateUnPacked




Dependency types
^^^^^^^^^^^^^^^^
.. data:: DepConflicts
.. data:: DepDepends
.. data:: DepObsoletes
.. data:: DepPreDepends
.. data:: DepRecommends
.. data:: DepReplaces
.. data:: DepSuggests

.. _InstStates:

Installed states
^^^^^^^^^^^^^^^^^
.. data:: InstStateHold
.. data:: InstStateHoldReInstReq
.. data:: InstStateOk
.. data:: InstStateReInstReq

.. _Priorities:

Priorities
^^^^^^^^^^
.. data:: PriExtra
.. data:: PriImportant
.. data:: PriOptional
.. data:: PriRequired
.. data:: PriStandard


.. _SelStates:

Select states
^^^^^^^^^^^^^^
.. data:: SelStateDeInstall
.. data:: SelStateHold
.. data:: SelStateInstall
.. data:: SelStatePurge
.. data:: SelStateUnknown


Build information
^^^^^^^^^^^^^^^^^
.. data:: Date
.. data:: LibVersion
.. data:: Time
.. data:: Version
