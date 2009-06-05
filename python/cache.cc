// -*- mode: cpp; mode: fold -*-
// Description								/*{{{*/
// $Id: cache.cc,v 1.5 2003/06/03 03:03:23 mdz Exp $
/* ######################################################################

   Cache - Wrapper for the cache related functions

   ##################################################################### */
									/*}}}*/
// Include Files							/*{{{*/
#include "generic.h"
#include "apt_pkgmodule.h"

#include <apt-pkg/pkgcache.h>
#include <apt-pkg/cachefile.h>
#include <apt-pkg/sptr.h>
#include <apt-pkg/configuration.h>
#include <apt-pkg/sourcelist.h>
#include <apt-pkg/error.h>
#include <apt-pkg/packagemanager.h>
#include <apt-pkg/pkgsystem.h>
#include <apt-pkg/sourcelist.h>
#include <apt-pkg/algorithms.h>

#include <Python.h>
#include "progress.h"

class pkgSourceList;

									/*}}}*/
struct PkgListStruct
{
   pkgCache::PkgIterator Iter;
   unsigned long LastIndex;

   PkgListStruct(pkgCache::PkgIterator const &I) : Iter(I), LastIndex(0) {}
   PkgListStruct() {abort();};  // G++ Bug..
};

struct RDepListStruct
{
   pkgCache::DepIterator Iter;
   pkgCache::DepIterator Start;
   unsigned long LastIndex;
   unsigned long Len;

   RDepListStruct(pkgCache::DepIterator const &I) : Iter(I), Start(I),
                         LastIndex(0)
   {
      Len = 0;
      pkgCache::DepIterator D = I;
      for (; D.end() == false; D++)
	 Len++;
   }
   RDepListStruct() {abort();};  // G++ Bug..
};

static PyObject *CreateProvides(PyObject *Owner,pkgCache::PrvIterator I)
{
   PyObject *List = PyList_New(0);
   for (; I.end() == false; I++)
   {
      PyObject *Obj;
      PyObject *Ver;
      Ver = CppOwnedPyObject_NEW<pkgCache::VerIterator>(Owner,&VersionType,
							I.OwnerVer());
      Obj = Py_BuildValue("ssN",I.ParentPkg().Name(),I.ProvideVersion(),
			  Ver);
      PyList_Append(List,Obj);
      Py_DECREF(Obj);
   }
   return List;
}

// Cache Class								/*{{{*/
// ---------------------------------------------------------------------
static PyObject *PkgCacheUpdate(PyObject *Self,PyObject *Args)
{
   PyObject *CacheFilePy = GetOwner<pkgCache*>(Self);
   pkgCacheFile *Cache = GetCpp<pkgCacheFile*>(CacheFilePy);

   PyObject *pyFetchProgressInst = 0;
   PyObject *pySourcesList = 0;
   if (PyArg_ParseTuple(Args, "OO", &pyFetchProgressInst,&pySourcesList) == 0)
      return 0;

   PyFetchProgress progress;
   progress.setCallbackInst(pyFetchProgressInst);
   pkgSourceList *source = GetCpp<pkgSourceList*>(pySourcesList);
   bool res = ListUpdate(progress, *source);

   PyObject *PyRes = Py_BuildValue("b", res);
   return HandleErrors(PyRes);
}

static PyObject *PkgCacheClose(PyObject *Self,PyObject *Args)
{
   PyObject *CacheFilePy = GetOwner<pkgCache*>(Self);
   pkgCacheFile *Cache = GetCpp<pkgCacheFile*>(CacheFilePy);
   Cache->Close();

   Py_INCREF(Py_None);
   return HandleErrors(Py_None);
}

static PyObject *PkgCacheOpen(PyObject *Self,PyObject *Args)
{
   PyObject *CacheFilePy = GetOwner<pkgCache*>(Self);
   pkgCacheFile *Cache = GetCpp<pkgCacheFile*>(CacheFilePy);

   PyObject *pyCallbackInst = 0;
   if (PyArg_ParseTuple(Args, "|O", &pyCallbackInst) == 0)
      return 0;

   if(pyCallbackInst != 0) {
      PyOpProgress progress;
      progress.setCallbackInst(pyCallbackInst);
      if (Cache->Open(progress,false) == false)
	 return HandleErrors();
   }  else {
      OpTextProgress Prog;
      if (Cache->Open(Prog,false) == false)
	 return HandleErrors();
   }

   //std::cout << "new cache is " << (pkgCache*)(*Cache) << std::endl;

   // update the cache pointer after the cache was rebuild
   ((CppPyObject<pkgCache*> *)Self)->Object = (pkgCache*)(*Cache);


   Py_INCREF(Py_None);
   return HandleErrors(Py_None);
}


static PyMethodDef PkgCacheMethods[] =
{
   {"update",PkgCacheUpdate,METH_VARARGS,"Update the cache"},
   {"open", PkgCacheOpen, METH_VARARGS,"Open the cache"},
   {"close", PkgCacheClose, METH_VARARGS,"Close the cache"},
#ifdef COMPAT_0_7
   {"Update",PkgCacheUpdate,METH_VARARGS,"Update the cache"},
   {"Open", PkgCacheOpen, METH_VARARGS,"Open the cache"},
   {"Close", PkgCacheClose, METH_VARARGS,"Close the cache"},
#endif
   {}
};

static PyObject *PkgCacheGetPackages(PyObject *Self, void*) {
   pkgCache *Cache = GetCpp<pkgCache *>(Self);
   return CppOwnedPyObject_NEW<PkgListStruct>(Self,&PkgListType,Cache->PkgBegin());
}

static PyObject *PkgCacheGetPackageCount(PyObject *Self, void*) {
   pkgCache *Cache = GetCpp<pkgCache *>(Self);
   return Py_BuildValue("i",Cache->HeaderP->PackageCount);
}

static PyObject *PkgCacheGetVersionCount(PyObject *Self, void*) {
   pkgCache *Cache = GetCpp<pkgCache *>(Self);
   return Py_BuildValue("i",Cache->HeaderP->VersionCount);
}
static PyObject *PkgCacheGetDependsCount(PyObject *Self, void*) {
   pkgCache *Cache = GetCpp<pkgCache *>(Self);
   return Py_BuildValue("i",Cache->HeaderP->DependsCount);
}

static PyObject *PkgCacheGetPackageFileCount(PyObject *Self, void*) {
   pkgCache *Cache = GetCpp<pkgCache *>(Self);
   return Py_BuildValue("i",Cache->HeaderP->PackageFileCount);
}

static PyObject *PkgCacheGetVerFileCount(PyObject *Self, void*) {
   pkgCache *Cache = GetCpp<pkgCache *>(Self);
   return Py_BuildValue("i",Cache->HeaderP->VerFileCount);
}

