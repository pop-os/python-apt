// -*- mode: cpp; mode: fold -*-
// Description								/*{{{*/
// $Id: depcache.cc,v 1.5 2003/06/03 03:03:23 mdz Exp $
/* ######################################################################

   DepCache - Wrapper for the depcache related functions

   ##################################################################### */
									/*}}}*/
// Include Files							/*{{{*/
#include "generic.h"
#include "apt_pkgmodule.h"

#include <apt-pkg/pkgcache.h>
#include <apt-pkg/cachefile.h>
#include <apt-pkg/algorithms.h>
#include <apt-pkg/policy.h>
#include <apt-pkg/sptr.h>

#include <Python.h>

#include <iostream>


// DepCache Class								/*{{{*/
// ---------------------------------------------------------------------

struct PkgDepCacheStruct
{
   pkgDepCache *depcache;
   pkgPolicy *policy;

   PkgDepCacheStruct(pkgCache *Cache) {
      policy = new pkgPolicy(Cache);
      depcache = new pkgDepCache(Cache);
   }
   virtual ~PkgDepCacheStruct() {
      delete depcache;
      delete policy;
   };


   PkgDepCacheStruct() {abort();};
};



static PyObject *PkgDepCacheInit(PyObject *Self,PyObject *Args)
{   
   PkgDepCacheStruct &Struct = GetCpp<PkgDepCacheStruct>(Self);

   Struct.depcache->Init(0);

   return HandleErrors(Py_None);   
}

static PyObject *PkgDepCacheGetCandidateVer(PyObject *Self,PyObject *Args)
{ 
   PkgDepCacheStruct &Struct = GetCpp<PkgDepCacheStruct>(Self);
   PyObject *PackageObj;
   PyObject *CandidateObj;
   if (PyArg_ParseTuple(Args,"O!",&PackageType,&PackageObj) == 0)
      return 0;

   pkgCache::PkgIterator &Pkg = GetCpp<pkgCache::PkgIterator>(PackageObj);
   pkgCache::VerIterator I = Struct.depcache->GetCandidateVer(Pkg);
   CandidateObj = CppOwnedPyObject_NEW<pkgCache::VerIterator>(PackageObj,&VersionType,I);

   return CandidateObj;
}

static PyObject *PkgDepCacheUpgrade(PyObject *Self,PyObject *Args)
{   
   PkgDepCacheStruct &Struct = GetCpp<PkgDepCacheStruct>(Self);

   char *distUpgrade=0;
   if (PyArg_ParseTuple(Args,"|b",&distUpgrade) == 0)
      return 0;

   if(distUpgrade)
      pkgDistUpgrade(*Struct.depcache);
   else
      pkgAllUpgrade(*Struct.depcache);

   return HandleErrors(Py_None);   
}

static PyObject *PkgDepCacheFixBroken(PyObject *Self,PyObject *Args)
{   
   PkgDepCacheStruct &Struct = GetCpp<PkgDepCacheStruct>(Self);

   if (PyArg_ParseTuple(Args,"") == 0)
      return 0;

   pkgFixBroken(*Struct.depcache);

   return HandleErrors(Py_None);   
}


static PyObject *PkgDepCacheMarkKeep(PyObject *Self,PyObject *Args)
{   
   PkgDepCacheStruct &Struct = GetCpp<PkgDepCacheStruct>(Self);

   PyObject *PackageObj;
   if (PyArg_ParseTuple(Args,"O!",&PackageType,&PackageObj) == 0)
      return 0;

   pkgCache::PkgIterator &Pkg = GetCpp<pkgCache::PkgIterator>(PackageObj);
   Struct.depcache->MarkKeep(Pkg);

   return HandleErrors(Py_None);   
}

static PyObject *PkgDepCacheMarkDelete(PyObject *Self,PyObject *Args)
{   
   PkgDepCacheStruct &Struct = GetCpp<PkgDepCacheStruct>(Self);

   PyObject *PackageObj;
   char purge = 0;
   if (PyArg_ParseTuple(Args,"O!|b",&PackageType,&PackageObj, &purge) == 0)
      return 0;

   pkgCache::PkgIterator &Pkg = GetCpp<pkgCache::PkgIterator>(PackageObj);
   Struct.depcache->MarkDelete(Pkg,purge);

   return HandleErrors(Py_None);   
}

