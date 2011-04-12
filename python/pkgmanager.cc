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
   if (PyArg_ParseTupleAndKeywords(Args,kwds,"O!",kwlist,&PyDepCache_Type,
                                   &Owner) == 0)
      return 0;

   pkgPackageManager *pm = _system->CreatePM(GetCpp<pkgDepCache*>(Owner));

   CppPyObject<pkgPackageManager*> *PkgManagerObj =
	   CppPyObject_NEW<pkgPackageManager*>(NULL, type,pm);

   return PkgManagerObj;
}

#ifdef COMPAT_0_7
PyObject *GetPkgManager(PyObject *Self,PyObject *Args)
{
    PyErr_WarnEx(PyExc_DeprecationWarning, "apt_pkg.GetPackageManager() is "
                 "deprecated. Please see apt_pkg.PackageManager() for the "
                 "replacement.", 1);
    return PkgManagerNew(&PyPackageManager_Type,Args,0);
}
#endif


static PyObject *PkgManagerGetArchives(PyObject *Self,PyObject *Args)
{
   pkgPackageManager *pm = GetCpp<pkgPackageManager*>(Self);
   PyObject *fetcher, *list, *recs;

   if (PyArg_ParseTuple(Args, "O!O!O!",
			&PyAcquire_Type,&fetcher,
			&PySourceList_Type, &list,
			&PyPackageRecords_Type, &recs) == 0)
      return 0;

   pkgAcquire *s_fetcher = GetCpp<pkgAcquire*>(fetcher);
   pkgSourceList *s_list = GetCpp<pkgSourceList*>(list);
   PkgRecordsStruct &s_records = GetCpp<PkgRecordsStruct>(recs);

   bool res = pm->GetArchives(s_fetcher, s_list,
			      &s_records.Records);

   return HandleErrors(PyBool_FromLong(res));
}

static PyObject *PkgManagerDoInstall(PyObject *Self,PyObject *Args)
{
   //PkgManagerStruct &Struct = GetCpp<PkgManagerStruct>(Self);
   pkgPackageManager *pm = GetCpp<pkgPackageManager*>(Self);
   int status_fd = -1;

   if (PyArg_ParseTuple(Args, "|i", &status_fd) == 0)
      return 0;

   pkgPackageManager::OrderResult res = pm->DoInstall(status_fd);

   return HandleErrors(MkPyNumber(res));
}

static PyObject *PkgManagerFixMissing(PyObject *Self,PyObject *Args)
{
   //PkgManagerStruct &Struct = GetCpp<PkgManagerStruct>(Self);
   pkgPackageManager *pm = GetCpp<pkgPackageManager*>(Self);

   if (PyArg_ParseTuple(Args, "") == 0)
      return 0;

   bool res = pm->FixMissing();

   return HandleErrors(PyBool_FromLong(res));
}

static PyMethodDef PkgManagerMethods[] =
{
   {"get_archives",PkgManagerGetArchives,METH_VARARGS,
    "get_archives(fetcher: Acquire, list: SourceList, recs: PackageRecords) -> bool\n\n"
    "Download the packages marked for installation via the Acquire object\n"
    "'fetcher', using the information found in 'list' and 'recs'."},
   {"do_install",PkgManagerDoInstall,METH_VARARGS,
    "do_install(status_fd: int) -> int\n\n"
    "Install the packages and return one of the class constants\n"
    "RESULT_COMPLETED, RESULT_FAILED, RESULT_INCOMPLETE. The argument\n"
    "status_fd can be used to specify a file descriptor that APT will\n"
    "write status information on (see README.progress-reporting in the\n"
    "apt source code for information on what will be written there)."},
   {"fix_missing",PkgManagerFixMissing,METH_VARARGS,
    "fix_missing() -> bool\n\n"
    "Fix the installation if a package could not be downloaded."},
   {}
};


static const char *packagemanager_doc =
    "PackageManager(depcache: apt_pkg.DepCache)\n\n"
    "PackageManager objects allow the fetching of packages marked for\n"
    "installation and the installation of those packages. The parameter\n"
    "'depcache' specifies an apt_pkg.DepCache object where information\n"
    "about the package selections is retrieved from.";
PyTypeObject PyPackageManager_Type =
{
   PyVarObject_HEAD_INIT(&PyType_Type, 0)
   "apt_pkg.PackageManager",           // tp_name
   sizeof(CppPyObject<pkgPackageManager*>),   // tp_basicsize
   0,                                   // tp_itemsize
   // Methods
   CppDeallocPtr<pkgPackageManager*>,   // tp_dealloc
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
   _PyAptObject_getattro,               // tp_getattro
   0,                                   // tp_setattro
   0,                                   // tp_as_buffer
   (Py_TPFLAGS_DEFAULT |                // tp_flags
    Py_TPFLAGS_BASETYPE),
   packagemanager_doc,                  // tp_doc
   0,                                   // tp_traverse
   0,                                   // tp_clear
   0,                                   // tp_richcompare
   0,                                   // tp_weaklistoffset
   0,                                   // tp_iter
   0,                                   // tp_iternext
   PkgManagerMethods,                   // tp_methods
   0,                                   // tp_members
   0,                                   // tp_getset
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