static PyObject *PkgCacheGetProvidesCount(PyObject *Self, void*) {
   pkgCache *Cache = GetCpp<pkgCache *>(Self);
   return Py_BuildValue("i",Cache->HeaderP->ProvidesCount);
}

static PyObject *PkgCacheGetFileList(PyObject *Self, void*) {
   pkgCache *Cache = GetCpp<pkgCache *>(Self);
   PyObject *List = PyList_New(0);
   for (pkgCache::PkgFileIterator I = Cache->FileBegin(); I.end() == false; I++)
   {
      PyObject *Obj;
      Obj = CppOwnedPyObject_NEW<pkgCache::PkgFileIterator>(Self,&PackageFileType,I);
      PyList_Append(List,Obj);
      Py_DECREF(Obj);
   }
   return List;
}

static PyGetSetDef PkgCacheGetSet[] = {
   {"depends_count",PkgCacheGetDependsCount},
   {"file_list",PkgCacheGetFileList},
   {"package_count",PkgCacheGetPackageCount},
   {"package_file_count",PkgCacheGetPackageFileCount},
   {"packages",PkgCacheGetPackages},
   {"provides_count",PkgCacheGetProvidesCount},
   {"ver_file_count",PkgCacheGetVerFileCount},
   {"version_count",PkgCacheGetVersionCount},
#ifdef COMPAT_0_7
   {"DependsCount",PkgCacheGetDependsCount},
   {"FileList",PkgCacheGetFileList},
   {"PackageCount",PkgCacheGetPackageCount},
   {"PackageFileCount",PkgCacheGetPackageFileCount},
   {"Packages",PkgCacheGetPackages},
   {"ProvidesCount",PkgCacheGetProvidesCount},
   {"VerFileCount",PkgCacheGetVerFileCount},
   {"VersionCount",PkgCacheGetVersionCount},
#endif
   {}
};

// Map access, operator []
static PyObject *CacheMapOp(PyObject *Self,PyObject *Arg)
{
   pkgCache *Cache = GetCpp<pkgCache *>(Self);

   if (PyString_Check(Arg) == 0)
   {
      PyErr_SetNone(PyExc_TypeError);
      return 0;
   }

   // Search for the package
   const char *Name = PyString_AsString(Arg);
   pkgCache::PkgIterator Pkg = Cache->FindPkg(Name);
   if (Pkg.end() == true)
   {
      PyErr_SetString(PyExc_KeyError,Name);
      return 0;
   }

   return CppOwnedPyObject_NEW<pkgCache::PkgIterator>(Self,&PackageType,Pkg);
}

// we need a special dealloc here to make sure that the CacheFile
// is closed before deallocation the cache (otherwise we have a bad)
// memory leak
void PkgCacheFileDealloc(PyObject *Self)
{
   PyObject *CacheFilePy = GetOwner<pkgCache*>(Self);
   pkgCacheFile *CacheF = GetCpp<pkgCacheFile*>(CacheFilePy);
   CacheF->Close();
   CppOwnedDealloc<pkgCache *>(Self);
}

static PyObject *PkgCacheNew(PyTypeObject *type,PyObject *Args,PyObject *kwds)
{
   PyObject *pyCallbackInst = 0;
   static char *kwlist[] = {"progress", 0};
   if (PyArg_ParseTupleAndKeywords	(Args, kwds, "|O", kwlist, &pyCallbackInst) == 0)
      return 0;

    if (_system == 0) {
        PyErr_SetString(PyExc_ValueError,"_system not initialized");
        return 0;
    }

   pkgCacheFile *Cache = new pkgCacheFile();

   if(pyCallbackInst != 0) {
      // sanity check for the progress object, see #497049
      if (PyObject_HasAttrString(pyCallbackInst, "done") != true) {
        PyErr_SetString(PyExc_ValueError,
                        "OpProgress object must implement done()");
        return 0;
      }
      if (PyObject_HasAttrString(pyCallbackInst, "update") != true) {
        PyErr_SetString(PyExc_ValueError,
                        "OpProgress object must implement update()");
        return 0;
      }
      PyOpProgress progress;
      progress.setCallbackInst(pyCallbackInst);
      if (Cache->Open(progress,false) == false)
         return HandleErrors();
   }
   else {
      OpTextProgress Prog;
      if (Cache->Open(Prog,false) == false)
	     return HandleErrors();
   }

   CppOwnedPyObject<pkgCacheFile*> *CacheFileObj =
	   CppOwnedPyObject_NEW<pkgCacheFile*>(0,&PkgCacheFileType, Cache);

   CppOwnedPyObject<pkgCache *> *CacheObj =
	   CppOwnedPyObject_NEW<pkgCache *>(CacheFileObj,type,
					    (pkgCache *)(*Cache));

   //Py_DECREF(CacheFileObj);
   return CacheObj;
}

static char *doc_PkgCache = "Cache([progress]) -> Cache() object.\n\n"
    "The cache provides access to the packages and other stuff.\n\n"
    "The optional parameter *progress* can be used to specify an \n"
    "apt.progress.OpProgress() object (or similar) which displays\n"
    "the opening progress.\n\n"
    "If not specified, the progress is displayed in simple text form.";

static PyMappingMethods CacheMap = {0,CacheMapOp,0};
PyTypeObject PkgCacheType =
{
   PyObject_HEAD_INIT(&PyType_Type)
   #if PY_MAJOR_VERSION < 3
   0,			                // ob_size
   #endif
   "apt_pkg.Cache",                     // tp_name
   sizeof(CppOwnedPyObject<pkgCache *>),   // tp_basicsize
   0,                                   // tp_itemsize
   // Methods
   PkgCacheFileDealloc,                  // tp_dealloc
   0,                                   // tp_print
   0,                                   // tp_getattr
   0,                                   // tp_setattr
   0,                                   // tp_compare
   0,                                   // tp_repr
   0,                                   // tp_as_number
   0,                                   // tp_as_sequence
   &CacheMap,		                // tp_as_mapping
   0,                                   // tp_hash
   0,                                   // tp_call
   0,                                   // tp_str
   0,                                   // tp_getattro
   0,                                   // tp_setattro
   0,                                   // tp_as_buffer
   Py_TPFLAGS_DEFAULT ,                 // tp_flags
   doc_PkgCache,                        // tp_doc
   0,                                   // tp_traverse
   0,                                   // tp_clear
   0,                                   // tp_richcompare
   0,                                   // tp_weaklistoffset
   0,                                   // tp_iter
   0,                                   // tp_iternext
   PkgCacheMethods,                     // tp_methods
   0,                                   // tp_members
   PkgCacheGetSet,                      // tp_getset
   0,                                   // tp_base
   0,                                   // tp_dict
   0,                                   // tp_descr_get
   0,                                   // tp_descr_set
   0,                                   // tp_dictoffset
   0,                                   // tp_init
   0,                                   // tp_alloc
   PkgCacheNew,                         // tp_new
};
									/*}}}*/
