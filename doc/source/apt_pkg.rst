:mod:`apt_pkg` --- The low-level bindings for apt-pkg
=====================================================
.. module:: apt_pkg

The apt_pkg extensions provides a more low-level way to work with apt. It can
do everything apt can, and is written in C++. It has been in python-apt since
the beginning.


Module Initialization
---------------------

Initialization is needed for most functions, but not for all of them. Some can
be called without having run init*(), but will not return the expected value.

.. function:: initConfig

    Initialize the configuration of apt. This is needed for most operations.

.. function:: initSystem

    Initialize the system.

.. function:: init

    Deprecated function. Use initConfig() and initSystem() instead.

Working with the cache
----------------------
.. class:: Cache([progress])

    Return a :class:`Cache()` object. The optional parameter *progress*
    specifies an instance of :class:`apt.progress.OpProgress()` which will
    display the open progress.

    .. describe:: cache[pkgname]

        Return the :class:`Package()` object for the package name given by
        *pkgname*.

    .. method:: Close()

        Close the package cache.

    .. method:: Open([progress])

        Open the package cache again. The parameter *progress* may be set to
        an :class:`apt.progress.OpProgress()` object or `None`.

    .. method:: Update(progress, list)

        Update the package cache.

        The parameter *progress* points to an :class:`apt.progress.FetchProgress()`
        object. The parameter *list* refers to a :class:`SourceList()` object.

    .. attribute:: DependsCount

        The total number of dependencies.

    .. attribute:: PackageCount

        The total number of packages available in the cache.

    .. attribute:: ProvidesCount

        The number of provided packages.

    .. attribute:: VerFileCount

        .. todo:: Seems to be some mixture of versions and pkgFile.

    .. attribute:: VersionCount

        The total number of package versions available in the cache.

    .. attribute:: PackageFileCount

        The total number of Packages files available (the Packages files
        listing the packages). This is the same as the length of the list in
        the attribute :attr:`FileList`.

    .. attribute:: FileList

        A list of :class:`PackageFile` objects.

.. class:: DepCache(cache)

    Return a :class:`DepCache` object. The parameter *cache* specifies an
    instance of :class:`Cache`.

    The DepCache object contains various methods to manipulate the cache,
    to install packages, to remove them, and much more.

    .. method:: Commit(fprogress, iprogress)

        Apply all the changes made.

        The parameter *fprogress* has to be set to an instance of
        apt.progress.FetchProgress or one of its subclasses.

        The parameter *iprogress* has to be set to an instance of
        apt.progress.InstallProgress or one of its subclasses.

    .. method:: FixBroken()

        Try to fix all broken packages in the cache.

    .. method:: GetCandidateVer(pkg)

        Return the candidate version of the package, ie. the version that
        would be installed normally.

        The parameter *pkg* refers to an :class:`Package` object,
        available using the :class:`pkgCache`.

        This method returns a :class:`Version` object.

    .. method:: SetCandidateVer(pkg, version)

        The opposite of :meth:`pkgDepCache.GetCandidateVer`. Set the candidate
        version of the :class:`Package` *pkg* to the :class:`Version`
        *version*.


    .. method:: Upgrade([distUpgrade=False])

        Perform an upgrade. More detailed, this marks all the upgradable
        packages for upgrade. You still need to call
        :meth:`pkgDepCache.Commit` for the changes to apply.

        To perform a dist-upgrade, the optional parameter *distUpgrade* has
        to be set to True.

    .. method:: FixBroken()

        Fix broken packages.

    .. method:: ReadPinFile()

        Read the policy, eg. /etc/apt/preferences.

    .. method:: MinimizeUpgrade()

        Go over the entire set of packages and try to keep each package marked
        for upgrade. If a conflict is generated then the package is restored.

        .. todo::
            Explain better..

    .. method:: MarkKeep(pkg)

        Mark the :class:`Package` *pkg* for keep.

    .. method:: MarkDelete(pkg[, purge])

        Mark the :class:`Package` *pkg* for delete. If *purge* is True,
        the configuration files will be removed as well.

    .. method:: MarkInstall(pkg[, autoInst=True[, fromUser=True]])

        Mark the :class:`Package` *pkg* for install.

        If *autoInst* is ``True``, the dependencies of the package will be
        installed as well. This is the default.

        If *fromUser* is ``True``, the package will be marked as manually
        installed. This is the default.

    .. method:: SetReinstall(pkg)

        Set if the :class:`Package` *pkg* should be reinstalled.

    .. method:: IsUpgradable(pkg)

        Return ``1`` if the package is upgradable.

        The package can be upgraded by calling :meth:`pkgDepCache.MarkInstall`.

    .. method:: IsNowBroken(pkg)

        Return `1` if the package is broken now (including changes made, but
        not committed).

    .. method:: IsInstBroken(pkg)

        Return ``1`` if the package is broken on the current install. This
        takes changes which have not been committed not into effect.

    .. method:: IsGarbage(pkg)

        Return ``1`` if the package is garbage, ie. if it is automatically
        installed and no longer referenced by other packages.

    .. method:: IsAutoInstalled(pkg)

        Return ``1``  if the package is automatically installed (eg. as the
        dependency of another package).

    .. method:: MarkedInstall(pkg)

        Return ``1`` if the package is marked for install.

    .. method:: MarkedUpgrade(pkg)

        Return ``1`` if the package is marked for upgrade.

    .. method:: MarkedDelete(pkg)

        Return ``1`` if the package is marked for delete.

    .. method:: MarkedKeep(pkg)

        Return ``1`` if the package is marked for keep.

    .. method:: MarkedReinstall(pkg)

        Return ``1`` if the package should be installed.

    .. method:: MarkedDowngrade(pkg)

        Return ``1`` if the package should be downgraded.

    .. attribute:: KeepCount

        Integer, number of packages marked as keep

    .. attribute:: InstCount

        Integer, number of packages marked for installation.

    .. attribute:: DelCount

        Number of packages which should be removed.

    .. attribute:: BrokenCount

        Number of packages which are broken.

    .. attribute:: UsrSize

        The size required for the changes on the filesystem. If you install
        packages, this is positive, if you remove them its negative.

    .. attribute:: DebSize

        The size of the packages which are needed for the changes to be
        applied.


