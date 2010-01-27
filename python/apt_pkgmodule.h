// -*- mode: cpp; mode: fold -*-
// Description								/*{{{*/
// $Id: apt_pkgmodule.h,v 1.4 2003/07/23 02:20:24 mdz Exp $
/* ######################################################################

   Prototypes for the module

   ##################################################################### */
									/*}}}*/
#ifndef APT_PKGMODULE_H
#define APT_PKGMODULE_H

#include <Python.h>
#include <apt-pkg/hashes.h>
#include <apt-pkg/acquire-item.h>
#include "generic.h"

// Configuration Stuff
#define Configuration_Check(op) ((op)->ob_type == &PyConfiguration_Type)
extern PyTypeObject PyConfiguration_Type;
extern PyTypeObject PyVersion_Type;

extern char *doc_LoadConfig;
extern char *doc_LoadConfigISC;
extern char *doc_LoadConfigDir;
extern char *doc_ParseCommandLine;
PyObject *LoadConfig(PyObject *Self,PyObject *Args);
PyObject *LoadConfigISC(PyObject *Self,PyObject *Args);
PyObject *LoadConfigDir(PyObject *Self,PyObject *Args);
PyObject *ParseCommandLine(PyObject *Self,PyObject *Args);

// Tag File Stuff
extern PyTypeObject PyTagSection_Type;
extern PyTypeObject PyTagFile_Type;
extern char *doc_ParseSection;
extern char *doc_ParseTagFile;
extern char *doc_RewriteSection;
PyObject *ParseSection(PyObject *self,PyObject *Args);
PyObject *ParseTagFile(PyObject *self,PyObject *Args);
PyObject *RewriteSection(PyObject *self,PyObject *Args);

// String Stuff
PyObject *StrQuoteString(PyObject *self,PyObject *Args);
PyObject *StrDeQuote(PyObject *self,PyObject *Args);
PyObject *StrSizeToStr(PyObject *self,PyObject *Args);
PyObject *StrTimeToStr(PyObject *self,PyObject *Args);
PyObject *StrURItoFileName(PyObject *self,PyObject *Args);
PyObject *StrBase64Encode(PyObject *self,PyObject *Args);
PyObject *StrStringToBool(PyObject *self,PyObject *Args);
PyObject *StrTimeRFC1123(PyObject *self,PyObject *Args);
PyObject *StrStrToTime(PyObject *self,PyObject *Args);
PyObject *StrCheckDomainList(PyObject *Self,PyObject *Args);

PyObject *PyAcquire_GetItem(PyObject *self, pkgAcquire::Item *item);
PyObject *PyAcquire_GetItemDesc(PyObject *self, pkgAcquire::ItemDesc *item);
bool     PyAcquire_DropItem(PyObject *self, pkgAcquire::Item *item);

// Cache Stuff
extern PyTypeObject PyCache_Type;
extern PyTypeObject PyCacheFile_Type;
extern PyTypeObject PyPackageList_Type;
extern PyTypeObject PyDescription_Type;
extern PyTypeObject PyPackage_Type;
extern PyTypeObject PyPackageFile_Type;
extern PyTypeObject PyDependency_Type;
extern PyTypeObject PyDependencyList_Type;
PyObject *TmpGetCache(PyObject *Self,PyObject *Args);

// DepCache
extern PyTypeObject PyDepCache_Type;
PyObject *GetDepCache(PyObject *Self,PyObject *Args);

// pkgProblemResolver
extern PyTypeObject PyProblemResolver_Type;
PyObject *GetPkgProblemResolver(PyObject *Self, PyObject *Args);
PyObject *GetPkgActionGroup(PyObject *Self, PyObject *Args);

extern PyTypeObject PyActionGroup_Type;
// cdrom
extern PyTypeObject PyCdrom_Type;
PyObject *GetCdrom(PyObject *Self,PyObject *Args);

// acquire
extern PyTypeObject PyAcquireItem_Type;
extern PyTypeObject PyAcquire_Type;
extern PyTypeObject PyAcquireFile_Type;
extern char *doc_GetPkgAcqFile;
PyObject *GetAcquire(PyObject *Self,PyObject *Args);
PyObject *GetPkgAcqFile(PyObject *Self, PyObject *Args, PyObject *kwds);

// packagemanager
extern PyTypeObject PyPackageManager_Type;
PyObject *GetPkgManager(PyObject *Self,PyObject *Args);


// PkgRecords Stuff
extern PyTypeObject PyPackageRecords_Type;
extern PyTypeObject PySourceRecords_Type;
PyObject *GetPkgRecords(PyObject *Self,PyObject *Args);
PyObject *GetPkgSrcRecords(PyObject *Self,PyObject *Args);

// pkgSourceList
extern PyTypeObject PySourceList_Type;
PyObject *GetPkgSourceList(PyObject *Self,PyObject *Args);

// pkgSourceList
extern PyTypeObject PyIndexFile_Type;

// metaIndex
extern PyTypeObject PyMetaIndex_Type;

// HashString
extern PyTypeObject PyHashString_Type;

// IndexRecord
extern PyTypeObject PyIndexRecords_Type;

// Policy
extern PyTypeObject PyPolicy_Type;
extern PyTypeObject PyHashes_Type;
extern PyTypeObject PyAcquireItemDesc_Type;
extern PyTypeObject PyAcquireWorker_Type;
extern PyTypeObject PySystemLock_Type;
extern PyTypeObject PyFileLock_Type;

// Functions to be exported in the public API.
PyObject *PyAcquire_FromCpp(pkgAcquire *fetcher, bool Delete);
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
# define PyDependencyList_ToCpp    GetCpp<RDepListStruct> // TODO
# define PyDescription_ToCpp       GetCpp<pkgCache::DescIterator>
# define PyHashes_ToCpp            GetCpp<Hashes>
# define PyHashString_ToCpp        GetCpp<HashString*>
# define PyIndexRecords_ToCpp      GetCpp<indexRecords*>
# define PyMetaIndex_ToCpp         GetCpp<metaIndex*>
# define PyPackage_ToCpp           GetCpp<pkgCache::PkgIterator>
# define PyPackageFile_ToCpp       GetCpp<pkgCache::PkgFileIterator>
# define PyIndexFile_ToCpp         GetCpp<pkgIndexFile*>
# define PyPackageList_ToCpp       GetCpp<PkgListStruct> // TODO
# define PyPackageManager_ToCpp    GetCpp<pkgPackageManager*>
# define PyPackageRecords_ToCpp    GetCpp<PkgRecordsStruct> // TODO
# define PyPolicy_ToCpp            GetCpp<pkgPolicy*>
# define PyProblemResolver_ToCpp   GetCpp<pkgProblemResolver*>
# define PySourceList_ToCpp        GetCpp<pkgSourceList*>
# define PySourceRecords_ToCpp     GetCpp<PkgSrcRecordsStruct> // TODO
# define PyTagFile_ToCpp           GetCpp<pkgTagFile>
# define PyTagSection_ToCpp        GetCpp<pkgTagSection>
# define PyVersion_ToCpp           GetCpp<pkgCache::VerIterator>


#include "python-apt.h"
#endif

