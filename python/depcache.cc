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
			

#include <iostream>



struct PyOpProgressStruct : public OpProgress
{

   PyObject *py_update_callback_func;
   PyObject *py_update_callback_args;

   virtual void Update() {
      if(py_update_callback_func == NULL)
	 return;

      // Build up the argument list... 
      PyObject *arglist = Py_BuildValue("(fO)", Percent, py_update_callback_args);

      // ...for calling the Python compare function.
      PyObject *result = PyEval_CallObject(py_update_callback_func,arglist);

      Py_XDECREF(result);
      Py_DECREF(arglist);

      return;
   };

   PyOpProgressStruct() : OpProgress(), py_update_callback_func(0) {};
};




// DepCache Class								/*{{{*/
// ---------------------------------------------------------------------

struct PkgDepCacheStruct
{
   pkgDepCache depcache;
   PyOpProgressStruct progress;

   PkgDepCacheStruct(pkgCache *Cache, pkgPolicy *Policy) 
      : depcache(Cache,Policy) {};
   // FIXME: wrap pkgPolicy as well and remove this "new() memory leak"
   PkgDepCacheStruct(pkgCache *Cache) 
      : depcache(Cache,new pkgPolicy(Cache) ) {};

   PkgDepCacheStruct() : depcache(NULL, NULL) {abort();};
};

static PyObject *PkgDepCacheProgressCallback(PyObject *Self, PyObject *Args)
{
   PyObject *pyCallbackObj;
   PyObject *pyCallbackArgs;

   PkgDepCacheStruct &Struct = GetCpp<PkgDepCacheStruct>(Self);
   if (!PyArg_ParseTuple(Args, "OO", &pyCallbackObj, &pyCallbackArgs)) 
        return NULL;
   // make sure second argument is a function
   if (!PyCallable_Check(pyCallbackObj)) {
      PyErr_SetString(PyExc_TypeError, "Need a callable object!");
      return 0;
   }
    
   // save the compare func. 
   Struct.progress.py_update_callback_func = pyCallbackObj;
   Struct.progress.py_update_callback_args = pyCallbackArgs;

   Py_INCREF(Py_None);
   return Py_None;
}

static PyObject *PkgDepCacheInit(PyObject *Self,PyObject *Args)
{   
   PkgDepCacheStruct &Struct = GetCpp<PkgDepCacheStruct>(Self);

   OpProgress *progress = &Struct.progress;
   Struct.depcache.Init(progress);

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
   {"SetProgressCallback",PkgDepCacheProgressCallback,METH_VARARGS,"Set a progress callback, first argument is the function, second a optional data argument that will be passed to the function"},
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

   return HandleErrors(CppOwnedPyObject_NEW<PkgDepCacheStruct>(Owner,
							 &PkgDepCacheType,
							 GetCpp<pkgCache *>(Owner)));
}




									/*}}}*/
