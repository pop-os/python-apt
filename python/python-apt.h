/*
 * python-apt.h - Header file for the public interface.
 *
 * Copyright 2009-2010 Julian Andres Klode <jak@debian.org>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
 * MA 02110-1301, USA.
 */

#ifndef PYTHON_APT_H
#define PYTHON_APT_H
#include <Python.h>
#include "generic.h"
#include <apt-pkg/configuration.h>
#include <apt-pkg/acquire-item.h>
#include <apt-pkg/packagemanager.h>
#include <apt-pkg/version.h>
#include <apt-pkg/deblistparser.h>
#include <apt-pkg/pkgcache.h>
#include <apt-pkg/cachefile.h>
#include <apt-pkg/tagfile.h>
#include <apt-pkg/init.h>
#include <apt-pkg/pkgsystem.h>
#include <apt-pkg/cdrom.h>
#include <apt-pkg/algorithms.h>
#include <apt-pkg/hashes.h>

typedef PyObject *ActionGroupF(pkgDepCache::ActionGroup *);
typedef pkgDepCache::ActionGroup*& ActionGroupT(PyObject *self);

struct _PyAptPkgAPIStruct {
    // apt_pkg.Acquire (pkgAcquire*)
    PyTypeObject *acquire_type;
    PyObject*    (*acquire_fromcpp)(pkgAcquire *acquire, bool Delete);
    pkgAcquire*& (*acquire_tocpp)(PyObject *self);
    // apt_pkg.AcquireFile
    PyTypeObject *acquirefile_type;
    pkgAcqFile*& (*acquirefile_tocpp)(PyObject *self);
    // apt_pkg.AcquireItem
    PyTypeObject *acquireitem_type;
    pkgAcquire::Item*& (*acquireitem_tocpp)(PyObject *self);
    // apt_pkg.AcquireItemDesc
    PyTypeObject *acquireitemdesc_type;
    pkgAcquire::ItemDesc*& (*acquireitemdesc_tocpp)(PyObject *self);
    
    PyTypeObject *acquireworker_type;
    pkgAcquire::Worker*& (*acquireworker_tocpp)(PyObject *self);
    
    PyTypeObject *actiongroup_type;
    pkgDepCache::ActionGroup*& (*actiongroup_tocpp)(PyObject *self);
    
    PyTypeObject *cache_type;
    pkgCache*& (*cache_tocpp)(PyObject *self);
    
    PyTypeObject *cachefile_type;
    pkgCacheFile*& (*cachefile_tocpp)(PyObject *self);
    
    PyTypeObject *cdrom_type;
    pkgCdrom&   (*cdrom_tocpp)(PyObject *self);
    
    PyTypeObject *configuration_type;
    Configuration*& (*configuration_tocpp)(PyObject *self);
    
    PyTypeObject *depcache_type;
    pkgDepCache*& (*depcache_tocpp)(PyObject *self);
    
    PyTypeObject *dependency_type;
    pkgCache::DepIterator& (*dependency_tocpp)(PyObject *self);
    
    PyTypeObject *dependencylist_type;
    void *dependencylist_tocpp; // FIXME: need packagelist_tocpp
    
    PyTypeObject *description_type;
    pkgCache::DescIterator& (*description_tocpp)(PyObject *self);
    
    PyTypeObject *hashes_type;
    Hashes& (*hashes_tocpp)(PyObject *self);
    
    PyTypeObject *hashstring_type;
    HashString*& (*hashstring_tocpp)(PyObject *self);
    
    PyTypeObject *indexrecords_type;
    indexRecords*& (*indexrecords_tocpp)(PyObject *self);
    
    PyTypeObject *metaindex_type;
    metaIndex*& (*metaindex_tocpp)(PyObject *self);

    PyTypeObject *package_type;
    pkgCache::PkgIterator& (*package_tocpp)(PyObject *self);
    
    PyTypeObject *packagefile_type;
    pkgCache::PkgFileIterator& (*packagefile_tocpp)(PyObject *self);