// PkgCacheFile Class							/*{{{*/
// ---------------------------------------------------------------------
PyTypeObject PkgCacheFileType =
{
   PyObject_HEAD_INIT(&PyType_Type)
   #if PY_MAJOR_VERSION < 3
   0,			                // ob_size
   #endif
   "pkgCacheFile",                      // tp_name
   sizeof(CppOwnedPyObject<pkgCacheFile*>),   // tp_basicsize
   0,                                   // tp_itemsize
   // Methods
   CppOwnedDealloc<pkgCacheFile*>,       // tp_dealloc
   0,                                   // tp_print
   0,                                   // tp_getattr
   0,                                   // tp_setattr
   0,                                   // tp_compare
   0,                                   // tp_repr
   0,                                   // tp_as_number
   0,                                   // tp_as_sequence
   0,                                   // tp_as_mapping
   0,                                   // tp_hash
};
									/*}}}*/
// Package List Class							/*{{{*/
// ---------------------------------------------------------------------
static Py_ssize_t PkgListLen(PyObject *Self)
{
   return GetCpp<PkgListStruct>(Self).Iter.Cache()->HeaderP->PackageCount;
}

static PyObject *PkgListItem(PyObject *iSelf,Py_ssize_t Index)
{
   PkgListStruct &Self = GetCpp<PkgListStruct>(iSelf);
   if (Index < 0 || (unsigned)Index >= Self.Iter.Cache()->HeaderP->PackageCount)
   {
      PyErr_SetNone(PyExc_IndexError);
      return 0;
   }

   if ((unsigned)Index < Self.LastIndex)
   {
      Self.LastIndex = 0;
      Self.Iter = Self.Iter.Cache()->PkgBegin();
   }

   while ((unsigned)Index > Self.LastIndex)
   {
      Self.LastIndex++;
      Self.Iter++;
      if (Self.Iter.end() == true)
      {
	 PyErr_SetNone(PyExc_IndexError);
	 return 0;
      }
   }

   return CppOwnedPyObject_NEW<pkgCache::PkgIterator>(GetOwner<PkgListStruct>(iSelf),&PackageType,
						      Self.Iter);
}

static PySequenceMethods PkgListSeq =
{
   PkgListLen,
   0,                // concat
   0,                // repeat
   PkgListItem,
   0,                // slice
   0,                // assign item
   0                 // assign slice
};

PyTypeObject PkgListType =
{
   PyObject_HEAD_INIT(&PyType_Type)
   #if PY_MAJOR_VERSION < 3
   0,			                // ob_size
   #endif
   "apt_pkg.PackageList",               // tp_name
   sizeof(CppOwnedPyObject<PkgListStruct>),   // tp_basicsize
   0,                                   // tp_itemsize
   // Methods
   CppOwnedDealloc<PkgListStruct>,      // tp_dealloc
   0,                                   // tp_print
   0,                                   // tp_getattr
   0,                                   // tp_setattr
   0,                                   // tp_compare
   0,                                   // tp_repr
   0,                                   // tp_as_number
   &PkgListSeq,                         // tp_as_sequence
   0,			                // tp_as_mapping
   0,                                   // tp_hash
};

#define MkGet(PyFunc,Ret) static PyObject *PyFunc(PyObject *Self,void*) \
{ \
    pkgCache::PkgIterator &Pkg = GetCpp<pkgCache::PkgIterator>(Self); \
    PyObject *Owner = GetOwner<pkgCache::PkgIterator>(Self); \
    return Ret; \
}

MkGet(PackageGetName,PyString_FromString(Pkg.Name()));
MkGet(PackageGetSection,Safe_FromString(Pkg.Section()));
MkGet(PackageGetRevDependsList,CppOwnedPyObject_NEW<RDepListStruct>(Owner,
                               &RDepListType, Pkg.RevDependsList()));
MkGet(PackageGetProvidesList,CreateProvides(Owner,Pkg.ProvidesList()));
MkGet(PackageGetSelectedState,Py_BuildValue("i",Pkg->SelectedState));
MkGet(PackageGetInstState,Py_BuildValue("i",Pkg->InstState));
MkGet(PackageGetCurrentState,Py_BuildValue("i",Pkg->CurrentState));
MkGet(PackageGetID,Py_BuildValue("i",Pkg->ID));
#
MkGet(PackageGetAuto,Py_BuildValue("i",(Pkg->Flags & pkgCache::Flag::Auto) != 0));
MkGet(PackageGetEssential,Py_BuildValue("i",(Pkg->Flags & pkgCache::Flag::Essential) != 0));
MkGet(PackageGetImportant,Py_BuildValue("i",(Pkg->Flags & pkgCache::Flag::Important) != 0));
#undef MkGet

static PyObject *PackageGetVersionList(PyObject *Self,void*)
{
   pkgCache::PkgIterator &Pkg = GetCpp<pkgCache::PkgIterator>(Self);
   PyObject *Owner = GetOwner<pkgCache::PkgIterator>(Self);

   PyObject *List = PyList_New(0);
   for (pkgCache::VerIterator I = Pkg.VersionList(); I.end() == false; I++)
   {
      PyObject *Obj;
      Obj = CppOwnedPyObject_NEW<pkgCache::VerIterator>(Owner,&VersionType,I);
      PyList_Append(List,Obj);
      Py_DECREF(Obj);
   }
   return List;
}
static PyObject *PackageGetCurrentVer(PyObject *Self,void*)
{
   pkgCache::PkgIterator &Pkg = GetCpp<pkgCache::PkgIterator>(Self);
   PyObject *Owner = GetOwner<pkgCache::PkgIterator>(Self);
   if (Pkg->CurrentVer == 0)
   {
      Py_INCREF(Py_None);
      return Py_None;
   }
   return CppOwnedPyObject_NEW<pkgCache::VerIterator>(Owner,&VersionType,
							 Pkg.CurrentVer());
}

