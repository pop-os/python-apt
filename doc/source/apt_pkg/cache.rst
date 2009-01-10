Classes in apt_pkg
==================

.. todo::

    This should be split and cleaned up a bit.


.. class:: Acquire

    .. method:: Run()

        Fetch all the items which have been added by
        :func:`apt_pkg.GetPkgAcqFile`.

    .. method:: Shutdown

        Shut the fetcher down.

.. class:: PkgAcqFile

    This class provides no methods or attributes

.. class:: AcquireItem

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

ActionGroup --- brings eg. big speedup
--------------------------------------

.. class:: ActionGroup

    Normally, apt checkes the package cache after every modification for
    packages which are automatically installed but on which no package depends
    anymore (it collects the package garbage).

    Using ActionGroups you can turn this off and therefore make your code
    much faster.

    Initialize it using :func:`apt_pkg.GetPkgActionGroup`, eg:

    .. code-block: python

        apt_pkg.GetPkgActionGroup(depcache)

    .. method:: release

        Release the ActionGroup. This will reactive the collection of package
        garbage.


Configuration
--------------

.. class:: Configuration

    The Configuration objects store the configuration of apt.

    .. method:: Find(key[, default=''])

        Return the value for the given key. This is the same as
        :meth:`Configuration.get`.

        If ``key`` does not exist, return ``default``.

    .. method:: FindFile(key[, default=''])

        Return the filename hold by the configuration at key. This formats the
        filename correctly and supports the Dir:: stuff in the configuration.

        If ``key`` does not exist, return ``default``.

    .. method:: FindDir(key[, default='/'])

        Return the absolute path to the directory specified in key. A trailing
        slash is appended.

        If ``key`` does not exist, return ``default``.

    .. method:: FindI(key[, default=0])

        Return the integer value stored at key.

        If ``key`` does not exist, return ``default``.

    .. method:: FindB(key[, default=0])

        Return the boolean value stored at key. This returns an integer, but
        it should be treated like True/False.

        If ``key`` does not exist, return ``default``.

    .. method:: Set(key, value)

        Set the value of ``key`` to ``value``.

    .. method:: Exists(key)

        Check whether the given key exists in the configuration.

    .. method:: SubTree(key)

        Return a sub tree starting at key. The resulting object can be used
        like this one.

    .. method:: List([key])

        List all items at ``key``. Normally, return the keys at the top level,
        eg. APT, Dir, etc.

        Use ``key`` to specify a key of which the childs will be returned.

    .. method:: ValueList([key])

        Same as :meth:`Configuration.List`, but this time for the values.

    .. method:: MyTag()

        Return the tag name of the current tree. Normally this is an empty
        string, but for subtrees it is the key of the subtree.

    .. method:: Clear(key)

        Clear the configuration. Remove all values and keys at ``key``.

    .. method:: keys([key])

        Return all the keys, recursive. If ``key`` is specified, ... (FIXME)

    .. method:: has_key(key)

        Return whether the configuration contains the key ``key``.

    .. method:: get(key[, default=''])

        This behaves just like :meth:`dict.get` and :meth:`Configuration.Find`,
        it returns the value of key or if it does not exist, ``default``.

The cache
---------
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

        Return an :class:`Package` object for the package with the given
        name.

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

    .. attribute::  PackageFileCount

        The total number of Packages files available (the Packages files
        listing the packages). This is the same as the length of the list in
        the attribute :attr:`FileList`.

    .. attribute:: FileList

        A list of :class:`PackageFile` objects.


PackageFile
------------
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

        Example:

        .. code-block:: python

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
.. literalinclude:: ../examples/cache-pkgfile.py


A Package
---------

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
.. literalinclude:: ../examples/cache-packages.py



Version, as returned by eg. :meth:`pkgDepCache.GetCandidateVer`
---------------------------------------------------------------
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
        would be:

        .. code-block:: python

            {'Depends': [
                            [
                             ('python', '2.4', '>=')
                            ]
                        ]
            }

        The same for a dependency on A (>= 1) | B (>= 2):

        .. code-block:: python

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


The Dependency class
--------------------
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

.. literalinclude:: ../examples/missing-deps.py


The Description class
---------------------
.. class:: Description

    Represent the description of the package.

    .. attribute:: LanguageCode

        The language code of the description

    .. attribute:: md5

        The md5 hashsum of the description

    .. attribute:: FileList

        A list of tuples (:class:`PackageFile`, int: index).



The pkgDepCache wrapper
-----------------------
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

        The parameter ``pkg`` refers to an :class:`Package` object,
        available using the :class:`pkgCache`.

        This method returns a :class:`Version` object.

    .. method:: SetCandidateVer(pkg, version)

        The opposite of :meth:`pkgDepCache.GetCandidateVer`. Set the candidate
        version of the :class:`Package` ``pkg`` to the :class:`Version`
        ``version``.


    .. method:: Upgrade([distUpgrade=False])

        Perform an upgrade. More detailed, this marks all the upgradable
        packages for upgrade. You still need to call
        :meth:`pkgDepCache.Commit` for the changes to apply.

        To perform a dist-upgrade, the optional parameter ``distUpgrade`` has
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

        Mark the :class:`Package` ``pkg`` for keep.

    .. method:: MarkDelete(pkg[, purge])

        Mark the :class:`Package` ``pkg`` for delete. If ``purge`` is True,
        the configuration files will be removed as well.

    .. method:: MarkInstall(pkg[, autoInst=True[, fromUser=True]])

        Mark the :class:`Package` ``pkg`` for install.

        If ``autoInst`` is True, the dependencies of the package will be
        installed as well. This is the default.

        If ``fromUser`` is True, the package will be marked as manually
        installed. This is the default.

    .. method:: SetReinstall(pkg)

        Set if the :class:`Package` ``pkg`` should be reinstalled.

    .. method:: IsUpgradable(pkg)

        Return `1` if the package is upgradable.

        The package can be upgraded by calling :meth:`pkgDepCache.MarkInstall`.

    .. method:: IsNowBroken(pkg)

        Return `1` if the package is broken now (including changes made, but
        not committed).

    .. method:: IsInstBroken(pkg)

        Return `1` if the package is broken on the current install. This takes
        changes which have not been committed not into effect.

    .. method:: IsGarbage(pkg)

        Return `1` if the package is garbage, ie. if it is automatically
        installed and no longer referenced by other packages.

    .. method:: IsAutoInstalled(pkg)

        Return `1`  if the package is automatically installed (eg. as the
        dependency of another package).

    .. method:: MarkedInstall(pkg)

        Return `1` if the package is marked for install.

    .. method:: MarkedUpgrade(pkg)

        Return `1` if the package is marked for upgrade.

    .. method:: MarkedDelete(pkg)

        Return `1` if the package is marked for delete.

    .. method:: MarkedKeep(pkg)

        Return `1` if the package is marked for keep.

    .. method:: MarkedReinstall(pkg)

        Return `1` if the package should be installed.

    .. method:: MarkedDowngrade(pkg)

        Return `1` if the package should be downgraded.

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
