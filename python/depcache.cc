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
#include <apt-pkg/policy.h>
#include <apt-pkg/sptr.h>

#include <Python.h>
			

// DepCache Class								/*{{{*/
// ---------------------------------------------------------------------

struct PkgDepCacheStruct
{
   pkgDepCache depcache;

   PkgDepCacheStruct(pkgCache *Cache, pkgPolicy *Policy) 
      : depcache(Cache,Policy) {};
   // FIXME: wrap pkgPolicy as well and remove this "new() memory leak"
   PkgDepCacheStruct(pkgCache *Cache) 
      : depcache(Cache,new pkgPolicy(Cache) ) {};
   PkgDepCacheStruct() : depcache(NULL, NULL) {abort();};
};

static PyObject *PkgDepCacheInit(PyObject *Self,PyObject *Args)
{   
   PkgDepCacheStruct &Struct = GetCpp<PkgDepCacheStruct>(Self);

   // FIXME: argument should be OpProgress
#if 0
   PyObject *PkgFObj;
   long int Index;
   if (PyArg_ParseTuple(Args,"(O!l)",&PackageFileType,&PkgFObj,&Index) == 0)
      return 0;
#endif   

   Struct.depcache.Init(0);

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
   pkgCache::VerIterator I = Struct.depcache.GetCandidateVer(Pkg);
   CandidateObj = CppOwnedPyObject_NEW<pkgCache::VerIterator>(PackageObj,&VersionType,I);

   return CandidateObj;
}

static PyMethodDef PkgDepCacheMethods[] = 
{
   {"Init",PkgDepCacheInit,METH_VARARGS,"Init the depcache"},
   {"GetCandidateVer",PkgDepCacheGetCandidateVer,METH_VARARGS,"Get candidate version"},
   {}
};


static PyObject *DepCacheAttr(PyObject *Self,char *Name)
{
   PkgDepCacheStruct &Struct = GetCpp<PkgDepCacheStruct>(Self);

   // size querries
   if(strcmp("KeepCount",Name) == 0) 
      return Py_BuildValue("i", Struct.depcache.KeepCount());
   else if(strcmp("InstCount",Name) == 0) 
      return Py_BuildValue("i", Struct.depcache.InstCount());
   else if(strcmp("DelCount",Name) == 0) 
      return Py_BuildValue("i", Struct.depcache.DelCount());
   else if(strcmp("BrokenCount",Name) == 0) 
      return Py_BuildValue("i", Struct.depcache.BrokenCount());
   else if(strcmp("UsrSize",Name) == 0) 
      return Py_BuildValue("i", Struct.depcache.UsrSize());
   else if(strcmp("DebSize",Name) == 0) 
      return Py_BuildValue("i", Struct.depcache.DebSize());
   
   
#if 0
   if (strcmp("FileList",Name) == 0)
   {
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
#endif
   return Py_FindMethod(PkgDepCacheMethods,Self,Name);
}




PyTypeObject PkgDepCacheType =
{
   PyObject_HEAD_INIT(&PyType_Type)
   0,			                // ob_size
   "pkgDepCache",                          // tp_name
   sizeof(CppOwnedPyObject<pkgDepCache *>),   // tp_basicsize
   0,                                   // tp_itemsize
   // Methods
   CppOwnedDealloc<pkgDepCache *>,        // tp_dealloc
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

   return HandleErrors(CppOwnedPyObject_NEW<PkgDepCacheStruct>(Owner,
							 &PkgDepCacheType,
							 GetCpp<pkgCache *>(Owner)));
}


									/*}}}*/