static PyGetSetDef PackageGetSet[] = {
    {"name",PackageGetName},
    {"section",PackageGetSection},
    {"rev_depends_list",PackageGetRevDependsList},
    {"provides_list",PackageGetProvidesList},
    {"selected_state",PackageGetSelectedState},
    {"inst_state",PackageGetInstState},
    {"current_state",PackageGetCurrentState},
    {"id",PackageGetID},
    {"auto",PackageGetAuto},
    {"essential",PackageGetEssential},
    {"important",PackageGetImportant},
    {"version_list",PackageGetVersionList},
    {"current_ver",PackageGetCurrentVer},
    #ifdef COMPAT_0_7
    {"Name",PackageGetName},
    {"Section",PackageGetSection},
    {"RevDependsList",PackageGetRevDependsList},
    {"ProvidesList",PackageGetProvidesList},
    {"SelectedState",PackageGetSelectedState},
    {"InstState",PackageGetInstState},
    {"CurrentState",PackageGetCurrentState},
    {"ID",PackageGetID},
    {"Auto",PackageGetAuto},
    {"Essential",PackageGetEssential},
    {"Important",PackageGetImportant},
    {"VersionList",PackageGetVersionList},
    {"CurrentVer",PackageGetCurrentVer},
    #endif
    {}
};

static PyObject *PackageRepr(PyObject *Self)
{
   pkgCache::PkgIterator &Pkg = GetCpp<pkgCache::PkgIterator>(Self);

   char S[300];
   snprintf(S,sizeof(S),"<pkgCache::Package object: Name:'%s' Section: '%s'"
	                " ID:%u Flags:0x%lX>",
	    Pkg.Name(),Pkg.Section(),Pkg->ID,Pkg->Flags);
   return PyString_FromString(S);
}

PyTypeObject PackageType =
{
   PyObject_HEAD_INIT(&PyType_Type)
   #if PY_MAJOR_VERSION < 3
   0,			                // ob_size
   #endif
   "apt_pkg.Package",                 // tp_name
   sizeof(CppOwnedPyObject<pkgCache::PkgIterator>),   // tp_basicsize
   0,                                   // tp_itemsize
   // Methods
   CppOwnedDealloc<pkgCache::PkgIterator>,  // tp_dealloc
   0,                                   // tp_print
   0,                                   // tp_getattr
   0,                                   // tp_setattr
   0,                                   // tp_compare
   PackageRepr,                         // tp_repr
   0,                                   // tp_as_number
   0,                                   // tp_as_sequence
   0,			                // tp_as_mapping
   0,                                   // tp_hash
   0,                                   // tp_call
   0,                                   // tp_str
   0,                                   // tp_getattro
   0,                                   // tp_setattro
   0,                                   // tp_as_buffer
   Py_TPFLAGS_DEFAULT,                  // tp_flags
   "Package Object",                    // tp_doc
   0,                                   // tp_traverse
   0,                                   // tp_clear
   0,                                   // tp_richcompare
   0,                                   // tp_weaklistoffset
   0,                                   // tp_iter
   0,                                   // tp_iternext
   0,                                   // tp_methods
   0,                                   // tp_members
   PackageGetSet,                       // tp_getset
};

#define Description_MkGet(PyFunc,Ret) static PyObject \
   *PyFunc(PyObject *Self,void*) { \
       pkgCache::DescIterator &Desc = GetCpp<pkgCache::DescIterator>(Self); \
       return Ret; }

Description_MkGet(DescriptionGetLanguageCode,
                  PyString_FromString(Desc.LanguageCode()));
Description_MkGet(DescriptionGetMd5,Safe_FromString(Desc.md5()));
#undef Description_MkGet

static PyObject *DescriptionGetFileList(PyObject *Self,void*)
{
   pkgCache::DescIterator &Desc = GetCpp<pkgCache::DescIterator>(Self);
   PyObject *Owner = GetOwner<pkgCache::DescIterator>(Self);

   /* The second value in the tuple is the index of the VF item. If the
      user wants to request a lookup then that number will be used.
      Maybe later it can become an object. */
   PyObject *List = PyList_New(0);
   for (pkgCache::DescFileIterator I = Desc.FileList(); I.end() == false; I++)
   {
      PyObject *DescFile;
      PyObject *Obj;
      DescFile = CppOwnedPyObject_NEW<pkgCache::PkgFileIterator>(Owner,&PackageFileType,I.File());
      Obj = Py_BuildValue("Nl",DescFile,I.Index());
      PyList_Append(List,Obj);
      Py_DECREF(Obj);
   }
   return List;
}

static PyGetSetDef DescriptionGetSet[] = {
    {"language_code",DescriptionGetLanguageCode},
    {"md5",DescriptionGetMd5},
    {"file_list",DescriptionGetFileList},
    #ifdef COMPAT_0_7
    {"LanguageCode",DescriptionGetLanguageCode},
    {"FileList",DescriptionGetFileList},
    #endif
    {}
};

static PyObject *DescriptionRepr(PyObject *Self)
{
   pkgCache::DescIterator &Desc = GetCpp<pkgCache::DescIterator>(Self);

   char S[300];
   snprintf(S,sizeof(S),
	    "<pkgCache::Description object: language_code:'%s' md5:'%s' ",
	    Desc.LanguageCode(), Desc.md5());
   return PyString_FromString(S);
}

PyTypeObject DescriptionType =
{
   PyObject_HEAD_INIT(&PyType_Type)
   #if PY_MAJOR_VERSION < 3
   0,			                // ob_size
   #endif
   "apt_pkg.Description",               // tp_name
   sizeof(CppOwnedPyObject<pkgCache::DescIterator>),   // tp_basicsize
   0,                                   // tp_itemsize
   // Methods
   CppOwnedDealloc<pkgCache::DescIterator>,          // tp_dealloc
   0,                                   // tp_print
   0,                                   // tp_getattr
   0,                                   // tp_setattr
   0,                                   // tp_compare
   DescriptionRepr,                         // tp_repr
   0,                                   // tp_as_number
   0,		                        // tp_as_sequence
   0,			                // tp_as_mapping
   0,                                   // tp_hash
   0,                                   // tp_call
   0,                                   // tp_str
   0,                                   // tp_getattro
   0,                                   // tp_setattro
   0,                                   // tp_as_buffer
   Py_TPFLAGS_DEFAULT,                  // tp_flags
   "AcquireItem Object",                // tp_doc
   0,                                   // tp_traverse
   0,                                   // tp_clear
   0,                                   // tp_richcompare
   0,                                   // tp_weaklistoffset
   0,                                   // tp_iter
   0,                                   // tp_iternext
   0,                                   // tp_methods
   0,                                   // tp_members
   DescriptionGetSet,                   // tp_getset
};
									/*}}}*/
// Version Class							/*{{{*/
// ---------------------------------------------------------------------

/* This is the simple depends result, the elements are split like
   ParseDepends does */
