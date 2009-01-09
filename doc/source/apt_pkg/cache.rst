Low-Level Cache Handling
===========================

.. class:: Acquire

    .. method:: Run()

        Fetch all the items which have been added by
        :func:`apt_pkg.GetPkgAcqFile`.

    .. method:: Shutdown

        Shut the fetcher down.

.. class:: pkgCache

    The :class:`pkgCache` class prov

    .. method:: Close()

        Close the package cache.

    .. method:: Open([progress])

        Open the package cache again. The parameter ``progress`` may be set to
        an :class:`apt.progress.OpProgress()` object or `None`.

    .. method:: Update(progress, list)

        Update the package cache.

        The parameter ``progress`` points to an :class:`apt.progress.FetchProgress()`
        object.

        The parameter ``list`` refers to an object as returned by
        :func:`apt_pkg.GetPkgSourceList`.

    .. method:: __getitem__(item)

        Return an :class:`pkgCachePackage` object for the package with the given
        name.

.. class:: pkgCachePackage

    The pkgCache::Package objects are an interface to package specific
    features.


    Attributes:

    .. attribute:: Name

        This is the name of the package.

    .. attribute:: Section

        The section of the package, as specified in the record. The list of
        possible sections is defined in the Policy.

    .. attribute:: ID

        The ID of the package. This can be used to store information about
        the package. The ID is an int value.


Working with dependencies
-------------------------
.. class:: pkgDepCache

    The pkgDepCache object contains various methods to manipulate the cache,
    to install packages, to remove them, and much more.

    .. method:: Commit(fprogress, iprogress)

        Apply all the changes made.

        The parameter ``fprogress`` has to be set to an instance of
        apt.progress.FetchProgress or one of its subclasses.

        The parameter ``iprogress`` has to be set to an instance of
        apt.progress.InstallProgress or one of its subclasses.

    .. method:: FixBroken()

        Try to fix all broken packages in the cache.

    .. method:: GetCandidateVer(pkg)

        Return the candidate version of the package, ie. the version that
        would be installed normally.

        The parameter ``pkg`` refers to an :class:`pkgCachePackage` object,
        available using the :class:`pkgCache`.

        This method returns a :class:`pkgCacheVersion` object.