    PyTypeObject *packageindexfile_type;
    pkgIndexFile*& (*packageindexfile_tocpp)(PyObject *self);
    
    PyTypeObject *packagelist_type;
    void *packagelist_tocpp;     // FIXME: need packagelist_tocpp
    
    PyTypeObject *packagemanager_type;
    pkgPackageManager*& (*packagemanager_tocpp)(PyObject *self);
    
    PyTypeObject *packagerecords_type;
    void *packagerecords_tocpp; // FIXME: need packagerecords_tocpp
    
    PyTypeObject *policy_type;
    pkgPolicy*& (*policy_tocpp)(PyObject *self);
    
    PyTypeObject *problemresolver_type;
    pkgProblemResolver*& (*problemresolver_tocpp)(PyObject *self);
    
    PyTypeObject *sourcelist_type;
    pkgSourceList*& (*sourcelist_tocpp)(PyObject *self);
    
    PyTypeObject *sourcerecords_type;
    void *sourcerecords_tocpp; // FIXME: need sourcerecords_tocpp
    
    PyTypeObject *tagfile_type;
    pkgTagFile& (*tagfile_tocpp)(PyObject *self);
    
    PyTypeObject *tagsection_type;
    pkgTagSection& (*tagsection_tocpp)(PyObject *self);
    
    PyTypeObject *version_type;
    pkgCache::VerIterator& (*version_tocpp)(PyObject *self);
};