static PyObject *MakeDepends(PyObject *Owner,pkgCache::VerIterator &Ver,
			     bool AsObj)
{
   PyObject *Dict = PyDict_New();
   PyObject *LastDep = 0;
   unsigned LastDepType = 0;
   for (pkgCache::DepIterator D = Ver.DependsList(); D.end() == false;)
   {
      pkgCache::DepIterator Start;
      pkgCache::DepIterator End;
      D.GlobOr(Start,End);

      // Switch/create a new dict entry
      if (LastDepType != Start->Type || LastDep != 0)
      {
	 // must be in sync with pkgCache::DepType in libapt
	 // it sucks to have it here duplicated, but we get it
	 // translated from libapt and that is certainly not what
	 // we want in a programing interface
	 const char *Types[] =
	 {
	    "", "Depends","PreDepends","Suggests",
	    "Recommends","Conflicts","Replaces",
	    "Obsoletes", "Breaks"
	 };
	 PyObject *Dep = PyString_FromString(Types[Start->Type]);
	 LastDepType = Start->Type;
	 LastDep = PyDict_GetItem(Dict,Dep);
	 if (LastDep == 0)
	 {
	    LastDep = PyList_New(0);
	    PyDict_SetItem(Dict,Dep,LastDep);
	    Py_DECREF(LastDep);
	 }
	 Py_DECREF(Dep);
      }

      PyObject *OrGroup = PyList_New(0);
      while (1)
      {
	 PyObject *Obj;
	 if (AsObj == true)
	    Obj = CppOwnedPyObject_NEW<pkgCache::DepIterator>(Owner,&DependencyType,
							 Start);
	 else
	 {
	    if (Start->Version == 0)
	       Obj = Py_BuildValue("sss",
				   Start.TargetPkg().Name(),
				   "",
				   Start.CompType());
	    else
	       Obj = Py_BuildValue("sss",
				   Start.TargetPkg().Name(),
				   Start.TargetVer(),
				   Start.CompType());
	 }
	 PyList_Append(OrGroup,Obj);
	 Py_DECREF(Obj);

	 if (Start == End)
	    break;
	 Start++;
      }

      PyList_Append(LastDep,OrGroup);
      Py_DECREF(OrGroup);
   }

   return Dict;
}

static inline pkgCache::VerIterator Version_GetVer(PyObject *Self) {
   return GetCpp<pkgCache::VerIterator>(Self);
}

// Version attributes.
static PyObject *VersionGetVerStr(PyObject *Self, void*) {
   return PyString_FromString(Version_GetVer(Self).VerStr());
}
static PyObject *VersionGetSection(PyObject *Self, void*) {
   return Safe_FromString(Version_GetVer(Self).Section());
}
static PyObject *VersionGetArch(PyObject *Self, void*) {
   return Safe_FromString(Version_GetVer(Self).Arch());
}
static PyObject *VersionGetFileList(PyObject *Self, void*) {
   pkgCache::VerIterator &Ver = GetCpp<pkgCache::VerIterator>(Self);
   PyObject *Owner = GetOwner<pkgCache::VerIterator>(Self);
   PyObject *List = PyList_New(0);
   for (pkgCache::VerFileIterator I = Ver.FileList(); I.end() == false; I++)
   {
      PyObject *PkgFile;
      PyObject *Obj;
      PkgFile = CppOwnedPyObject_NEW<pkgCache::PkgFileIterator>(Owner,&PackageFileType,I.File());
      Obj = Py_BuildValue("Nl",PkgFile,I.Index());
      PyList_Append(List,Obj);
      Py_DECREF(Obj);
   }
   return List;
}

static PyObject *VersionGetDependsListStr(PyObject *Self, void*) {
   pkgCache::VerIterator &Ver = GetCpp<pkgCache::VerIterator>(Self);
   PyObject *Owner = GetOwner<pkgCache::VerIterator>(Self);
   return MakeDepends(Owner,Ver,false);
}
static PyObject *VersionGetDependsList(PyObject *Self, void*) {
   pkgCache::VerIterator &Ver = GetCpp<pkgCache::VerIterator>(Self);
   PyObject *Owner = GetOwner<pkgCache::VerIterator>(Self);
   return MakeDepends(Owner,Ver,true);
}
static PyObject *VersionGetParentPkg(PyObject *Self, void*) {
   PyObject *Owner = GetOwner<pkgCache::VerIterator>(Self);
   return CppOwnedPyObject_NEW<pkgCache::PkgIterator>(Owner,&PackageType,
                                                      Version_GetVer(Self).ParentPkg());
}
static PyObject *VersionGetProvidesList(PyObject *Self, void*) {
   PyObject *Owner = GetOwner<pkgCache::VerIterator>(Self);
   return CreateProvides(Owner,Version_GetVer(Self).ProvidesList());
}
static PyObject *VersionGetSize(PyObject *Self, void*) {
   return Py_BuildValue("i", Version_GetVer(Self)->Size);
}
static PyObject *VersionGetInstalledSize(PyObject *Self, void*) {
   return Py_BuildValue("i", Version_GetVer(Self)->InstalledSize);
}
static PyObject *VersionGetHash(PyObject *Self, void*) {
   return Py_BuildValue("i", Version_GetVer(Self)->Hash);
}
static PyObject *VersionGetID(PyObject *Self, void*) {
   return Py_BuildValue("i", Version_GetVer(Self)->ID);
}
static PyObject *VersionGetPriority(PyObject *Self, void*) {
   return Py_BuildValue("i",Version_GetVer(Self)->Priority);
}
static PyObject *VersionGetPriorityStr(PyObject *Self, void*) {
   return Safe_FromString(Version_GetVer(Self).PriorityType());
}
static PyObject *VersionGetDownloadable(PyObject *Self, void*) {
   return Py_BuildValue("b",Version_GetVer(Self).Downloadable());
}
static PyObject *VersionGetTranslatedDescription(PyObject *Self, void*) {
   pkgCache::VerIterator &Ver = GetCpp<pkgCache::VerIterator>(Self);
   PyObject *Owner = GetOwner<pkgCache::VerIterator>(Self);
   return CppOwnedPyObject_NEW<pkgCache::DescIterator>(Owner,
                    &DescriptionType,
                    Ver.TranslatedDescription());
}

#if 0 // FIXME: enable once pkgSourceList is stored somewhere
static PyObject *VersionGetIsTrusted(PyObject *Self, void*) {
   else if (strcmp("IsTrusted", Name) == 0)
   {
      pkgSourceList Sources;
      Sources.ReadMainList();
      for(pkgCache::VerFileIterator i = Ver.FileList(); !i.end(); i++)
      {
	 pkgIndexFile *index;
	 if(Sources.FindIndex(i.File(), index) && !index->IsTrusted())
	    return Py_BuildValue("b", false);
      }
      return Py_BuildValue("b", true);
   }
}
#endif