.. class:: PackageManager(depcache)

    Return a new :class:`PackageManager` object. The parameter *depcache*
    specifies a :class:`DepCache` object.

    :class:`PackageManager` objects provide several methods and attributes,
    which will be listed here:

    .. method:: GetArchives(fetcher, list, records)

        Add all the selected packages to the :class:`Acquire()` object
        *fetcher*.

        The parameter *list* refers to a :class:`SourceList()` object.

        The parameter *records* refers to a :class:`PackageRecords()` object.

    .. method:: DoInstall()

        Install the packages.

    .. method:: FixMissing

        Fix the installation if a package could not be downloaded.

    .. attribute:: ResultCompleted

        A constant for checking whether the the result is 'completed'.

        Compare it against the return value of :meth:`PkgManager.GetArchives`
        or :meth:`PkgManager.DoInstall`.

    .. attribute:: ResultFailed

        A constant for checking whether the the result is 'failed'.

        Compare it against the return value of :meth:`PkgManager.GetArchives`
        or :meth:`PkgManager.DoInstall`.

    .. attribute:: ResultIncomplete

        A constant for checking whether the the result is 'incomplete'.

        Compare it against the return value of :meth:`PkgManager.GetArchives`
        or :meth:`PkgManager.DoInstall`.

Improve performance with :class:`ActionGroup`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. class:: ActionGroup(depcache)

    Create a new :class:`ActionGroup()` object for the :class:`DepCache` object
    given by the parameter *depcache*.

    :class:`ActionGroup()` objects make operations on the cache faster by
    delaying certain cleanup operations until the action group is released.

    ActionGroup is also a context manager and therefore supports the
    :keyword:`with` statement. But because it becomes active as soon as it
    is created, you should not create an ActionGroup() object before entering
    the with statement.

    If you want to use ActionGroup as a with statement (which is recommended
    because it makes it easier to see when an actiongroup is active), always
    use the following form::

        with apt_pkg.ActionGroup(depcache):
            ...

    For code which has to run on Python versions prior to 2.5, you can also
    use the traditional way::

        actiongroup = apt_pkg.ActionGroup(depcache)
        ...
        actiongroup.release()

    :class:`ActionGroup` provides the following method:

    .. method:: release()

        Release the ActionGroup. This will reactive the collection of package
        garbage.

Resolving Dependencies
^^^^^^^^^^^^^^^^^^^^^^

.. class:: ProblemResolver(depcache)

    Return a new :class:`ProblemResolver` object. The parameter *depcache*
    specifies a :class:`pkgDepCache` object as returned by :func:`GetDepCache`.

    The problem resolver helps when there are problems in the package
    selection. An example is a package which conflicts with another, already
    installed package.

    .. method:: Protect(pkg)

        Protect the :class:`Package()` object given by the parameter *pkg*.

        .. todo::

            Really document it.

    .. method:: InstallProtect()

        Protect all installed packages from being removed.

    .. method:: Remove(pkg)

        Remove the :class:`Package()` object given by the parameter *pkg*.

        .. todo::

            Really document it.

    .. method:: Clear(pkg)

        Reset the :class:`Package()` *pkg* to the default state.

        .. todo::

            Really document it.

    .. method:: Resolve()

        Try to resolve problems by installing and removing packages.

    .. method:: ResolveByKeep()

        Try to resolve problems only by using keep.


:class:`PackageFile`
--------------------
.. class:: PackageFile

    A :class:`PackageFile` represents a Packages file, eg.
    /var/lib/dpkg/status.

    .. attribute:: Architecture

        The architecture of the package file.

    .. attribute:: Archive

        The archive (eg. unstable)

    .. attribute:: Component

        The component (eg. main)

    .. attribute:: FileName

        The name of the file.

    .. attribute:: ID

        The ID of the package. This is an integer which can be used to store
        further information about the file [eg. as dictionary key].

    .. attribute:: IndexType

        The sort of the index file. In normal cases, this is
        'Debian Package Index'.

    .. attribute:: Label

        The Label, as set in the Release file

    .. attribute:: NotAutomatic

        Whether packages from this list will be updated automatically. The
        default for eg. example is 0 (aka false).

    .. attribute:: NotSource

        Whether the file has no source from which it can be updated. In such a
        case, the value is 1; else 0. /var/lib/dpkg/status is 0 for example.

        Example::

            for pkgfile in cache.FileList:
                if pkgfile.NotSource:
                    print 'The file %s has no source.' % pkgfile.FileName

    .. attribute:: Origin

        The Origin, as set in the Release file

    .. attribute:: Site

        The hostname of the site.

    .. attribute:: Size

        The size of the file.

    .. attribute:: Version

        The version, as set in the release file (eg. "4.0" for "Etch")