// Checking macros.
# define PyAcquire_Check(op)          PyObject_TypeCheck(op, &PyAcquire_Type)
# define PyAcquireFile_Check(op)      PyObject_TypeCheck(op, &PyAcquireFile_Type)
# define PyAcquireItem_Check(op)      PyObject_TypeCheck(op, &PyAcquireItem_Type)
# define PyAcquireItemDesc_Check(op)  PyObject_TypeCheck(op, &PyAcquireItemDesc_Type)
# define PyAcquireWorker_Check(op)    PyObject_TypeCheck(op, &PyAcquireWorker_Type)
# define PyActionGroup_Check(op)      PyObject_TypeCheck(op, &PyActionGroup_Type)
# define PyCache_Check(op)            PyObject_TypeCheck(op, &PyCache_Type)
# define PyCacheFile_Check(op)        PyObject_TypeCheck(op, &PyCacheFile_Type)
# define PyCdrom_Check(op)            PyObject_TypeCheck(op, &PyCdrom_Type)
# define PyConfiguration_Check(op)    PyObject_TypeCheck(op, &PyConfiguration_Type)
# define PyDepCache_Check(op)         PyObject_TypeCheck(op, &PyDepCache_Type)
# define PyDependency_Check(op)       PyObject_TypeCheck(op, &PyDependency_Type)
# define PyDependencyList_Check(op)   PyObject_TypeCheck(op, &PyDependencyList_Type)
# define PyDescription_Check(op)      PyObject_TypeCheck(op, &PyDescription_Type)
# define PyHashes_Check(op)           PyObject_TypeCheck(op, &PyHashes_Type)
# define PyHashString_Check(op)       PyObject_TypeCheck(op, &PyHashString_Type)
# define PyIndexRecords_Check(op)     PyObject_TypeCheck(op, &PyIndexRecords_Type)
# define PyMetaIndex_Check(op)        PyObject_TypeCheck(op, &PyMetaIndex_Type)
# define PyPackage_Check(op)          PyObject_TypeCheck(op, &PyPackage_Type)
# define PyPackageFile_Check(op)      PyObject_TypeCheck(op, &PyPackageFile_Type)
# define PyIndexFile_Check(op)        PyObject_TypeCheck(op, &PyIndexFile_Type)
# define PyPackageList_Check(op)      PyObject_TypeCheck(op, &PyPackageList_Type)
# define PyPackageManager_Check(op)   PyObject_TypeCheck(op, &PyPackageManager_Type)
# define PyPackageRecords_Check(op)   PyObject_TypeCheck(op, &PyPackageRecords_Type)
# define PyPolicy_Check(op)           PyObject_TypeCheck(op, &PyPolicy_Type)
# define PyProblemResolver_Check(op)  PyObject_TypeCheck(op, &PyProblemResolver_Type)
# define PySourceList_Check(op)       PyObject_TypeCheck(op, &PySourceList_Type)
# define PySourceRecords_Check(op)    PyObject_TypeCheck(op, &PySourceRecords_Type)
# define PyTagFile_Check(op)          PyObject_TypeCheck(op, &PyTagFile_Type)
# define PyTagSection_Check(op)       PyObject_TypeCheck(op, &PyTagSection_Type)
# define PyVersion_Check(op)          PyObject_TypeCheck(op, &PyVersion_Type)
// Exact check macros.
# define PyAcquire_CheckExact(op)          (op->op_type == &PyAcquire_Type)
# define PyAcquireFile_CheckExact(op)      (op->op_type == &PyAcquireFile_Type)
# define PyAcquireItem_CheckExact(op)      (op->op_type == &PyAcquireItem_Type)
# define PyAcquireItemDesc_CheckExact(op)  (op->op_type == &PyAcquireItemDesc_Type)
# define PyAcquireWorker_CheckExact(op)    (op->op_type == &PyAcquireWorker_Type)
# define PyActionGroup_CheckExact(op)      (op->op_type == &PyActionGroup_Type)
# define PyCache_CheckExact(op)            (op->op_type == &PyCache_Type)
# define PyCacheFile_CheckExact(op)        (op->op_type == &PyCacheFile_Type)
# define PyCdrom_CheckExact(op)            (op->op_type == &PyCdrom_Type)
# define PyConfiguration_CheckExact(op)    (op->op_type == &PyConfiguration_Type)
# define PyDepCache_CheckExact(op)         (op->op_type == &PyDepCache_Type)
# define PyDependency_CheckExact(op)       (op->op_type == &PyDependency_Type)
# define PyDependencyList_CheckExact(op)   (op->op_type == &PyDependencyList_Type)
# define PyDescription_CheckExact(op)      (op->op_type == &PyDescription_Type)
# define PyHashes_CheckExact(op)           (op->op_type == &PyHashes_Type)
# define PyHashString_CheckExact(op)       (op->op_type == &PyHashString_Type)
# define PyIndexRecords_CheckExact(op)     (op->op_type == &PyIndexRecords_Type)
# define PyMetaIndex_CheckExact(op)        (op->op_type == &PyMetaIndex_Type)
# define PyPackage_CheckExact(op)          (op->op_type == &PyPackage_Type)
# define PyPackageFile_CheckExact(op)      (op->op_type == &PyPackageFile_Type)
# define PyIndexFile_CheckExact(op)        (op->op_type == &PyIndexFile_Type)
# define PyPackageList_CheckExact(op)      (op->op_type == &PyPackageList_Type)
# define PyPackageManager_CheckExact(op)   (op->op_type == &PyPackageManager_Type)
# define PyPackageRecords_CheckExact(op)   (op->op_type == &PyPackageRecords_Type)
# define PyPolicy_CheckExact(op)           (op->op_type == &PyPolicy_Type)
# define PyProblemResolver_CheckExact(op)  (op->op_type == &PyProblemResolver_Type)
# define PySourceList_CheckExact(op)       (op->op_type == &PySourceList_Type)
# define PySourceRecords_CheckExact(op)    (op->op_type == &PySourceRecords_Type)
# define PyTagFile_CheckExact(op)          (op->op_type == &PyTagFile_Type)
# define PyTagSection_CheckExact(op)       (op->op_type == &PyTagSection_Type)
# define PyVersion_CheckExact(op)          (op->op_type == &PyVersion_Type)

# ifndef APT_PKGMODULE_H
static struct _PyAptPkgAPIStruct *_PyAptPkg_API;

