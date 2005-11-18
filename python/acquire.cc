// Description								/*{{{*/
// $Id: acquire.cc,v 1.1 2003/06/03 03:03:23 mvo Exp $
/* ######################################################################

   Acquire - Wrapper for the acquire code

   ##################################################################### */

#include "generic.h"
#include "apt_pkgmodule.h"
#include "acquire.h"
#include "progress.h"

#include <apt-pkg/acquire-item.h>


static PyObject *PkgAcquireRun(PyObject *Self,PyObject *Args)
{   
   PkgAcquireStruct &Struct = GetCpp<PkgAcquireStruct>(Self);

   if (PyArg_ParseTuple(Args, "") == 0) 
      return 0;

   //FIXME: add pulse interval here
   pkgAcquire::RunResult run = Struct.fetcher.Run();

   return HandleErrors(Py_BuildValue("i",run));
}

static PyObject *PkgAcquireShutdown(PyObject *Self,PyObject *Args)
{   
   PkgAcquireStruct &Struct = GetCpp<PkgAcquireStruct>(Self);

   if (PyArg_ParseTuple(Args, "") == 0) 
      return 0;

   Struct.fetcher.Shutdown();

   Py_INCREF(Py_None);
   return HandleErrors(Py_None);   
}

static PyMethodDef PkgAcquireMethods[] = 
{
   {"Run",PkgAcquireRun,METH_VARARGS,"Run the fetcher"},
   {}
};


static PyObject *AcquireAttr(PyObject *Self,char *Name)
{
   PkgAcquireStruct &Struct = GetCpp<PkgAcquireStruct>(Self);

   if(strcmp("TotalNeeded",Name) == 0) 
      return Py_BuildValue("l", Struct.fetcher.TotalNeeded());
   if(strcmp("FetchNeeded",Name) == 0) 
      return Py_BuildValue("l", Struct.fetcher.FetchNeeded());
   if(strcmp("PartialPresent",Name) == 0) 
      return Py_BuildValue("l", Struct.fetcher.PartialPresent());
   // some constants
   if(strcmp("ResultContinue",Name) == 0) 
      return Py_BuildValue("i", pkgAcquire::Continue);
   if(strcmp("ResultFailed",Name) == 0) 
      return Py_BuildValue("i", pkgAcquire::Failed);
   if(strcmp("ResultCancelled",Name) == 0) 
      return Py_BuildValue("i", pkgAcquire::Cancelled);

   return Py_FindMethod(PkgAcquireMethods,Self,Name);
}




PyTypeObject PkgAcquireType =
{
   PyObject_HEAD_INIT(&PyType_Type)
   0,			                // ob_size
   "Acquire",                          // tp_name
   sizeof(CppOwnedPyObject<PkgAcquireStruct>),   // tp_basicsize
   0,                                   // tp_itemsize
   // Methods
   CppOwnedDealloc<PkgAcquireStruct>,        // tp_dealloc
   0,                                   // tp_print
   AcquireAttr,                           // tp_getattr
   0,                                   // tp_setattr
   0,                                   // tp_compare
   0,                                   // tp_repr
   0,                                   // tp_as_number
   0,                                   // tp_as_sequence
   0,	                                // tp_as_mapping
   0,                                   // tp_hash
};

PyObject *GetAcquire(PyObject *Self,PyObject *Args)
{
   pkgAcquire *fetcher;

   PyObject *pyFetchProgressInst = NULL;
   if (PyArg_ParseTuple(Args,"|O",&pyFetchProgressInst) == 0)
      return 0;

   if (pyFetchProgressInst != NULL) {
      // FIXME: memleak?
      PyFetchProgress *progress = new PyFetchProgress();
      progress->setCallbackInst(pyFetchProgressInst);
      fetcher = new pkgAcquire(progress);
   } else {
      fetcher = new pkgAcquire();
   }

   CppOwnedPyObject<pkgAcquire> *FetcherObj =
	   CppOwnedPyObject_NEW<pkgAcquire>(0,&PkgAcquireType, *fetcher);
   
   return FetcherObj;
}




									/*}}}*/