Example
^^^^^^^
.. literalinclude:: examples/cache-pkgfile.py


:class:`Package`
----------------

.. class:: Package

    The pkgCache::Package objects are an interface to package specific
    features.


    Attributes:

    .. attribute:: CurrentVer

        The version currently installed, or None. This returns a
        :class:`Version` object.

    .. attribute:: ID

        The ID of the package. This can be used to store information about
        the package. The ID is an int value.

    .. attribute:: Name

        This is the name of the package.

    .. attribute:: ProvidesList

        A list of packages providing this package. More detailed, this is a
        list of tuples (str:pkgname, ????, :class:`Version`).

        If you want to check for check for virtual packages, the expression
        ``pkg.ProvidesList and not pkg.VersionList`` helps you. It detects if
        the package is provided by something else and is not available as a
        real package.

    .. attribute:: RevDependsList

        An iterator of :class:`Dependency` objects for dependencies on this
        package.

    .. attribute:: Section

        The section of the package, as specified in the record. The list of
        possible sections is defined in the Policy.

    .. attribute:: VersionList

        A list of :class:`Version` objects for all versions available in the
        cache.

    **States**:

    .. attribute:: SelectedState

        The state we want it to be, ie. if you mark a package for installation,
        this is :attr:`apt_pkg.SelStateInstall`.

        See :ref:`SelStates` for a list of available states.

    .. attribute:: InstState

        The state the currently installed version is in. This is normally
        :attr:`apt_pkg.InstStateOK`, unless the installation failed.

        See :ref:`InstStates` for a list of available states.

    .. attribute:: CurState

        The current state of the package (not installed, unpacked, installed,
        etc). See :ref:`CurStates` for a list of available states.

    **Flags**:

    .. attribute:: Auto

        Whether the package was installed automatically as a dependency of
        another package. (or marked otherwise as automatically installed)

    .. attribute:: Essential

        Whether the package is essential.

    .. attribute:: Important

        Whether the package is important.

Example:
^^^^^^^^^
.. literalinclude:: examples/cache-packages.py



:class:`Version`
----------------
.. class:: Version

    The version object contains all information related to a specific package
    version.

    .. attribute:: VerStr

        The version, as a string.

    .. attribute:: Section

        The usual sections (eg. admin, net, etc.). Prefixed with the component
        name for packages not in main (eg. non-free/admin).

    .. attribute:: Arch

        The architecture of the package, eg. amd64 or all.

    .. attribute:: FileList

        A list of (:class:`PackageFile`, int: index) tuples for all Package
        files containing this version of the package.

    .. attribute:: DependsListStr

        A dictionary of dependencies. The key specifies the type of the
        dependency ('Depends', 'Recommends', etc.).


        The value is a list, containing items which refer to the or-groups of
        dependencies. Each of these or-groups is itself a list, containing
        tuples like ('pkgname', 'version', 'relation') for each or-choice.

        An example return value for a package with a 'Depends: python (>= 2.4)'
        would be::

            {'Depends': [
                            [
                             ('python', '2.4', '>=')
                            ]
                        ]
            }

        The same for a dependency on A (>= 1) | B (>= 2)::

            {'Depends': [
                            [
                                ('A', '1', '>='),
                                ('B', '2', '>='),
                            ]
                        ]
            }

    .. attribute:: DependsList

        This is basically the same as :attr:`Version.DependsListStr`,
        but instead of the ('pkgname', 'version', 'relation') tuples,
        it returns :class:`Dependency` objects, which can assist you with
        useful functions.

    .. attribute:: ParentPkg

        The :class:`Package` object this version belongs to.

    .. attribute:: ProvidesList

        This returns a list of all packages provided by this version. Like
        :attr:`Package.ProvidesList`, it returns a list of tuples
        of the form ('virtualpkgname', ???, :class:`Version`), where as the
        last item is the same as the object itself.

    .. attribute:: Size

        The size of the .deb file, in bytes.

    .. attribute:: InstalledSize

        The size of the package (in kilobytes), when unpacked on the disk.

    .. attribute:: Hash

        An integer hash value.

    .. attribute:: ID

        An integer id.

    .. attribute:: Priority

        The integer representation of the priority. This can be used to speed
        up comparisons a lot, compared to :attr:`Version.PriorityStr`.

        The values are defined in the :mod:`apt_pkg` extension, see
        :ref:`Priorities` for more information.

    .. attribute:: PriorityStr

        Return the priority of the package version, as a string, eg.
        "optional".

    .. attribute:: Downloadable

        Whether this package can be downloaded from a remote site.

    .. attribute:: TranslatedDescription

        Return a :class:`Description` object.