static PyObject *PkgDepCacheMarkInstall(PyObject *Self,PyObject *Args)
{   
   PkgDepCacheStruct &Struct = GetCpp<PkgDepCacheStruct>(Self);

   PyObject *PackageObj;
   if (PyArg_ParseTuple(Args,"O!",&PackageType,&PackageObj) == 0)
      return 0;

   pkgCache::PkgIterator &Pkg = GetCpp<pkgCache::PkgIterator>(PackageObj);
   Struct.depcache->MarkInstall(Pkg);

   return HandleErrors(Py_None);   
}

static PyObject *PkgDepCacheIsUpgradable(PyObject *Self,PyObject *Args)
{   
   PkgDepCacheStruct &Struct = GetCpp<PkgDepCacheStruct>(Self);

   PyObject *PackageObj;
   if (PyArg_ParseTuple(Args,"O!",&PackageType,&PackageObj) == 0)
      return 0;

   pkgCache::PkgIterator &Pkg = GetCpp<pkgCache::PkgIterator>(PackageObj);
   pkgDepCache::StateCache &state = (*Struct.depcache)[Pkg];

   return HandleErrors(Py_BuildValue("b",state.Upgradable()));   
}

static PyObject *PkgDepCacheIsNowBroken(PyObject *Self,PyObject *Args)
{   
   PkgDepCacheStruct &Struct = GetCpp<PkgDepCacheStruct>(Self);

   PyObject *PackageObj;
   if (PyArg_ParseTuple(Args,"O!",&PackageType,&PackageObj) == 0)
      return 0;

   pkgCache::PkgIterator &Pkg = GetCpp<pkgCache::PkgIterator>(PackageObj);
   pkgDepCache::StateCache &state = (*Struct.depcache)[Pkg];

   return HandleErrors(Py_BuildValue("b",state.NowBroken()));   
}

static PyObject *PkgDepCacheIsInstBroken(PyObject *Self,PyObject *Args)
{   
   PkgDepCacheStruct &Struct = GetCpp<PkgDepCacheStruct>(Self);

   PyObject *PackageObj;
   if (PyArg_ParseTuple(Args,"O!",&PackageType,&PackageObj) == 0)
      return 0;

   pkgCache::PkgIterator &Pkg = GetCpp<pkgCache::PkgIterator>(PackageObj);
   pkgDepCache::StateCache &state = (*Struct.depcache)[Pkg];

   return HandleErrors(Py_BuildValue("b",state.InstBroken()));   
}


static PyObject *PkgDepCacheMarkedInstall(PyObject *Self,PyObject *Args)
{   
   PkgDepCacheStruct &Struct = GetCpp<PkgDepCacheStruct>(Self);

   PyObject *PackageObj;
   if (PyArg_ParseTuple(Args,"O!",&PackageType,&PackageObj) == 0)
      return 0;

   pkgCache::PkgIterator &Pkg = GetCpp<pkgCache::PkgIterator>(PackageObj);
   pkgDepCache::StateCache &state = (*Struct.depcache)[Pkg];

   return HandleErrors(Py_BuildValue("b",state.Install()));   
}

static PyObject *PkgDepCacheMarkedUpgrade(PyObject *Self,PyObject *Args)
{   
   PkgDepCacheStruct &Struct = GetCpp<PkgDepCacheStruct>(Self);

   PyObject *PackageObj;
   if (PyArg_ParseTuple(Args,"O!",&PackageType,&PackageObj) == 0)
      return 0;

   pkgCache::PkgIterator &Pkg = GetCpp<pkgCache::PkgIterator>(PackageObj);
   pkgDepCache::StateCache &state = (*Struct.depcache)[Pkg];

   return HandleErrors(Py_BuildValue("b",state.Upgrade()));   
}

static PyObject *PkgDepCacheMarkedDelete(PyObject *Self,PyObject *Args)
{   
   PkgDepCacheStruct &Struct = GetCpp<PkgDepCacheStruct>(Self);

   PyObject *PackageObj;
   if (PyArg_ParseTuple(Args,"O!",&PackageType,&PackageObj) == 0)
      return 0;

   pkgCache::PkgIterator &Pkg = GetCpp<pkgCache::PkgIterator>(PackageObj);
   pkgDepCache::StateCache &state = (*Struct.depcache)[Pkg];

   return HandleErrors(Py_BuildValue("b",state.Delete()));   
}

static PyObject *PkgDepCacheMarkedKeep(PyObject *Self,PyObject *Args)
{   
   PkgDepCacheStruct &Struct = GetCpp<PkgDepCacheStruct>(Self);

   PyObject *PackageObj;
   if (PyArg_ParseTuple(Args,"O!",&PackageType,&PackageObj) == 0)
      return 0;

   pkgCache::PkgIterator &Pkg = GetCpp<pkgCache::PkgIterator>(PackageObj);
   pkgDepCache::StateCache &state = (*Struct.depcache)[Pkg];

   return HandleErrors(Py_BuildValue("b",state.Keep()));   
}

