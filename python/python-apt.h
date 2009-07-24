/*
 * python-apt.h - Header file for the public interface.
 *
 * Copyright 2009 Julian Andres Klode <jak@debian.org>
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

struct _PyAptPkgAPIStruct {
    PyTypeObject *acquire_type;
    PyTypeObject *acquirefile_type;
    PyTypeObject *acquireitem_type;
    PyTypeObject *acquireitemdesc_type;
    PyTypeObject *acquireworker_type;
    PyTypeObject *actiongroup_type;
    PyTypeObject *cache_type;
    PyTypeObject *cachefile_type;
    PyTypeObject *cdrom_type;
    PyTypeObject *configuration_type;
    PyTypeObject *depcache_type;
    PyTypeObject *dependency_type;
    PyTypeObject *dependencylist_type;
    PyTypeObject *description_type;
    PyTypeObject *hashes_type;
    PyTypeObject *hashstring_type;
    PyTypeObject *indexrecords_type;
    PyTypeObject *metaindex_type;
    PyTypeObject *package_type;
    PyTypeObject *packagefile_type;
    PyTypeObject *packageindexfile_type;
    PyTypeObject *packagelist_type;
    PyTypeObject *packagemanager_type;
    PyTypeObject *packagerecords_type;
    PyTypeObject *policy_type;
    PyTypeObject *problemresolver_type;
    PyTypeObject *sourcelist_type;
    PyTypeObject *sourcerecords_type;
    PyTypeObject *tagfile_type;
    PyTypeObject *tagsection_type;
    PyTypeObject *version_type;
};

# ifndef APT_PKGMODULE_H
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
#  define PyPackageIndexFile_Type  *(_PyAptPkg_API->packageindexfile_type)
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

// Creating

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
# endif // APT_PKGMODULE_H

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
# define PyPackageIndexFile_Check(op) PyObject_TypeCheck(op, &PyPackageIndexFile_Type)
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
# define PyPackageIndexFile_CheckExact(op) (op->op_type == &PyPackageIndexFile_Type)
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

// Get the underlying C++ reference or pointer from the Python object.
# define PyAcquire_ToCpp           GetCpp<pkgAcquire*>
# define PyAcquireFile_ToCpp       GetCpp<pkgAcqFile*>
# define PyAcquireItem_ToCpp       GetCpp<pkgAcquire::Item*>
# define PyAcquireItemDesc_ToCpp   GetCpp<pkgAcquire::ItemDesc*>
# define PyAcquireWorker_ToCpp     GetCpp<pkgAcquire::Worker*>
# define PyActionGroup_ToCpp       GetCpp<pkgDepCache::ActionGroup*>
# define PyCache_ToCpp             GetCpp<pkgCache*>
# define PyCacheFile_ToCpp         GetCpp<pkgCacheFile*>
# define PyCdrom_ToCpp             GetCpp<pkgCdrom>
# define PyConfiguration_ToCpp     GetCpp<Configuration*>
# define PyDepCache_ToCpp          GetCpp<pkgDepCache*>
# define PyDependency_ToCpp        GetCpp<pkgCache::DepIterator>
//# define PyDependencyList_ToCpp    GetCpp<RDepListStruct> // NOT EXPORTED
# define PyDescription_ToCpp       GetCpp<pkgCache::DescIterator>
# define PyHashes_ToCpp            GetCpp<Hashes>
# define PyHashString_ToCpp        GetCpp<HashString*>
# define PyIndexRecords_ToCpp      GetCpp<indexRecords*>
# define PyMetaIndex_ToCpp         GetCpp<metaIndex*>
# define PyPackage_ToCpp           GetCpp<pkgCache::PkgIterator>
# define PyPackageFile_ToCpp       GetCpp<pkgCache::PkgFileIterator>
# define PyPackageIndexFile_ToCpp  GetCpp<pkgIndexFile*>
//# define PyPackageList_ToCpp       GetCpp<PkgListStruct> // NOT EXPORTED.
# define PyPackageManager_ToCpp    GetCpp<pkgPackageManager*>
//# define PyPackageRecords_ToCpp    GetCpp<PkgRecordsStruct> // NOT EXPORTED
# define PyPolicy_ToCpp            GetCpp<pkgPolicy*>
# define PyProblemResolver_ToCpp   GetCpp<pkgProblemResolver*>
# define PySourceList_ToCpp        GetCpp<pkgSourceList*>
//# define PySourceRecords_ToCpp     GetCpp<PkgSrcRecordsStruct> // NOT EXPORTED
# define PyTagFile_ToCpp           GetCpp<pkgTagFile>
# define PyTagSection_ToCpp        GetCpp<pkgTagSection>
# define PyVersion_ToCpp           GetCpp<pkgCache::VerIterator>

// Python object creation, using two inline template functions and one variadic
// macro per type.
template<class Cpp>
inline CppPyObject<Cpp> *FromCpp(PyTypeObject *pytype, Cpp obj,
                                 bool Delete=false)
{
    CppPyObject<Cpp> *Obj = CppPyObject_NEW<Cpp>(pytype, obj);
    Obj->NoDelete = (!Delete);
    return Obj;
}

template<class Cpp>
inline CppOwnedPyObject<Cpp> *FromCppOwned(PyTypeObject *pytype, Cpp const &obj,
                              bool Delete=false, PyObject *Owner=NULL)
{
    CppOwnedPyObject<Cpp> *Obj = CppOwnedPyObject_NEW<Cpp>(Owner, pytype, obj);
    Obj->NoDelete = (!Delete);
    return Obj;
}

# define PyAcquire_FromCpp(...)          FromCpp<pkgAcquire*>(&PyAcquire_Type, ##__VA_ARGS__)
# define PyAcquireFile_FromCpp(...)      FromCppOwned<pkgAcqFile*>(&PyAcquireFile_Type, ##__VA_ARGS__)
# define PyAcquireItem_FromCpp(...)      FromCppOwned<pkgAcquire::Item*>(&PyAcquireItem_Type,##__VA_ARGS__)
# define PyAcquireItemDesc_FromCpp(...)  FromCppOwned<pkgAcquire::ItemDesc*>(&PyAcquireItemDesc_Type,##__VA_ARGS__)
# define PyAcquireWorker_FromCpp(...)  FromCppOwned<pkgAcquire::Worker*>(&PyAcquireWorker_Type,##__VA_ARGS__)
# define PyActionGroup_FromCpp(...)      FromCppOwned<pkgDepCache::ActionGroup*>(&PyActionGroup_Type,##__VA_ARGS__)
# define PyCache_FromCpp(...)            FromCppOwned<pkgCache*>(&PyCache_Type,##__VA_ARGS__)
# define PyCacheFile_FromCpp(...)        FromCpp<pkgCacheFile*>(&PyCacheFile_Type,##__VA_ARGS__)
# define PyCdrom_FromCpp(...)            FromCpp<pkgCdrom>(&PyCdrom_Type,##__VA_ARGS__)
# define PyConfiguration_FromCpp(...)    FromCppOwned<Configuration*>(&PyConfiguration_Type, ##__VA_ARGS__)
# define PyDepCache_FromCpp(...)         FromCppOwned<pkgDepCache*>(&PyDepCache_Type,##__VA_ARGS__)
# define PyDependency_FromCpp(...)       FromCppOwned<pkgCache::DepIterator>(&PyDependency_Type,##__VA_ARGS__)
//# define PyDependencyList_FromCpp(...)   FromCppOwned<RDepListStruct>(&PyDependencyList_Type,##__VA_ARGS__)
# define PyDescription_FromCpp(...)      FromCppOwned<pkgCache::DescIterator>(&PyDescription_Type,##__VA_ARGS__)
# define PyHashes_FromCpp(...)           FromCpp<Hashes>(&PyHashes_Type,##__VA_ARGS__)
# define PyHashString_FromCpp(...)       FromCpp<HashString*>(&PyHashString_Type,##__VA_ARGS__)
# define PyIndexRecords_FromCpp(...)     FromCpp<indexRecords*>(&PyIndexRecords_Type,##__VA_ARGS__)
# define PyMetaIndex_FromCpp(...)        FromCppOwned<metaIndex*>(&PyMetaIndex_Type,##__VA_ARGS__)
# define PyPackage_FromCpp(...)          FromCppOwned<pkgCache::PkgIterator>(&PyPackage_Type,##__VA_ARGS__)
# define PyPackageIndexFile_FromCpp(...) FromCppOwned<pkgIndexFile*>(&PyPackageIndexFile_Type,##__VA_ARGS__)
# define PyPackageFile_FromCpp(...)      FromCppOwned<pkgCache::PkgFileIterator>(&PyPackageFile_Type,##__VA_ARGS__)
//# define PyPackageList_FromCpp(...)      FromCppOwned<PkgListStruct>(&PyPackageList_Type,##__VA_ARGS__)
# define PyPackageManager_FromCpp(...)   FromCpp<pkgPackageManager*>(&PyPackageManager_Type,##__VA_ARGS__)
//# define PyPackageRecords_FromCpp(...)   FromCppOwned<PkgRecordsStruct>(&PyPackageRecords_Type,##__VA_ARGS__)
# define PyPolicy_FromCpp(...)           FromCppOwned<pkgPolicy*>(&PyPolicy_Type,##__VA_ARGS__)
# define PyProblemResolver_FromCpp(...)  FromCppOwned<pkgProblemResolver*>(&PyProblemResolver_Type,##__VA_ARGS__)
# define PySourceList_FromCpp(...)       FromCpp<pkgSourceList*>(&PySourceList_Type,##__VA_ARGS__)
//# define PySourceRecords_FromCpp(...)    FromCpp<PkgSrcRecordsStruct>(&PySourceRecords_Type,##__VA_ARGS__)
# define PyTagFile_FromCpp(...)          FromCppOwned<pkgTagFile>(&PyTagFile_Type,##__VA_ARGS__)
# define PyTagSection_FromCpp(...)       FromCppOwned<pkgTagSection>(&PyTagSection_Type,##__VA_ARGS__)
# define PyVersion_FromCpp(...)          FromCppOwned<pkgCache::VerIterator>(&PyVersion_Type,##__VA_ARGS__)
#endif