:class:`Dependency`
-------------------
.. class:: Dependency

    Represent a dependency from one package to another one.

    .. method:: AllTargets

        A list of :class:`Version` objects which satisfy the dependency,
        and do not conflict with already installed ones.

        From my experience, if you use this method to select the target
        version, it is the best to select the last item unless any of the
        other candidates is already installed. This leads to results being
        very close to the normal package installation.

    .. method:: SmartTargetPkg

        Return a :class:`Version` object of a package which satisfies the
        dependency and does not conflict with installed packages
        (the 'natural target').

    .. attribute:: TargetVer

        The target version of the dependency, as string. Empty string if the
        dependency is not versioned.

    .. attribute:: TargetPkg

        The :class:`Package` object of the target package.

    .. attribute:: ParentVer

        The :class:`Version` object of the parent version, ie. the package
        which declares the dependency.

    .. attribute:: ParentPkg

        The :class:`Package` object of the package which declares the
        dependency. This is the same as using ParentVer.ParentPkg.

    .. attribute:: CompType

        The type of comparison (>=, ==, >>, <=), as string.

    .. attribute:: DepType

        The type of the dependency, as string, eg. "Depends".

    .. attribute:: ID

        The ID of the package, as integer.

Example: Find all missing dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
With the help of Dependency.AllTargets(), you can easily find all packages with
broken dependencies:

.. literalinclude:: examples/missing-deps.py


:class:`Description`
--------------------
.. class:: Description

    Represent the description of the package.

    .. attribute:: LanguageCode

        The language code of the description

    .. attribute:: md5

        The md5 hashsum of the description

    .. attribute:: FileList

        A list of tuples (:class:`PackageFile`, int: index).



:class:`MetaIndex`
------------------

.. todo::

    Complete them

.. class:: MetaIndex

    .. attribute:: URI
    .. attribute:: Dist
    .. attribute:: IsTrusted
    .. attribute:: IndexFiles


:class:`PackageIndexFile`
-------------------------

.. class:: PackageIndexFile

    .. method:: ArchiveURI(path)

        Return the full url to path in the archive.

    .. attribute:: Label

        Return the Label.

    .. attribute:: Exists

        Return whether the file exists.

    .. attribute:: HasPackages

        Return whether the file has packages.

    .. attribute:: Size

        Size of the file

    .. attribute:: IsTrusted

        Whether we can trust the file.


Records
--------

.. class:: PackageRecords(cache)

    Create a new :class:`PackageRecords` object, for the packages in the cache
    specified by the parameter *cache*.

    Provide access to the packages records. This provides very useful
    attributes for fast (convient) access to some fields of the record.

    .. method:: Lookup(verfile_iter)

        Change the actual package to the package given by the verfile_iter.

        The parameter *verfile_iter* refers to a tuple consisting
        of (:class:`PackageFile()`, int: index), as returned by various
        attributes, including :attr:`Version.FileList`.

        Example (shortened)::

            cand = depcache.GetCandidateVer(cache['python-apt'])
            records.Lookup(cand.FileList[0])
            # Now you can access the record
            print records.SourcePkg # == python-apt

    .. attribute:: FileName

        Return the field 'Filename' of the record. This is the path to the
        package, relative to the base path of the archive.

    .. attribute:: MD5Hash

        Return the MD5 hashsum of the package This refers to the field
        'MD5Sum' in the raw record.

    .. attribute:: SHA1Hash

        Return the SHA1 hashsum of the package. This refers to the field 'SHA1'
        in the raw record.

    .. attribute:: SHA256Hash

        Return the SHA256 hashsum of the package. This refers to the field
        'SHA256' in the raw record.

        .. versionadded:: 0.7.9

    .. attribute:: SourcePkg

        Return the source package.

    .. attribute:: SourceVer

        Return the source version.

    .. attribute:: Maintainer

        Return the maintainer of the package.

    .. attribute:: ShortDesc

        Return the short description. This is the summary on the first line of
        the 'Description' field.

    .. attribute:: LongDesc

        Return the long description. These are lines 2-END from the
        'Description' field.

    .. attribute:: Name

        Return the name of the package. This is the 'Package' field.

    .. attribute:: Homepage

        Return the Homepage. This is the 'Homepage' field.

    .. attribute:: Record

        Return the whole record as a string. If you want to access fields of
        the record not available as an attribute, you can use
        :func:`apt_pkg.ParseSection` to parse the record and access the field
        name.

        Example::

            section = apt_pkg.ParseSection(records.Record)
            print section['SHA256']