static PyObject *VersionRepr(PyObject *Self)
{
   pkgCache::VerIterator &Ver = GetCpp<pkgCache::VerIterator>(Self);

   char S[300];
   snprintf(S,sizeof(S),"<apt_pkg.Version object: Pkg:'%s' Ver:'%s' "
	                "Section:'%s' Arch:'%s' Size:%lu ISize:%lu Hash:%u "
	                "ID:%u Priority:%u>",
	    Ver.ParentPkg().Name(),Ver.VerStr(),Ver.Section(),Ver.Arch(),
	    (unsigned long)Ver->Size,(unsigned long)Ver->InstalledSize,
	    Ver->Hash,Ver->ID,Ver->Priority);
   return PyString_FromString(S);
}

static PyGetSetDef VersionGetSet[] = {
   {"arch",VersionGetArch},
   {"depends_list",VersionGetDependsList},
   {"depends_list_str",VersionGetDependsListStr},
   {"downloadable",VersionGetDownloadable},
   {"file_list",VersionGetFileList},
   {"hash",VersionGetHash},
   {"id",VersionGetID},
   {"installed_size",VersionGetInstalledSize},
   {"parent_pkg",VersionGetParentPkg},
   {"priority",VersionGetPriority},
   {"priority_str",VersionGetPriorityStr},
   {"provides_list",VersionGetProvidesList},
   {"section",VersionGetSection},
   {"size",VersionGetSize},
   {"translated_description",VersionGetTranslatedDescription},
   {"ver_str",VersionGetVerStr},
#ifdef COMPAT_0_7
   {"Arch",VersionGetArch},
   {"DependsList",VersionGetDependsList},
   {"DependsListStr",VersionGetDependsListStr},
   {"Downloadable",VersionGetDownloadable},
   {"FileList",VersionGetFileList},
   {"Hash",VersionGetHash},
   {"ID",VersionGetID},
   {"InstalledSize",VersionGetInstalledSize},
   {"ParentPkg",VersionGetParentPkg},
   {"Priority",VersionGetPriority},
   {"PriorityStr",VersionGetPriorityStr},
   {"ProvidesList",VersionGetProvidesList},
   {"Section",VersionGetSection},
   {"Size",VersionGetSize},
   {"TranslationDescription",VersionGetTranslatedDescription},
   {"VerStr",VersionGetVerStr},
#endif
   {}
};

PyTypeObject VersionType =
{
   PyObject_HEAD_INIT(&PyType_Type)
   #if PY_MAJOR_VERSION < 3
   0,			                // ob_size
   #endif
   "apt_pkg.Version",                   // tp_name
   sizeof(CppOwnedPyObject<pkgCache::VerIterator>),   // tp_basicsize
   0,                                   // tp_itemsize
   // Methods
   CppOwnedDealloc<pkgCache::VerIterator>,          // tp_dealloc
   0,                                   // tp_print
   0,                                   // tp_getattr
   0,                                   // tp_setattr
   0,                                   // tp_compare
   VersionRepr,                         // tp_repr
   0,                                   // tp_as_number
   0,		                        // tp_as_sequence
   0,			                // tp_as_mapping
   0,                                   // tp_hash
   0,                                   // tp_call
   0,                                   // tp_str
   0,                                   // tp_getattro
   0,                                   // tp_setattro
   0,                                   // tp_as_buffer
   Py_TPFLAGS_DEFAULT,                  // tp_flags
   "Version Object",                    // tp_doc
   0,                                   // tp_traverse
   0,                                   // tp_clear
   0,                                   // tp_richcompare
   0,                                   // tp_weaklistoffset
   0,                                   // tp_iter
   0,                                   // tp_iternext
   0,                                   // tp_methods
   0,                                   // tp_members
   VersionGetSet,                       // tp_getset
};

									/*}}}*/

// PackageFile Class							/*{{{*/
// ---------------------------------------------------------------------
static PyObject *PackageFile_GetFileName(PyObject *Self,void*)
{
    pkgCache::PkgFileIterator &File = GetCpp<pkgCache::PkgFileIterator>(Self);
    return Safe_FromString(File.FileName());
}

static PyObject *PackageFile_GetArchive(PyObject *Self,void*)
{
    pkgCache::PkgFileIterator &File = GetCpp<pkgCache::PkgFileIterator>(Self);
    return Safe_FromString(File.Archive());
}

static PyObject *PackageFile_GetComponent(PyObject *Self,void*)
{
    pkgCache::PkgFileIterator &File = GetCpp<pkgCache::PkgFileIterator>(Self);
    return Safe_FromString(File.Component());
}

static PyObject *PackageFile_GetVersion(PyObject *Self,void*)
{
    pkgCache::PkgFileIterator &File = GetCpp<pkgCache::PkgFileIterator>(Self);
    return Safe_FromString(File.Version());
}

static PyObject *PackageFile_GetOrigin(PyObject *Self,void*)
{
    pkgCache::PkgFileIterator &File = GetCpp<pkgCache::PkgFileIterator>(Self);
    return Safe_FromString(File.Origin());
}

static PyObject *PackageFile_GetLabel(PyObject *Self,void*)
{
    pkgCache::PkgFileIterator &File = GetCpp<pkgCache::PkgFileIterator>(Self);
    return Safe_FromString(File.Label());
}

static PyObject *PackageFile_GetArchitecture(PyObject *Self,void*)
{
    pkgCache::PkgFileIterator &File = GetCpp<pkgCache::PkgFileIterator>(Self);
    return Safe_FromString(File.Architecture());
}

static PyObject *PackageFile_GetSite(PyObject *Self,void*)
{
    pkgCache::PkgFileIterator &File = GetCpp<pkgCache::PkgFileIterator>(Self);
    return Safe_FromString(File.Site());
}

static PyObject *PackageFile_GetIndexType(PyObject *Self,void*)
{
    pkgCache::PkgFileIterator &File = GetCpp<pkgCache::PkgFileIterator>(Self);
    return Safe_FromString(File.IndexType());
}
static PyObject *PackageFile_GetSize(PyObject *Self,void*)
{
    pkgCache::PkgFileIterator &File = GetCpp<pkgCache::PkgFileIterator>(Self);
    return Py_BuildValue("i",File->Size);
}

static PyObject *PackageFile_GetNotSource(PyObject *Self,void*)
{
    pkgCache::PkgFileIterator &File = GetCpp<pkgCache::PkgFileIterator>(Self);
    return Py_BuildValue("i",(File->Flags & pkgCache::Flag::NotSource) != 0);
}
static PyObject *PackageFile_GetNotAutomatic(PyObject *Self,void*)
{
    pkgCache::PkgFileIterator &File = GetCpp<pkgCache::PkgFileIterator>(Self);
    return Py_BuildValue("i",(File->Flags & pkgCache::Flag::NotSource) != 0);
}