static PyMethodDef PkgDepCacheMethods[] = 
{
   {"Init",PkgDepCacheInit,METH_VARARGS,"Init the depcache (done on construct automatically)"},
   {"GetCandidateVer",PkgDepCacheGetCandidateVer,METH_VARARGS,"Get candidate version"},
   // global cache operations
   {"Upgrade",PkgDepCacheUpgrade,METH_VARARGS,"Perform Upgrade (optional boolean argument if dist-upgrade should be performed)"},
   {"FixBroken",PkgDepCacheFixBroken,METH_VARARGS,"Fix broken packages"},
   // Manipulators
   {"MarkKeep",PkgDepCacheMarkKeep,METH_VARARGS,"Mark package for keep"},
   {"MarkDelete",PkgDepCacheMarkDelete,METH_VARARGS,"Mark package for delete (optional boolean argument if it should be purged)"},
   {"MarkInstall",PkgDepCacheMarkInstall,METH_VARARGS,"Mark package for Install"},
   // state information
   {"IsUpgradable",PkgDepCacheIsUpgradable,METH_VARARGS,"Is pkg upgradable"},
   {"IsNowBroken",PkgDepCacheIsNowBroken,METH_VARARGS,"Is pkg is now broken"},
   {"IsInstBroken",PkgDepCacheIsInstBroken,METH_VARARGS,"Is pkg broken on the current install"},
   {"MarkedInstall",PkgDepCacheMarkedInstall,METH_VARARGS,"Is pkg marked for install"},
   {"MarkedUpgrade",PkgDepCacheMarkedUpgrade,METH_VARARGS,"Is pkg marked for upgrade"},
   {"MarkedDelete",PkgDepCacheMarkedDelete,METH_VARARGS,"Is pkg marked for delete"},
   {"MarkedKeep",PkgDepCacheMarkedDelete,METH_VARARGS,"Is pkg marked for keep"},
   {}
};


static PyObject *DepCacheAttr(PyObject *Self,char *Name)
{
   PkgDepCacheStruct &Struct = GetCpp<PkgDepCacheStruct>(Self);

   // size querries
   if(strcmp("KeepCount",Name) == 0) 
      return Py_BuildValue("l", Struct.depcache->KeepCount());
   else if(strcmp("InstCount",Name) == 0) 
      return Py_BuildValue("l", Struct.depcache->InstCount());
   else if(strcmp("DelCount",Name) == 0) 
      return Py_BuildValue("l", Struct.depcache->DelCount());
   else if(strcmp("BrokenCount",Name) == 0) 
      return Py_BuildValue("l", Struct.depcache->BrokenCount());
   else if(strcmp("UsrSize",Name) == 0) 
      return Py_BuildValue("d", Struct.depcache->UsrSize());
   else if(strcmp("DebSize",Name) == 0) 
      return Py_BuildValue("d", Struct.depcache->DebSize());
   
   
   return Py_FindMethod(PkgDepCacheMethods,Self,Name);
}




PyTypeObject PkgDepCacheType =
{
   PyObject_HEAD_INIT(&PyType_Type)
   0,			                // ob_size
   "pkgDepCache",                          // tp_name
   sizeof(CppOwnedPyObject<PkgDepCacheStruct>),   // tp_basicsize
   0,                                   // tp_itemsize
   // Methods
   CppOwnedDealloc<PkgDepCacheStruct>,        // tp_dealloc
   0,                                   // tp_print
   DepCacheAttr,                           // tp_getattr
   0,                                   // tp_setattr
   0,                                   // tp_compare
   0,                                   // tp_repr
   0,                                   // tp_as_number
   0,                                   // tp_as_sequence
   0,	                                // tp_as_mapping
   0,                                   // tp_hash
};


PyObject *GetDepCache(PyObject *Self,PyObject *Args)
{
   PyObject *Owner;
   if (PyArg_ParseTuple(Args,"O!",&PkgCacheType,&Owner) == 0)
      return 0;

   PyObject *DepCachePyObj;
   DepCachePyObj = CppOwnedPyObject_NEW<PkgDepCacheStruct>(Owner,
							   &PkgDepCacheType,
							   GetCpp<pkgCache *>(Owner));
   HandleErrors(DepCachePyObj);
   PkgDepCacheStruct &Struct = GetCpp<PkgDepCacheStruct>(DepCachePyObj);   

   // init without progress obj
   Struct.depcache->Init(0);

   return DepCachePyObj;
}




									/*}}}*/