.. class:: SourceRecords

    This represents the entries in the Sources files, ie. the dsc files of
    the source packages.

    .. note::

        If the Lookup failed, because no package could be found, no error is
        raised. Instead, the attributes listed below are simply not existing
        anymore (same applies when no Lookup has been made, or when it has
        been restarted).

    .. method:: Lookup(pkgname)

        Lookup the record for the package named *pkgname*. To access all
        available records, you need to call it multiple times.

        Imagine a package P with two versions X, Y. The first ``Lookup(P)``
        would set the record to version X and the second ``Lookup(P)`` to
        version Y.

    .. method:: Restart()

        Restart the lookup.

        Imagine a package P with two versions X, Y. The first ``Lookup(P)``
        would set the record to version X and the second ``Lookup(P)`` to
        version Y.

        If you now call ``Restart()``, the internal position will be cleared.
        Now you can call ``Lookup(P)`` again to move to X.

    .. attribute:: Package

        The name of the source package.

    .. attribute:: Version

        A string describing the version of the source package.

    .. attribute:: Maintainer

        A string describing the name of the maintainer.

    .. attribute:: Section

        A string describing the section.

    .. attribute:: Record

        The whole record, as a string. You can use :func:`apt_pkg.ParseSection`
        if you need to parse it.

        You need to parse the record if you want to access fields not available
        via the attributes, eg. 'Standards-Version'

    .. attribute:: Binaries

        Return a list of strings describing the package names of the binaries
        created by the source package. This matches the 'Binary' field in the
        raw record.

    .. attribute:: Index

        The index in the Sources files.

    .. attribute:: Files

        The list of files. This returns a list of tuples with the contents
        ``(str: md5, int: size, str: path, str:type)``.

    .. attribute:: BuildDepends

        Return the list of Build dependencies, as
        ``(str: package, str: version, int: op, int: type)``.

        .. table:: Values of *op*

            ===== =============================================
            Value      Meaning
            ===== =============================================
            0x0   No Operation (no versioned build dependency)
            0x10  | (or) - this will be added to the other values
            0x1   <= (less than or equal)
            0x2   >= (greater than or equal)
            0x3   << (less than)
            0x4   >> (greater than)
            0x5   == (equal)
            0x6   != (not equal)
            ===== =============================================

        .. table:: Values of *type*

            ===== ===================
            Value Meaning
            ===== ===================
            0     Build-Depends
            1     Build-Depends-Indep
            2     Build-Conflicts
            3     Build-Conflicts-Indep
            ===== ===================

        **Example**: In the following content, we will imagine a
        build-dependency::

            Build-Depends: A (>= 1) | B (>= 1), C

        This results in::

            [('A', '1', 18, 0), # 18 = 16 + 2 = 0x10 + 0x2
             ('B', '1', 2, 0),
             ('C', '', 0, 0)]

        This is **not** the same as returned by
        :func:`apt_pkg.ParseSrcDepends`.



The Acquire interface
----------------------
The Acquire Interface is responsible for all sorts of downloading in apt. All
packages, index files, etc. downloading is done using the Acquire functionality.

The :mod:`apt_pkg` module provides a subset of this functionality which allows
you to implement file downloading in your applications. Together with the
:class:`PackageManager` class you can also fetch all the packages marked for
installation.


.. class:: Acquire([progress])

    Return an :class:`Acquire` object. The parameter *progress* refers to
    an :class:`apt.progress.FetchProgress()` object.

    Acquire objects maintaing a list of items which will be fetched or have
    been fetched already during the lifetime of this object. To add new items
    to this list, you can create new :class:`AcquireFile` objects which allow
    you to add single files.

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

.. class:: AcquireItem

    The :class:`AcquireItem()` objects represent the items of a
    :class:`Acquire` object. :class:`AcquireItem()` objects can not be created
    by the user, they are solely available through the :attr:`Acquire.Items`
    list of an :class:`Acquire` object.

    .. attribute:: ID

        The ID of the item.

    .. attribute:: Complete

        Is the item completely acquired?

    .. attribute:: Local

        Is the item a local file?

    .. attribute:: IsTrusted

        Can the file be trusted?

    .. attribute:: FileSize

        The size of the file, in bytes.

    .. attribute:: ErrorText

        The error message. For example, when a file does not exist on a http
        server, this will contain a 404 error message.

    .. attribute:: DestFile

        The location the file is saved as.

    .. attribute:: DescURI

        The source location.

    **Status**:

    .. attribute:: Status

        Integer, representing the status of the item.

    .. attribute:: StatIdle

        Constant for comparing :attr:`AcquireItem.Status`.

    .. attribute:: StatFetching

        Constant for comparing :attr:`AcquireItem.Status`

    .. attribute:: StatDone

        Constant for comparing :attr:`AcquireItem.Status`

    .. attribute:: StatError

        Constant for comparing :attr:`AcquireItem.Status`

    .. attribute:: StatAuthError

        Constant for comparing :attr:`AcquireItem.Status`


.. class:: AcquireFile(owner, uri[, md5, size, descr, shortdescr, destdir, destfile])

    Create a new :class:`AcquireFile()` object and register it with *acquire*,
    so it will be fetched. AcquireFile objects provide no methods or attributes
    and are completely useless at the moment.

    The parameter *owner* refers to an :class:`Acquire()` object as returned
    by :func:`GetAcquire`. The file will be added to the Acquire queue
    automatically.

    The parameter *uri* refers to the location of the file, any protocol
    of apt is supported.

    The parameter *md5* refers to the md5sum of the file. This can be used
    for checking the file.

    The parameter *size* can be used to specify the size of the package,
    which can then be used to calculate the progress and validate the download.

    The parameter *descr* is a descripition of the download. It may be
    used to describe the item in the progress class. *shortDescr* is the
    short form of it.

    You can use *destdir* to manipulate the directory where the file will
    be saved in. Instead of *destdir*, you can also specify the full path to
    the file using the parameter *destfile*. You can not combine both.