static int import_apt_pkg(void) {
#  if PY_MAJOR_VERSION >= 3 && PY_MINOR_VERSION >= 1
    _PyAptPkg_API = (_PyAptPkgAPIStruct *)PyCapsule_Import("apt_pkg._C_API", 0);
    return (_PyAptPkg_API != NULL) ? 0 : -1;
#  else

    PyObject *module = PyImport_ImportModule("apt_pkg");

    if (module == NULL) {
        return -1;
    }
    if (module != NULL) {
        PyObject *c_api_object = PyObject_GetAttrString(module, "_C_API");
        if (c_api_object == NULL)
            return -1;
        if (PyCObject_Check(c_api_object))
            _PyAptPkg_API = (struct _PyAptPkgAPIStruct *)PyCObject_AsVoidPtr(c_api_object);
        Py_DECREF(c_api_object);
    }
    return 0;
#  endif // PY_MAJOR_VERSION >= 3 && PY_MINOR_VERSION >= 1
}

#  define PyAcquire_Type           *(_PyAptPkg_API->acquire_type)
#  define PyAcquireFile_Type       *(_PyAptPkg_API->acquirefile_type)
#  define PyAcquireItem_Type       *(_PyAptPkg_API->acquireitem_type)
#  define PyAcquireItemDesc_Type   *(_PyAptPkg_API->acquireitemdesc_type)
#  define PyAcquireWorker_Type     *(_PyAptPkg_API->acquireworker_type)
#  define PyActionGroup_Type       *(_PyAptPkg_API->actiongroup_type)
#  define PyCache_Type             *(_PyAptPkg_API->cache_type)
#  define PyCacheFile_Type         *(_PyAptPkg_API->cachefile_type)
#  define PyCdrom_Type             *(_PyAptPkg_API->cdrom_type)
#  define PyConfiguration_Type     *(_PyAptPkg_API->configuration_type)
#  define PyDepCache_Type          *(_PyAptPkg_API->depcache_type)
#  define PyDependency_Type        *(_PyAptPkg_API->dependency_type)
#  define PyDependencyList_Type    *(_PyAptPkg_API->dependencylist_type)
#  define PyDescription_Type       *(_PyAptPkg_API->description_type)
#  define PyHashes_Type            *(_PyAptPkg_API->hashes_type)
#  define PyHashString_Type        *(_PyAptPkg_API->hashstring_type)
#  define PyIndexRecords_Type      *(_PyAptPkg_API->indexrecords_type)
#  define PyMetaIndex_Type         *(_PyAptPkg_API->metaindex_type)
#  define PyPackage_Type           *(_PyAptPkg_API->package_type)
#  define PyPackageFile_Type       *(_PyAptPkg_API->packagefile_type)
#  define PyIndexFile_Type         *(_PyAptPkg_API->packageindexfile_type)
#  define PyPackageList_Type       *(_PyAptPkg_API->packagelist_type)
#  define PyPackageManager_Type    *(_PyAptPkg_API->packagemanager_type)
#  define PyPackageRecords_Type    *(_PyAptPkg_API->packagerecords_type)
#  define PyPolicy_Type            *(_PyAptPkg_API->policy_type)
#  define PyProblemResolver_Type   *(_PyAptPkg_API->problemresolver_type)
#  define PySourceList_Type        *(_PyAptPkg_API->sourcelist_type)
#  define PySourceRecords_Type     *(_PyAptPkg_API->sourcerecords_type)
#  define PyTagFile_Type           *(_PyAptPkg_API->tagfile_type)
#  define PyTagSection_Type        *(_PyAptPkg_API->tagsection_type)
#  define PyVersion_Type           *(_PyAptPkg_API->version_type)
// Code 
#  define PyAcquire_ToCpp          _PyAptPkg_API->acquire_tocpp
#  define PyAcquireFile_ToCpp      _PyAptPkg_API->acquirefile_tocpp
#  define PyAcquireItem_ToCpp      _PyAptPkg_API->acquireitem_tocpp
#  define PyAcquireItemDesc_ToCpp  _PyAptPkg_API->acquireitemdesc_tocpp
#  define PyAcquireWorker_ToCpp    _PyAptPkg_API->acquireworker_tocpp
#  define PyActionGroup_ToCpp      _PyAptPkg_API->actiongroup_tocpp
#  define PyCache_ToCpp            _PyAptPkg_API->cache_tocpp
#  define PyCacheFile_ToCpp        _PyAptPkg_API->cachefile_tocpp
#  define PyCdrom_ToCpp            _PyAptPkg_API->cdrom_tocpp
#  define PyConfiguration_ToCpp    _PyAptPkg_API->configuration_tocpp
#  define PyDepCache_ToCpp         _PyAptPkg_API->depcache_tocpp
#  define PyDependency_ToCpp       _PyAptPkg_API->dependency_tocpp
#  define PyDependencyList_ToCpp   _PyAptPkg_API->dependencylist_tocpp // NULL
#  define PyDescription_ToCpp      _PyAptPkg_API->description_tocpp
#  define PyHashes_ToCpp           _PyAptPkg_API->hashes_tocpp
#  define PyHashString_ToCpp       _PyAptPkg_API->hashstring_tocpp
#  define PyIndexRecords_ToCpp     _PyAptPkg_API->indexrecords_tocpp
#  define PyMetaIndex_ToCpp        _PyAptPkg_API->metaindex_tocpp
#  define PyPackage_ToCpp          _PyAptPkg_API->package_tocpp
#  define PyPackageFile_ToCpp      _PyAptPkg_API->packagefile_tocpp
#  define PyIndexFile_ToCpp        _PyAptPkg_API->packageindexfile_tocpp
#  define PyPackageList_ToCpp      _PyAptPkg_API->packagelist_tocpp // NULL
#  define PyPackageManager_ToCpp   _PyAptPkg_API->packagemanager_tocpp
#  define PyPackageRecords_ToCpp   _PyAptPkg_API->packagerecords_tocpp
#  define PyPolicy_ToCpp           _PyAptPkg_API->policy_tocpp
#  define PyProblemResolver_ToCpp  _PyAptPkg_API->problemresolver_tocpp
#  define PySourceList_ToCpp       _PyAptPkg_API->sourcelist_tocpp
#  define PySourceRecords_ToCpp    _PyAptPkg_API->sourcerecords_tocpp // NULL
#  define PyTagFile_ToCpp          _PyAptPkg_API->tagfile_tocpp
#  define PyTagSection_ToCpp       _PyAptPkg_API->tagsection_tocpp
#  define PyVersion_ToCpp          _PyAptPkg_API->version_tocpp
// Get the C++ object
#  define PyAcquire_FromCpp              _PyAptPkg_API->acquire_fromcpp
# endif // APT_PKGMODULE_H