static PyObject *PackageFile_GetID(PyObject *Self,void*)
{
    pkgCache::PkgFileIterator &File = GetCpp<pkgCache::PkgFileIterator>(Self);
    return Py_BuildValue("i",File->ID);
}

static PyObject *PackageFileRepr(PyObject *Self)
{
    pkgCache::PkgFileIterator &File = GetCpp<pkgCache::PkgFileIterator>(Self);

    char S[300];
    snprintf(S,sizeof(S),"<apt_pkg.PackageFile object: "
             "File:'%s' a=%s,c=%s,v=%s,o=%s,l=%s "
             "Arch='%s' Site='%s' IndexType='%s' Size=%lu "
             "Flags=0x%lX ID:%u>",
             File.FileName(),File.Archive(),File.Component(),File.Version(),
             File.Origin(),File.Label(),File.Architecture(),File.Site(),
             File.IndexType(),File->Size,File->Flags,File->ID);
    return PyString_FromString(S);
}

static PyGetSetDef PackageFileGetSet[] = {
  {(char*)"architecture",PackageFile_GetArchitecture},
  {(char*)"archive",PackageFile_GetArchive},
  {(char*)"component",PackageFile_GetComponent},
  {(char*)"filename",PackageFile_GetFileName},
  {(char*)"id",PackageFile_GetID},
  {(char*)"index_type",PackageFile_GetIndexType},
  {(char*)"label",PackageFile_GetLabel},
  {(char*)"not_automatic",PackageFile_GetNotAutomatic},
  {(char*)"not_source",PackageFile_GetNotSource},
  {(char*)"origin",PackageFile_GetOrigin},
  {(char*)"site",PackageFile_GetSite},
  {(char*)"size",PackageFile_GetSize},
  {(char*)"version",PackageFile_GetVersion},
  #ifdef COMPAT_0_7
  {"Architecture",PackageFile_GetArchitecture},
  {"Archive",PackageFile_GetArchive},
  {"Component",PackageFile_GetComponent},
  {"FileName",PackageFile_GetFileName},
  {"ID",PackageFile_GetID},
  {"IndexType",PackageFile_GetIndexType},
  {"Label",PackageFile_GetLabel},
  {"NotAutomatic",PackageFile_GetNotAutomatic},
  {"NotSource",PackageFile_GetNotSource},
  {"Origin",PackageFile_GetOrigin},
  {"Site",PackageFile_GetSite},
  {"Size",PackageFile_GetSize},
  {"Version",PackageFile_GetVersion},
  #endif
  {}
};

PyTypeObject PackageFileType = {
   PyObject_HEAD_INIT(&PyType_Type)
   #if PY_MAJOR_VERSION < 3
   0,                                                    // ob_size
   #endif
   "apt_pkg.PackageFile",                                // tp_name
   sizeof(CppOwnedPyObject<pkgCache::PkgFileIterator>),  // tp_basicsize
   0,                                                    // tp_itemsize
   CppOwnedDealloc<pkgCache::PkgFileIterator>,           // tp_dealloc
   0,                                                    // tp_print
   0,                                                    // tp_getattr
   0,                                                    // tp_setattr
   0,                                                    // tp_compare
   PackageFileRepr,                                      // tp_repr
   0,                                                    // tp_as_number
   0,                                                    // tp_as_sequence
   0,                                                    // tp_as_mapping
   0,                                                    // tp_hash
   0,                                                    // tp_call
   0,                                                    // tp_str
   0,                                                    // tp_getattro
   0,                                                    // tp_setattro
   0,                                                    // tp_as_buffer
   Py_TPFLAGS_DEFAULT,                                   // tp_flags
   "apt_pkg.PackageFile Object",                         // tp_doc
   0,                                                    // tp_traverse
   0,                                                    // tp_clear
   0,                                                    // tp_richcompare
   0,                                                    // tp_weaklistoffset
   0,                                                    // tp_iter
   0,                                                    // tp_iternext
   0,                                                    // tp_methods
   0,                                                    // tp_members
   PackageFileGetSet,                                    // tp_getset
};

// depends class
static PyObject *DependencyRepr(PyObject *Self)
{
   pkgCache::DepIterator &Dep = GetCpp<pkgCache::DepIterator>(Self);

   char S[300];
   snprintf(S,sizeof(S),"<pkgCache::Dependency object: "
	                "Pkg:'%s' Ver:'%s' Comp:'%s'>",
	    Dep.TargetPkg().Name(),
	    (Dep.TargetVer() == 0?"":Dep.TargetVer()),
	    Dep.CompType());
   return PyString_FromString(S);
}

static PyObject *DepSmartTargetPkg(PyObject *Self,PyObject *Args)
{
   if (PyArg_ParseTuple(Args,"") == 0)
      return 0;

   pkgCache::DepIterator &Dep = GetCpp<pkgCache::DepIterator>(Self);
   PyObject *Owner = GetOwner<pkgCache::DepIterator>(Self);

   pkgCache::PkgIterator P;
   if (Dep.SmartTargetPkg(P) == false)
   {
      Py_INCREF(Py_None);
      return Py_None;
   }

   return CppOwnedPyObject_NEW<pkgCache::PkgIterator>(Owner,&PackageType,P);
}

static PyObject *DepAllTargets(PyObject *Self,PyObject *Args)
{
   if (PyArg_ParseTuple(Args,"") == 0)
      return 0;

   pkgCache::DepIterator &Dep = GetCpp<pkgCache::DepIterator>(Self);
   PyObject *Owner = GetOwner<pkgCache::DepIterator>(Self);

   SPtr<pkgCache::Version *> Vers = Dep.AllTargets();
   PyObject *List = PyList_New(0);
   for (pkgCache::Version **I = Vers; *I != 0; I++)
   {
      PyObject *Obj;
      Obj = CppOwnedPyObject_NEW<pkgCache::VerIterator>(Owner,&VersionType,
							pkgCache::VerIterator(*Dep.Cache(),*I));
      PyList_Append(List,Obj);
      Py_DECREF(Obj);
   }
   return List;
}

static PyMethodDef DependencyMethods[] =
{
   {"smart_target_pkg",DepSmartTargetPkg,METH_VARARGS,"Returns the natural Target or None"},
   {"all_targets",DepAllTargets,METH_VARARGS,"Returns all possible Versions that match this dependency"},
#ifdef COMPAT_0_7
   {"SmartTargetPkg",DepSmartTargetPkg,METH_VARARGS,"Returns the natural Target or None"},
   {"AllTargets",DepAllTargets,METH_VARARGS,"Returns all possible Versions that match this dependency"},
#endif
   {}
};

// Dependency Class							/*{{{*/
// ---------------------------------------------------------------------

