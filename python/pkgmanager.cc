// Description								/*{{{*/
// $Id: acquire.cc,v 1.1 2003/06/03 03:03:23 mvo Exp $
/* ######################################################################

   PkgManager - Wrapper for the pkgPackageManager code

   ##################################################################### */

#include "generic.h"
#include "apt_pkgmodule.h"
#include "acquire.h"
#include "sourcelist.h"
#include "pkgrecords.h"

#include <apt-pkg/packagemanager.h>
#include <apt-pkg/pkgsystem.h>

#include <iostream>


struct PkgManagerStruct
{
   pkgPackageManager pm;
};

static PyObject *PkgManagerGetArchives(PyObject *Self,PyObject *Args)
{   
   PkgManagerStruct &Struct = GetCpp<PkgManagerStruct>(Self);
   PyObject *fetcher, *list, *recs;
   
   if (PyArg_ParseTuple(Args, "O!O!O!",
			&PkgAcquireType,&fetcher,
			&PkgSourceListType, &list,
			&PkgRecordsType, &recs) == 0) 
      return 0;

   PkgAcquireStruct &s_fetcher = GetCpp<PkgAcquireStruct>(fetcher);
   PkgSourceListStruct &s_list = GetCpp<PkgSourceListStruct>(list);
   PkgRecordsStruct &s_records = GetCpp<PkgRecordsStruct>(recs);

   bool res = Struct.pm.GetArchives(&s_fetcher.fetcher,
				    &s_list.List,
				    &s_records.Records);

   return HandleErrors(Py_None);
}


static PyMethodDef PkgManagerMethods[] = 
{
   {"GetArchives",PkgManagerGetArchives,METH_VARARGS,"Load the selected archvies into the fetcher"},
   {}
};


static PyObject *PkgManagerAttr(PyObject *Self,char *Name)
{
   PkgManagerStruct &Struct = GetCpp<PkgManagerStruct>(Self);

   // some constants
   if(strcmp("ResultCompleted",Name) == 0) 
      return Py_BuildValue("i", pkgPackageManager::Completed);
   if(strcmp("ResultFailed",Name) == 0) 
      return Py_BuildValue("i", pkgPackageManager::Failed);
   if(strcmp("ResultIncomplete",Name) == 0) 
      return Py_BuildValue("i", pkgPackageManager::Incomplete);

   return Py_FindMethod(PkgManagerMethods,Self,Name);
}


PyTypeObject PkgManagerType =
{
   PyObject_HEAD_INIT(&PyType_Type)
   0,			                // ob_size
   "PackageManager",                          // tp_name
   sizeof(CppOwnedPyObject<PkgManagerStruct>),   // tp_basicsize
   0,                                   // tp_itemsize
   // Methods
   CppOwnedDealloc<PkgManagerStruct>,        // tp_dealloc
   0,                                   // tp_print
   PkgManagerAttr,                           // tp_getattr
   0,                                   // tp_setattr
   0,                                   // tp_compare
   0,                                   // tp_repr
   0,                                   // tp_as_number
   0,                                   // tp_as_sequence
   0,	                                // tp_as_mapping
   0,                                   // tp_hash
};

PyObject *GetPkgManager(PyObject *Self,PyObject *Args)
{
   PyObject *Owner;
   if (PyArg_ParseTuple(Args,"O!",&PkgDepCacheType,&Owner) == 0)
      return 0;

   pkgPackageManager *pm = _system->CreatePM(GetCpp<pkgDepCache*>(Owner));

   CppOwnedPyObject<pkgPackageManager> *PkgManagerObj =
	   CppOwnedPyObject_NEW<pkgPackageManager>(0,&PkgManagerType, *pm);
   
   return PkgManagerObj;
}




									/*}}}*/