// Template using a simpler version of from cpp
template<class Cpp>
inline CppPyObject<Cpp> *FromCpp(PyTypeObject *pytype, Cpp const &obj, bool Delete=false, PyObject *Owner=NULL)
{
    CppPyObject<Cpp> *Obj = CppPyObject_NEW<Cpp>(Owner, pytype, obj);
    Obj->NoDelete = (!Delete);
    return Obj;
}


# define PyAcquireFile_FromCpp(...)      FromCpp<pkgAcqFile*>(&PyAcquireFile_Type, ##__VA_ARGS__)
# define PyAcquireItem_FromCpp(...)      FromCpp<pkgAcquire::Item*>(&PyAcquireItem_Type,##__VA_ARGS__)
# define PyAcquireItemDesc_FromCpp(...)  FromCpp<pkgAcquire::ItemDesc*>(&PyAcquireItemDesc_Type,##__VA_ARGS__)
# define PyAcquireWorker_FromCpp(...)  FromCpp<pkgAcquire::Worker*>(&PyAcquireWorker_Type,##__VA_ARGS__)
# define PyActionGroup_FromCpp(...)      FromCpp<pkgDepCache::ActionGroup*>(&PyActionGroup_Type,##__VA_ARGS__)
# define PyCache_FromCpp(...)            FromCpp<pkgCache*>(&PyCache_Type,##__VA_ARGS__)
# define PyCacheFile_FromCpp(...)        FromCpp<pkgCacheFile*>(&PyCacheFile_Type,##__VA_ARGS__)
# define PyCdrom_FromCpp(...)            FromCpp<pkgCdrom>(&PyCdrom_Type,##__VA_ARGS__)
# define PyConfiguration_FromCpp(...)    FromCpp<Configuration*>(&PyConfiguration_Type, ##__VA_ARGS__)
# define PyDepCache_FromCpp(...)         FromCpp<pkgDepCache*>(&PyDepCache_Type,##__VA_ARGS__)
# define PyDependency_FromCpp(...)       FromCpp<pkgCache::DepIterator>(&PyDependency_Type,##__VA_ARGS__)
//# define PyDependencyList_FromCpp(...)   FromCpp<RDepListStruct>(&PyDependencyList_Type,##__VA_ARGS__)
# define PyDescription_FromCpp(...)      FromCpp<pkgCache::DescIterator>(&PyDescription_Type,##__VA_ARGS__)
# define PyHashes_FromCpp(...)           FromCpp<Hashes>(&PyHashes_Type,##__VA_ARGS__)
# define PyHashString_FromCpp(...)       FromCpp<HashString*>(&PyHashString_Type,##__VA_ARGS__)
# define PyIndexRecords_FromCpp(...)     FromCpp<indexRecords*>(&PyIndexRecords_Type,##__VA_ARGS__)
# define PyMetaIndex_FromCpp(...)        FromCpp<metaIndex*>(&PyMetaIndex_Type,##__VA_ARGS__)
# define PyPackage_FromCpp(...)          FromCpp<pkgCache::PkgIterator>(&PyPackage_Type,##__VA_ARGS__)
# define PyIndexFile_FromCpp(...) FromCpp<pkgIndexFile*>(&PyIndexFile_Type,##__VA_ARGS__)
# define PyPackageFile_FromCpp(...)      FromCpp<pkgCache::PkgFileIterator>(&PyPackageFile_Type,##__VA_ARGS__)
//# define PyPackageList_FromCpp(...)      FromCpp<PkgListStruct>(&PyPackageList_Type,##__VA_ARGS__)
# define PyPackageManager_FromCpp(...)   FromCpp<pkgPackageManager*>(&PyPackageManager_Type,##__VA_ARGS__)
//# define PyPackageRecords_FromCpp(...)   FromCpp<PkgRecordsStruct>(&PyPackageRecords_Type,##__VA_ARGS__)
# define PyPolicy_FromCpp(...)           FromCpp<pkgPolicy*>(&PyPolicy_Type,##__VA_ARGS__)
# define PyProblemResolver_FromCpp(...)  FromCpp<pkgProblemResolver*>(&PyProblemResolver_Type,##__VA_ARGS__)
# define PySourceList_FromCpp(...)       FromCpp<pkgSourceList*>(&PySourceList_Type,##__VA_ARGS__)
//# define PySourceRecords_FromCpp(...)    FromCpp<PkgSrcRecordsStruct>(&PySourceRecords_Type,##__VA_ARGS__)
# define PyTagFile_FromCpp(...)          FromCpp<pkgTagFile>(&PyTagFile_Type,##__VA_ARGS__)
# define PyTagSection_FromCpp(...)       FromCpp<pkgTagSection>(&PyTagSection_Type,##__VA_ARGS__)
# define PyVersion_FromCpp(...)          FromCpp<pkgCache::VerIterator>(&PyVersion_Type,##__VA_ARGS__)
#endif