Hash functions
--------------
The apt_pkg module also provides several hash functions. If you develop
applications with python-apt it is often easier to use these functions instead
of the ones provides in Python's :mod:`hashlib` module.

.. function:: md5sum(object)

    Return the md5sum of the object. *object* may either be a string, in
    which case the md5sum of the string is returned, or a :class:`file()`
    object (or a file descriptor), in which case the md5sum of its contents is
    returned.

    .. versionchanged:: 0.8.0
        Added support for using file descriptors.

.. function:: sha1sum(object)

    Return the sha1sum of the object. *object* may either be a string, in
    which case the sha1sum of the string is returned, or a :class:`file()`
    object (or a file descriptor), in which case the sha1sum of its contents
    is returned.

    .. versionchanged:: 0.8.0
        Added support for using file descriptors.

.. function:: sha256sum(object)

    Return the sha256sum of the object. *object* may either be a string, in
    which case the sha256sum of the string is returned, or a :class:`file()`
    object  (or a file descriptor), in which case the sha256sum of its contents
    is returned.

    .. versionchanged:: 0.8.0
        Added support for using file descriptors.

Debian control files
--------------------
Debian control files are files containing multiple stanzas of :RFC:`822`-style
header sections. They are widely used in the Debian community, and can represent
many kinds of information. One example for such a file is the
:file:`/var/lib/dpkg/status` file which contains a list of the currently
installed packages.

The :mod:`apt_pkg` module provides two classes to read those files and parts
thereof and provides a function :func:`RewriteSection` which takes a
:class:`TagSection()` object and sorting information and outputs a sorted
section as a string.

.. class:: TagFile(file)

    An object which represents a typical debian control file. Can be used for
    Packages, Sources, control, Release, etc.

    An example for working with a TagFile could look like::

        tagf = apt_pkg.TagFile(open('/var/lib/dpkg/status'))
        tagf.Step()
        print tagf.Section['Package']

    .. method:: Step

        Step forward to the next section. This simply returns ``1`` if OK, and
        ``0`` if there is no section

    .. method:: Offset

        Return the current offset (in bytes) from the beginning of the file.

    .. method:: Jump(offset)

        Jump back/forward to *offset*. Use ``Jump(0)`` to jump to the
        beginning of the file again.

    .. attribute:: Section

        This is the current :class:`TagSection()` instance.

.. class:: TagSection(text)

    Represent a single section of a debian control file.

    .. describe:: section[key]

        Return the value of the field at *key*. If *key* is not available,
        raise :exc:`KeyError`.

    .. describe:: key in section

        Return ``True`` if *section* has a key *key*, else ``False``.

      .. versionadded:: 0.8.0

    .. method:: Bytes

        The number of bytes in the section.

    .. method:: Find(key, default='')

        Return the value of the field at the key *key* if available,
        else return *default*.

    .. method:: FindFlag(key)

        Find a yes/no value for the key *key*. An example for such a
        field is 'Essential'.

    .. method:: get(key, default='')

        Return the value of the field at the key *key* if available, else
        return *default*.

    .. method:: has_key(key)

        Check whether the field with named by *key* exists.

        .. deprecated:: 0.8.0

    .. method:: keys()

        Return a list of keys in the section.

.. autofunction:: RewriteSection(section, order, rewrite_list)

.. data:: RewritePackageOrder

    The order in which the information for binary packages should be rewritten,
    i.e. the order in which the fields should appear.

.. data:: RewriteSourceOrder

    The order in which the information for source packages should be rewritten,
    i.e. the order in which the fields should appear.

Dependencies
------------
.. function:: CheckDep(pkgver, op, depver)

    Check that the dependency requirements consisting of op and depver can be
    satisfied by the version pkgver.

    Example::

        >>> bool(apt_pkg.CheckDep("1.0", ">=", "1"))
        True

.. function:: ParseDepends(depends)

    Parse the string *depends* which contains dependency information as
    specified in Debian Policy, Section 7.1.

    Returns a list. The members of this list are lists themselves and contain
    one or more tuples in the format ``(package,version,operation)`` for every
    'or'-option given, e.g.::

        >>> apt_pkg.ParseDepends("PkgA (>= VerA) | PkgB (>= VerB)")
        [[('PkgA', 'VerA', '>='), ('PkgB', 'VerB', '>=')]]

.. function:: ParseSrcDepends(depends)

    Parse the string *depends* which contains dependency information as
    specified in Debian Policy, Section 7.1.

    Returns a list. The members of this list are lists themselves and contain
    one or more tuples in the format ``(package,version,operation)`` for every
    'or'-option given, e.g.::

        >>> apt_pkg.ParseDepends("PkgA (>= VerA) | PkgB (>= VerB)")
        [[('PkgA', 'VerA', '>='), ('PkgB', 'VerB', '>=')]]


    Furthemore, this function also supports to limit the architectures, as
    used in e.g. Build-Depends::

        >>> apt_pkg.ParseSrcDepends("a (>= 01) [i386 amd64]")
        [[('a', '01', '>=')]]


