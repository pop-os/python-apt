// Description								/*{{{*/
// $Id: cdrom.cc,v 1.1 2003/06/03 03:03:23 mvo Exp $
/* ######################################################################

   Cdrom - Wrapper for the apt-cdrom support

   ##################################################################### */

#include "generic.h"
#include "apt_pkgmodule.h"
#include "progress.h"

#include <apt-pkg/cdrom.h>


struct PkgCdromStruct
{
   pkgCdrom cdrom;
};

static PyObject *PkgCdromAdd(PyObject *Self,PyObject *Args)
{
   PkgCdromStruct &Struct = GetCpp<PkgCdromStruct>(Self);

   PyObject *pyCdromProgressInst = 0;
   if (PyArg_ParseTuple(Args, "O", &pyCdromProgressInst) == 0) {
      return 0;
   }

   PyCdromProgress progress;
   progress.setCallbackInst(pyCdromProgressInst);

   bool res = Struct.cdrom.Add(&progress);

   return HandleErrors(Py_BuildValue("b", res));
}

static PyObject *PkgCdromIdent(PyObject *Self,PyObject *Args)
{
   PkgCdromStruct &Struct = GetCpp<PkgCdromStruct>(Self);

   PyObject *pyCdromProgressInst = 0;
   if (PyArg_ParseTuple(Args, "O", &pyCdromProgressInst) == 0) {
      return 0;
   }

   PyCdromProgress progress;
   progress.setCallbackInst(pyCdromProgressInst);

   string ident;
   bool res = Struct.cdrom.Ident(ident, &progress);

   PyObject *result = Py_BuildValue("(bs)", res, ident.c_str());

   return HandleErrors(result);
}


static PyMethodDef PkgCdromMethods[] =
{
   {"Add",PkgCdromAdd,METH_VARARGS,"Add a cdrom"},
   {"Ident",PkgCdromIdent,METH_VARARGS,"Ident a cdrom"},
   {}
};


PyTypeObject PkgCdromType =
{
   PyObject_HEAD_INIT(&PyType_Type)
   #if PY_MAJOR_VERSION < 3
   0,                                   // ob_size
   #endif
   "Cdrom",                             // tp_name
   sizeof(CppOwnedPyObject<PkgCdromStruct>),   // tp_basicsize
   0,                                   // tp_itemsize
   // Methods
   CppOwnedDealloc<PkgCdromStruct>,     // tp_dealloc
   0,                                   // tp_print
   0,                                   // tp_getattr
   0,                                   // tp_setattr
   0,                                   // tp_compare
   0,                                   // tp_repr
   0,                                   // tp_as_number
   0,                                   // tp_as_sequence
   0,	                                // tp_as_mapping
   0,                                   // tp_hash
   0,                                   // tp_call
   0,                                   // tp_str
   0,                                   // tp_getattro
   0,                                   // tp_setattro
   0,                                   // tp_as_buffer
   Py_TPFLAGS_DEFAULT,                  // tp_flags
   "Cdrom Object",                      // tp_doc
   0,                                   // tp_traverse
   0,                                   // tp_clear
   0,                                   // tp_richcompare
   0,                                   // tp_weaklistoffset
   0,                                   // tp_iter
   0,                                   // tp_iternext
   PkgCdromMethods,                     // tp_methods
};

PyObject *GetCdrom(PyObject *Self,PyObject *Args)
{
   pkgCdrom *cdrom = new pkgCdrom();

   CppOwnedPyObject<pkgCdrom> *CdromObj =
	   CppOwnedPyObject_NEW<pkgCdrom>(0,&PkgCdromType, *cdrom);

   return CdromObj;
}




									/*}}}*/
