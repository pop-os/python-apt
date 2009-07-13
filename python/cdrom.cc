// Description								/*{{{*/
// $Id: cdrom.cc,v 1.1 2003/06/03 03:03:23 mvo Exp $
/* ######################################################################

   Cdrom - Wrapper for the apt-cdrom support

   ##################################################################### */

#include "generic.h"
#include "apt_pkgmodule.h"
#include "progress.h"

#include <apt-pkg/cdrom.h>

static PyObject *PkgCdromAdd(PyObject *Self,PyObject *Args)
{
   pkgCdrom &Cdrom = GetCpp<pkgCdrom>(Self);

   PyObject *pyCdromProgressInst = 0;
   if (PyArg_ParseTuple(Args, "O", &pyCdromProgressInst) == 0) {
      return 0;
   }

   PyCdromProgress progress;
   progress.setCallbackInst(pyCdromProgressInst);

   bool res = Cdrom.Add(&progress);

   return HandleErrors(Py_BuildValue("b", res));
}

static PyObject *PkgCdromIdent(PyObject *Self,PyObject *Args)
{
   pkgCdrom &Cdrom = GetCpp<pkgCdrom>(Self);

   PyObject *pyCdromProgressInst = 0;
   if (PyArg_ParseTuple(Args, "O", &pyCdromProgressInst) == 0) {
      return 0;
   }

   PyCdromProgress progress;
   progress.setCallbackInst(pyCdromProgressInst);

   string ident;
   bool res = Cdrom.Ident(ident, &progress);

   PyObject *result = Py_BuildValue("(bs)", res, ident.c_str());

   return HandleErrors(result);
}


static PyMethodDef PkgCdromMethods[] =
{
   {"add",PkgCdromAdd,METH_VARARGS,"add(progress) -> Add a cdrom"},
   {"ident",PkgCdromIdent,METH_VARARGS,"ident(progress) -> Ident a cdrom"},
#ifdef COMPAT_0_7
   {"Add",PkgCdromAdd,METH_VARARGS,"Add(progress) -> Add a cdrom"},
   {"Ident",PkgCdromIdent,METH_VARARGS,"Ident(progress) -> Ident a cdrom"},
#endif
   {}
};


static PyObject *PkgCdromNew(PyTypeObject *type,PyObject *Args,PyObject *kwds)
{
   pkgCdrom *cdrom = new pkgCdrom();

   char *kwlist[] = {NULL};
   if (PyArg_ParseTupleAndKeywords(Args,kwds,"",kwlist) == 0)
      return 0;

   CppOwnedPyObject<pkgCdrom> *CdromObj =
	   CppOwnedPyObject_NEW<pkgCdrom>(0,type, *cdrom);

   return CdromObj;
}


PyTypeObject PyCdrom_Type =
{
   PyVarObject_HEAD_INIT(&PyType_Type, 0)
   "apt_pkg.Cdrom",                     // tp_name
   sizeof(CppOwnedPyObject<pkgCdrom>),   // tp_basicsize
   0,                                   // tp_itemsize
   // Methods
   CppOwnedDealloc<pkgCdrom>,     // tp_dealloc
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
   (Py_TPFLAGS_DEFAULT |                // tp_flags
    Py_TPFLAGS_BASETYPE),
   "Cdrom Object",                      // tp_doc
   0,                                   // tp_traverse
   0,                                   // tp_clear
   0,                                   // tp_richcompare
   0,                                   // tp_weaklistoffset
   0,                                   // tp_iter
   0,                                   // tp_iternext
   PkgCdromMethods,                     // tp_methods
   0,                                   // tp_members
   0,                                   // tp_getset
   0,                                   // tp_base
   0,                                   // tp_dict
   0,                                   // tp_descr_get
   0,                                   // tp_descr_set
   0,                                   // tp_dictoffset
   0,                                   // tp_init
   0,                                   // tp_alloc
   PkgCdromNew,                         // tp_new
};

#ifdef COMPAT_0_7
PyObject *GetCdrom(PyObject *Self,PyObject *Args)
{
   PyErr_WarnEx(PyExc_DeprecationWarning, "apt_pkg.GetCdrom() is deprecated. "
                 "Please see apt_pkg.Cdrom() for the replacement.", 1);
   return PkgCdromNew(&PyCdrom_Type,Args,0);
}
#endif




									/*}}}*/