Configuration
-------------

.. class:: Configuration()

    Configuration() objects store the configuration of apt, mostly created from
    the contents of :file:`/etc/apt.conf` and the files in
    :file:`/etc/apt.conf.d`.

    .. describe:: key in conf

      Return ``True`` if *conf* has a key *key*, else ``False``.

      .. versionadded:: 0.8.0

    .. describe:: conf[key]

        Return the value of the option given key *key*. If it does not
        exist, raise :exc:`KeyError`.

    .. describe:: conf[key] = value

        Set the option at *key* to *value*.

    .. method:: Find(key[, default=''])

        Return the value for the given key *key*. This is the same as
        :meth:`Configuration.get`.

        If *key* does not exist, return *default*.

    .. method:: FindFile(key[, default=''])

        Return the filename hold by the configuration at *key*. This formats the
        filename correctly and supports the Dir:: stuff in the configuration.

        If *key* does not exist, return *default*.

    .. method:: FindDir(key[, default='/'])

        Return the absolute path to the directory specified in *key*. A
        trailing slash is appended.

        If *key* does not exist, return *default*.

    .. method:: FindI(key[, default=0])

        Return the integer value stored at *key*.

        If *key* does not exist, return *default*.

    .. method:: FindB(key[, default=0])

        Return the boolean value stored at *key*. This returns an integer, but
        it should be treated like True/False.

        If *key* does not exist, return *default*.

    .. method:: Set(key, value)

        Set the value of *key* to *value*.

    .. method:: Exists(key)

        Check whether the key *key* exists in the configuration.

    .. method:: SubTree(key)

        Return a sub tree starting at *key*. The resulting object can be used
        like this one.

    .. method:: List([key])

        List all items at *key*. Normally, return the keys at the top level,
        eg. APT, Dir, etc.

        Use *key* to specify a key of which the childs will be returned.

    .. method:: ValueList([key])

        Same as :meth:`Configuration.List`, but this time for the values.

    .. method:: MyTag()

        Return the tag name of the current tree. Normally this is an empty
        string, but for subtrees it is the key of the subtree.

    .. method:: Clear(key)

        Clear the configuration. Remove all values and keys at *key*.

    .. method:: keys([key])

        Return all the keys, recursive. If *key* is specified, ... (FIXME)

    .. method:: has_key(key)

        Return whether the configuration contains the key *key*.

        .. deprecated:: 0.8.0

    .. method:: get(key[, default=''])

        This behaves just like :meth:`dict.get` and :meth:`Configuration.Find`,
        it returns the value of key or if it does not exist, *default*.

.. class:: ConfigurationPtr

    Behaves like a :class:`Configuration()` objects, but uses a pointer to the
    underlying C++ object. This is used for the default configuration in the
    :data:`Config` attribute of the module.

.. class:: ConfigurationSub

    Behaves like a :class:`Configuration()` objects, but provides access to
    a subsection of another Configuration-like object. This type of object is
    returned by the :meth:`Configuration.SubTree()` method.

.. data:: Config

    A :class:`ConfigurationPtr()` object with the default configuration. This
    object is initialized by calling :func:`InitConfig`.


Modifying
^^^^^^^^^


.. function:: ReadConfigFile(configuration, filename)

    Read the configuration file specified by the parameter *filename* and add
    the settings therein to the :class:`Configuration()` object specified by
    the parameter *configuration*

.. function:: ReadConfigDir(configuration, dirname)

    Read configuration files in the directory specified by the parameter
    *dirname* and add the settings therein to the :class:`Configuration()`
    object specified by the parameter *configuration*.

.. function:: ReadConfigFileISC(configuration, filename)

    Read the configuration file specified by the parameter *filename* and add
    the settings therein to the :class:`Configuration()` object specified by
    the parameter *configuration*

.. function:: ParseCommandLine(configuration,options,argv)

    This function is like getopt except it manipulates a configuration space.
    output is a list of non-option arguments (filenames, etc). *options* is a
    list of tuples of the form ``(‘c’,”long-opt or None”,
    ”Configuration::Variable”,”optional type”)``.

    Where ``type`` may be one of HasArg, IntLevel, Boolean, InvBoolean,
    ConfigFile, or ArbItem. The default is Boolean.

Locking
--------

.. function:: GetLock(filename)

    Create an empty file at the path specified by the parameter *filename* and
    lock it.

    While the file is locked by a process, calling this function in another
    process returns ``-1``.

    When the lock is not required anymore, the file descriptor should be closed
    using :func:`os.close`.

.. function:: PkgSystemLock()

    Lock the global pkgsystem.

.. function:: PkgSystemUnLock()

    Unlock the global pkgsystem.

Other classes
--------------
.. class:: Cdrom()

    Return a Cdrom object with the following methods:

    .. method:: Ident(progress)

        Identify the cdrom. The parameter *progress* refers to an
        :class:`apt.progress.CdromProgress()` object.

    .. method:: Add(progress)

        Add the cdrom to the sources.list file. The parameter *progress*
        refers to an :class:`apt.progress.CdromProgress()` object.