static PyObject *DependencyGetTargetVer(PyObject *Self,void*)
{
   pkgCache::DepIterator &Dep = GetCpp<pkgCache::DepIterator>(Self);
   if (Dep->Version == 0)
      return PyString_FromString("");
   return PyString_FromString(Dep.TargetVer());
}

static PyObject *DependencyGetTargetPkg(PyObject *Self,void*)
{
   pkgCache::DepIterator &Dep = GetCpp<pkgCache::DepIterator>(Self);
   PyObject *Owner = GetOwner<pkgCache::DepIterator>(Self);
   return CppOwnedPyObject_NEW<pkgCache::PkgIterator>(Owner,&PackageType,
                                                      Dep.TargetPkg());
}

static PyObject *DependencyGetParentVer(PyObject *Self,void*)
{
   pkgCache::DepIterator &Dep = GetCpp<pkgCache::DepIterator>(Self);
   PyObject *Owner = GetOwner<pkgCache::DepIterator>(Self);
   return CppOwnedPyObject_NEW<pkgCache::VerIterator>(Owner,&VersionType,
                                                      Dep.ParentVer());
}

static PyObject *DependencyGetParentPkg(PyObject *Self,void*)
{
   pkgCache::DepIterator &Dep = GetCpp<pkgCache::DepIterator>(Self);
   PyObject *Owner = GetOwner<pkgCache::DepIterator>(Self);
   return CppOwnedPyObject_NEW<pkgCache::PkgIterator>(Owner,&PackageType,
                                                      Dep.ParentPkg());
}

static PyObject *DependencyGetCompType(PyObject *Self,void*)
{
   pkgCache::DepIterator &Dep = GetCpp<pkgCache::DepIterator>(Self);
   return PyString_FromString(Dep.CompType());
}

static PyObject *DependencyGetDepType(PyObject *Self,void*)
{
   pkgCache::DepIterator &Dep = GetCpp<pkgCache::DepIterator>(Self);
   return PyString_FromString(Dep.DepType());
}

static PyObject *DependencyGetID(PyObject *Self,void*)
{
   pkgCache::DepIterator &Dep = GetCpp<pkgCache::DepIterator>(Self);
   return Py_BuildValue("i",Dep->ID);
}

static PyGetSetDef DependencyGetSet[] = {
   {"comp_type",DependencyGetCompType},
   {"dep_type",DependencyGetDepType},
   {"id",DependencyGetID},
   {"parent_pkg",DependencyGetParentPkg},
   {"parent_ver",DependencyGetParentVer},
   {"target_pkg",DependencyGetTargetPkg},
   {"target_ver",DependencyGetTargetVer},
#ifdef COMPAT_0_7
   {"CompType",DependencyGetCompType},
   {"DepType",DependencyGetDepType},
   {"ID",DependencyGetID},
   {"ParentPkg",DependencyGetParentPkg},
   {"ParentVer",DependencyGetParentVer},
   {"TargetPkg",DependencyGetTargetPkg},
   {"TargetVer",DependencyGetTargetVer},
#endif
   {}
};


PyTypeObject DependencyType =
{
   PyObject_HEAD_INIT(&PyType_Type)
   #if PY_MAJOR_VERSION < 3
   0,			                // ob_size
   #endif
   "apt_pkg.Dependency",                // tp_name
   sizeof(CppOwnedPyObject<pkgCache::DepIterator>),   // tp_basicsize
   0,                                   // tp_itemsize
   // Methods
   CppOwnedDealloc<pkgCache::DepIterator>,          // tp_dealloc
   0,                                   // tp_print
   0,                                   // tp_getattr
   0,                                   // tp_setattr
   0,                                   // tp_compare
   DependencyRepr,                      // tp_repr
   0,                                   // tp_as_number
   0,		                        // tp_as_sequence
   0,			                // tp_as_mapping
   0,                                   // tp_hash
   0,                                   // tp_call
   0,                                   // tp_str
   0,                                   // tp_getattro
   0,                                   // tp_setattro
   0,                                   // tp_as_buffer
   Py_TPFLAGS_DEFAULT,                  // tp_flags
   "Dependency Object",                 // tp_doc
   0,                                   // tp_traverse
   0,                                   // tp_clear
   0,                                   // tp_richcompare
   0,                                   // tp_weaklistoffset
   0,                                   // tp_iter
   0,                                   // tp_iternext
   DependencyMethods,                   // tp_methods
   0,                                   // tp_members
   DependencyGetSet,                    // tp_getset
};

									/*}}}*/
									/*}}}*/
// Reverse Dependency List Class					/*{{{*/
// ---------------------------------------------------------------------
static Py_ssize_t RDepListLen(PyObject *Self)
{
   return GetCpp<RDepListStruct>(Self).Len;
}

static PyObject *RDepListItem(PyObject *iSelf,Py_ssize_t Index)
{
   RDepListStruct &Self = GetCpp<RDepListStruct>(iSelf);
   if (Index < 0 || (unsigned)Index >= Self.Len)
   {
      PyErr_SetNone(PyExc_IndexError);
      return 0;
   }

   if ((unsigned)Index < Self.LastIndex)
   {
      Self.LastIndex = 0;
      Self.Iter = Self.Start;
   }

   while ((unsigned)Index > Self.LastIndex)
   {
      Self.LastIndex++;
      Self.Iter++;
      if (Self.Iter.end() == true)
      {
	 PyErr_SetNone(PyExc_IndexError);
	 return 0;
      }
   }

   return CppOwnedPyObject_NEW<pkgCache::DepIterator>(GetOwner<RDepListStruct>(iSelf),
						      &DependencyType,Self.Iter);
}

static PySequenceMethods RDepListSeq =
{
   RDepListLen,
   0,                // concat
   0,                // repeat
   RDepListItem,
   0,                // slice
   0,                // assign item
   0                 // assign slice
};

PyTypeObject RDepListType =
{
   PyObject_HEAD_INIT(&PyType_Type)
   #if PY_MAJOR_VERSION < 3
   0,			                // ob_size
   #endif
   "apt_pkg.DependencyList",             // tp_name
   sizeof(CppOwnedPyObject<RDepListStruct>),   // tp_basicsize
   0,                                   // tp_itemsize
   // Methods
   CppOwnedDealloc<RDepListStruct>,      // tp_dealloc
   0,                                   // tp_print
   0,                                   // tp_getattr
   0,                                   // tp_setattr
   0,                                   // tp_compare
   0,                                   // tp_repr
   0,                                   // tp_as_number
   &RDepListSeq,                         // tp_as_sequence
   0,			                // tp_as_mapping
   0,                                   // tp_hash
};

									/*}}}*/


#ifdef COMPAT_0_7
PyObject *TmpGetCache(PyObject *Self,PyObject *Args)
{
    return PkgCacheNew(&PkgCacheType,Args,0);
}
#endif
