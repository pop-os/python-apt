// -*- mode: cpp; mode: fold -*-
// Description								/*{{{*/
// $Id: indexfile.cc,v 1.2 2003/12/26 17:04:22 mdz Exp $
/* ######################################################################

   pkgIndexFile - Wrapper for the pkgIndexFilefunctions

   ##################################################################### */
									/*}}}*/
// Include Files							/*{{{*/
#include "generic.h"
#include "apt_pkgmodule.h"

#include <apt-pkg/indexfile.h>

#include <Python.h>

static PyObject *PackageIndexFileArchiveURI(PyObject *Self,PyObject *Args)
{
   pkgIndexFile *File = GetCpp<pkgIndexFile*>(Self);
   char *path;

   if (PyArg_ParseTuple(Args, "s",&path) == 0)
      return 0;

   return HandleErrors(Safe_FromString(File->ArchiveURI(path).c_str()));
}

static PyMethodDef PackageIndexFileMethods[] =
{
   {"ArchiveURI",PackageIndexFileArchiveURI,METH_VARARGS,"Returns the ArchiveURI"},
   {}
};

#define File (GetCpp<pkgIndexFile*>(Self))
static PyObject *PackageIndexFileGetLabel(PyObject *Self,void*) {
   return Safe_FromString(File->GetType()->Label);
}
static PyObject *PackageIndexFileGetDescribe(PyObject *Self,void*) {
   return Safe_FromString(File->Describe().c_str());
}
static PyObject *PackageIndexFileGetExists(PyObject *Self,void*) {
   return Py_BuildValue("i",(File->Exists()));
}
static PyObject *PackageIndexFileGetHasPackages(PyObject *Self,void*) {
   return Py_BuildValue("i",(File->HasPackages()));
}
static PyObject *PackageIndexFileGetSize(PyObject *Self,void*) {
   return Py_BuildValue("i",(File->Size()));
}
static PyObject *PackageIndexFileGetIsTrusted(PyObject *Self,void*) {
   return Py_BuildValue("i",(File->IsTrusted()));
}
#undef File

static PyObject *PackageIndexFileRepr(PyObject *Self)
{
   pkgIndexFile *File = GetCpp<pkgIndexFile*>(Self);

   char S[1024];
   snprintf(S,sizeof(S),"<pkIndexFile object: "
			"Label:'%s' Describe='%s' Exists='%i' "
	                "HasPackages='%i' Size='%i'  "
 	                "IsTrusted='%i' ArchiveURI='%s'>",
	    File->GetType()->Label,  File->Describe().c_str(), File->Exists(),
	    File->HasPackages(), File->Size(),
            File->IsTrusted(), File->ArchiveURI("").c_str());
   return PyString_FromString(S);
}

static PyGetSetDef PackageIndexFileGetSet[] = {
    {"Describe",PackageIndexFileGetDescribe},
    {"Exists",PackageIndexFileGetExists},
    {"HasPackages",PackageIndexFileGetHasPackages},
    {"IsTrusted",PackageIndexFileGetIsTrusted},
    {"Label",PackageIndexFileGetLabel},
    {"Size",PackageIndexFileGetSize},
    {}
};

PyTypeObject PackageIndexFileType =
{
   PyObject_HEAD_INIT(&PyType_Type)
   #if PY_MAJOR_VERSION < 3
   0,                                   // ob_size
   #endif
   "pkgIndexFile",                      // tp_name
   sizeof(CppOwnedPyObject<pkgIndexFile*>),   // tp_basicsize
   0,                                   // tp_itemsize
   // Methods
   CppOwnedDealloc<pkgIndexFile*>,      // tp_dealloc
   0,                                   // tp_print
   0,                                   // tp_getattr
   0,                                   // tp_setattr
   0,                                   // tp_compare
   PackageIndexFileRepr,                // tp_repr
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
   "pkgIndexFile Object",               // tp_doc
   0,                                   // tp_traverse
   0,                                   // tp_clear
   0,                                   // tp_richcompare
   0,                                   // tp_weaklistoffset
   0,                                   // tp_iter
   0,                                   // tp_iternext
   PackageIndexFileMethods,             // tp_methods
   0,                                   // tp_members
   PackageIndexFileGetSet,              // tp_getset
};