.. class:: SourceList

    This is for :file:`/etc/apt/sources.list`.

    .. method:: FindIndex(pkgfile)

        Return a :class:`PackageIndexFile` object for the :class:`PackageFile`
        *pkgfile*.

    .. method:: ReadMainList

        Read the main list.

    .. method:: GetIndexes(acq[, all])

        Add the index files to the :class:`Acquire()` object *acq*. If *all* is
        given and ``True``, all files are fetched.

String functions
----------------
.. function:: Base64Encode(string)

    Encode the given string using base64, e.g::

        >>> apt_pkg.Base64Encode(u"A")
        'QQ=='


.. function:: CheckDomainList(host, list)

    See if Host is in a ',' seperated list, e.g.::

        apt_pkg.CheckDomainList("alioth.debian.org","debian.net,debian.org")

.. function:: DeQuoteString(string)

    Dequote the string specified by the parameter *string*, e.g.::

        >>> apt_pkg.DeQuoteString("%61%70%74%20is%20cool")
        'apt is cool'

.. function:: QuoteString(string, repl)

    For every character listed in the string *repl*, replace all occurences in
    the string *string* with the correct HTTP encoded value:

        >>> apt_pkg.QuoteString("apt is cool","apt")
        '%61%70%74%20is%20cool'

.. function:: SizeToStr(size)

    Return a string presenting the human-readable version of the integer
    *size*. When calculating the units (k,M,G,etc.) the size is divided by the
    factor 1000.

    Example::

        >>> apt_pkg.SizeToStr(10000)
        '10.0k'

.. function:: StringToBool(input)

    Parse the string *input* and return one of **-1**, **0**, **1**.

    .. table:: Return values

        ===== =============================================
        Value      Meaning
        ===== =============================================
         -1   The string *input* is not recognized.
          0   The string *input* evaluates to **False**.
         +1   The string *input* evaluates to **True**.
        ===== =============================================

    Example::

        >>> apt_pkg.StringToBool("yes")
        1
        >>> apt_pkg.StringToBool("no")
        0
        >>> apt_pkg.StringToBool("not-recognized")
        -1

.. function:: StrToTime(rfc_time)

    Convert the :rfc:`1123` conforming string *rfc_time* to the unix time, and
    return the integer. This is the opposite of :func:`TimeRFC1123`.

    Example::

        >> apt_pkg.StrToTime('Thu, 01 Jan 1970 00:00:00 GMT')
        0

.. function:: TimeRFC1123(seconds)

    Format the unix time specified by the integer *seconds*, according to the
    requirements of :rfc:`1123`.

    Example::

        >>> apt_pkg.TimeRFC1123(0)
        'Thu, 01 Jan 1970 00:00:00 GMT'


.. function:: TimeToStr(seconds)

    Format a given duration in a human-readable manner. The parameter *seconds*
    refers to a number of seconds, given as an integer. The return value is a
    string with a unit like 's' for seconds.

    Example::

        >>> apt_pkg.TimeToStr(3601)
        '1h0min1s'

.. function:: UpstreamVersion(version)

    Return the string *version*, eliminating everything following the last
    '-'. Thus, this should be equivalent to ``version.rsplit('-', 1)[0]``.

.. function:: URItoFileName(uri)

    Take a string *uri* as parameter and return a filename which can be used to
    store the file, based on the URI.

    Example::

        >>> apt_pkg.URItoFileName('http://debian.org/index.html')
        'debian.org_index.html'


.. function:: VersionCompare(a, b)

    Compare two versions, *a* and *b*, and return an integer value which has
    the same characteristic as the built-in :func:`cmp` function.

    .. table:: Return values

        ===== =============================================
        Value      Meaning
        ===== =============================================
        > 0   The version *a* is greater than version *b*.
        = 0   Both versions are equal.
        < 0   The version *a* is less than version *b*.
        ===== =============================================




Module Constants
----------------
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
^^^^^^^^^^^^^^^^
.. data:: InstStateHold
.. data:: InstStateHoldReInstReq
.. data:: InstStateOk
.. data:: InstStateReInstReq

.. _Priorities:

Priorities
^^^^^^^^^^^
.. data:: PriExtra
.. data:: PriImportant
.. data:: PriOptional
.. data:: PriRequired
.. data:: PriStandard


.. _SelStates:

Select states
^^^^^^^^^^^^^
.. data:: SelStateDeInstall
.. data:: SelStateHold
.. data:: SelStateInstall
.. data:: SelStatePurge
.. data:: SelStateUnknown


Build information
^^^^^^^^^^^^^^^^^
.. data:: Date

    The date on which this extension has been compiled.

.. data:: LibVersion

    The version of the apt_pkg library. This is **not** the version of apt,
    nor the version of python-apt.

.. data:: Time

    The time this extension has been built.

.. data:: Version

    The version of apt (not of python-apt).

.. data:: _COMPAT_0_7

    A more or less internal variable defining whether this build provides an
    API which is compatible to the one of python-apt 0.7. This is used in the
    apt and aptsources packages to decide whether compatibility should be
    enabled or not.
