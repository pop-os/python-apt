// Description								/*{{{*/
// $Id: acquire.cc,v 1.1 2003/06/03 03:03:23 mvo Exp $
/* ######################################################################

   PkgManager - Wrapper for the pkgPackageManager code

   ##################################################################### */

#include "generic.h"
#include "apt_pkgmodule.h"
#include "pkgrecords.h"

#include <apt-pkg/packagemanager.h>
#include <apt-pkg/pkgsystem.h>
#include <apt-pkg/sourcelist.h>
#include <apt-pkg/error.h>
#include <apt-pkg/acquire.h>
#include <apt-pkg/init.h>
#include <apt-pkg/configuration.h>

#include <iostream>

static PyObject *PkgManagerNew(PyTypeObject *type,PyObject *Args,PyObject *kwds)
{
   PyObject *Owner;
   char *kwlist[] = {"depcache",0};
   if (PyArg_ParseTupleAndKeywords(Args,kwds,"O!",kwlist,&PkgDepCacheType,
                                   &Owner) == 0)
      return 0;

   pkgPackageManager *pm = _system->CreatePM(GetCpp<pkgDepCache*>(Owner));

   CppPyObject<pkgPackageManager*> *PkgManagerObj =
	   CppPyObject_NEW<pkgPackageManager*>(type,pm);

   return PkgManagerObj;
}

#ifdef COMPAT_0_7
PyObject *GetPkgManager(PyObject *Self,PyObject *Args)
{
    return PkgManagerNew(&PkgManagerType,Args,0);
}
#endif


static PyObject *PkgManagerGetArchives(PyObject *Self,PyObject *Args)
{
   pkgPackageManager *pm = GetCpp<pkgPackageManager*>(Self);
   PyObject *fetcher, *list, *recs;

   if (PyArg_ParseTuple(Args, "O!O!O!",
			&PkgAcquireType,&fetcher,
			&PkgSourceListType, &list,
			&PkgRecordsType, &recs) == 0)
      return 0;

   pkgAcquire *s_fetcher = GetCpp<pkgAcquire*>(fetcher);
   pkgSourceList *s_list = GetCpp<pkgSourceList*>(list);
   PkgRecordsStruct &s_records = GetCpp<PkgRecordsStruct>(recs);

   bool res = pm->GetArchives(s_fetcher, s_list,
			      &s_records.Records);

   return HandleErrors(Py_BuildValue("b",res));
}

static PyObject *PkgManagerDoInstall(PyObject *Self,PyObject *Args)
{
   //PkgManagerStruct &Struct = GetCpp<PkgManagerStruct>(Self);
   pkgPackageManager *pm = GetCpp<pkgPackageManager*>(Self);
   int status_fd = -1;

   if (PyArg_ParseTuple(Args, "|i", &status_fd) == 0)
      return 0;

   pkgPackageManager::OrderResult res = pm->DoInstall(status_fd);

   return HandleErrors(Py_BuildValue("i",res));
}

static PyObject *PkgManagerFixMissing(PyObject *Self,PyObject *Args)
{
   //PkgManagerStruct &Struct = GetCpp<PkgManagerStruct>(Self);
   pkgPackageManager *pm = GetCpp<pkgPackageManager*>(Self);

   if (PyArg_ParseTuple(Args, "") == 0)
      return 0;

   bool res = pm->FixMissing();

   return HandleErrors(Py_BuildValue("b",res));
}

static PyMethodDef PkgManagerMethods[] =
{
   {"get_archives",PkgManagerGetArchives,METH_VARARGS,"Load the selected archives into the fetcher"},
   {"do_install",PkgManagerDoInstall,METH_VARARGS,"Do the actual install"},
   {"fix_missing",PkgManagerFixMissing,METH_VARARGS,"Fix the install if a pkg couldn't be downloaded"},
#ifdef COMPAT_0_7
   {"GetArchives",PkgManagerGetArchives,METH_VARARGS,"Load the selected archives into the fetcher"},
   {"DoInstall",PkgManagerDoInstall,METH_VARARGS,"Do the actual install"},
   {"FixMissing",PkgManagerFixMissing,METH_VARARGS,"Fix the install if a pkg couldn't be downloaded"},
#endif
   {}
};


static PyObject *PkgManagerGetResultCompleted(PyObject *Self,void*) {
   return Py_BuildValue("i", pkgPackageManager::Completed);
}
static PyObject *PkgManagerGetResultFailed(PyObject *Self,void*) {
   return Py_BuildValue("i", pkgPackageManager::Failed);
}
static PyObject *PkgManagerGetResultIncomplete(PyObject *Self,void*) {
   return Py_BuildValue("i", pkgPackageManager::Incomplete);
}

static PyGetSetDef PkgManagerGetSet[] = {
    {"result_completed",PkgManagerGetResultCompleted},
    {"result_failed",PkgManagerGetResultFailed},
    {"result_incomplete",PkgManagerGetResultIncomplete},
#ifdef COMPAT_0_7
    {"ResultCompleted",PkgManagerGetResultCompleted},
    {"ResultFailed",PkgManagerGetResultFailed},
    {"ResultIncomplete",PkgManagerGetResultIncomplete},
#endif
    {}
};

PyTypeObject PkgManagerType =
{
   PyObject_HEAD_INIT(&PyType_Type)
   #if PY_MAJOR_VERSION < 3
   0,                                   // ob_size
   #endif
   "apt_pkg.PackageManager",           // tp_name
   sizeof(CppPyObject<pkgPackageManager*>),   // tp_basicsize
   0,                                   // tp_itemsize
   // Methods
   CppDealloc<pkgPackageManager*>,      // tp_dealloc
   0,                                   // tp_print
   0,                                   // tp_getattr
   0,                                   // tp_setattr
   0,                                   // tp_compare
   0,                                   // tp_repr
   0,                                   // tp_as_number
   0,                                   // tp_as_sequence
   0,                                   // tp_as_mapping
   0,                                   // tp_hash
   0,                                   // tp_call
   0,                                   // tp_str
   0,                                   // tp_getattro
   0,                                   // tp_setattro
   0,                                   // tp_as_buffer
   Py_TPFLAGS_DEFAULT,                  // tp_flags
   "PackageManager Object",             // tp_doc
   0,                                   // tp_traverse
   0,                                   // tp_clear
   0,                                   // tp_richcompare
   0,                                   // tp_weaklistoffset
   0,                                   // tp_iter
   0,                                   // tp_iternext
   PkgManagerMethods,                   // tp_methods
   0,                                   // tp_members
   PkgManagerGetSet,                    // tp_getset
   0,                                   // tp_base
   0,                                   // tp_dict
   0,                                   // tp_descr_get
   0,                                   // tp_descr_set
   0,                                   // tp_dictoffset
   0,                                   // tp_init
   0,                                   // tp_alloc
   PkgManagerNew,                         // tp_new
};



									/*}}}*/
