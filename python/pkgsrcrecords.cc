// -*- mode: cpp; mode: fold -*-
// Description								/*{{{*/
// $Id: pkgsrcrecords.cc,v 1.2 2003/12/26 17:04:22 mdz Exp $
/* ######################################################################

   Package Records - Wrapper for the package records functions

   ##################################################################### */
									/*}}}*/
// Include Files							/*{{{*/
#include "generic.h"
#include "apt_pkgmodule.h"

#include <apt-pkg/sourcelist.h>

#include <Python.h>
									/*}}}*/

struct PkgSrcRecordsStruct
{
   pkgSourceList List;
   pkgSrcRecords *Records;
   pkgSrcRecords::Parser *Last;
   
   PkgSrcRecordsStruct() : Last(0) {
      List.ReadMainList();
      Records = new pkgSrcRecords(List);
   };
   ~PkgSrcRecordsStruct() {
      delete Records;
   };
};
    
// PkgSrcRecords Class							/*{{{*/
// ---------------------------------------------------------------------

static char *doc_PkgSrcRecordsLookup = "xxx";
static PyObject *PkgSrcRecordsLookup(PyObject *Self,PyObject *Args)
{   
   PkgSrcRecordsStruct &Struct = GetCpp<PkgSrcRecordsStruct>(Self);
   
   char *Name = 0;
   if (PyArg_ParseTuple(Args,"s",&Name) == 0)
      return 0;
   
   Struct.Last = Struct.Records->Find(Name, false);
   if (Struct.Last == 0) {
      Struct.Records->Restart();
      Py_INCREF(Py_None);
      return HandleErrors(Py_None);	
   }

   return Py_BuildValue("i", 1);
}

static PyMethodDef PkgSrcRecordsMethods[] = 
{
   {"Lookup",PkgSrcRecordsLookup,METH_VARARGS,doc_PkgSrcRecordsLookup},
   {}
};

static PyObject *PkgSrcRecordsAttr(PyObject *Self,char *Name)
{
   PkgSrcRecordsStruct &Struct = GetCpp<PkgSrcRecordsStruct>(Self);

   if (Struct.Last != 0)
   {
      if (strcmp("Package",Name) == 0)
	 return CppPyString(Struct.Last->Package());
      else if (strcmp("Version",Name) == 0)
	 return CppPyString(Struct.Last->Version());
      else if (strcmp("Maintainer",Name) == 0)
	 return CppPyString(Struct.Last->Maintainer());
      else if (strcmp("Section",Name) == 0)
	 return CppPyString(Struct.Last->Section());
      else if (strcmp("Binaries",Name) == 0) {
         PyObject *List = PyList_New(0);

         for(const char **b = Struct.Last->Binaries();
             *b != 0;
             ++b)
            PyList_Append(List, CppPyString(*b));

         return List; // todo
      } else if (strcmp("Files",Name) == 0)
         return 0; // todo
      else if (strcmp("BuildDepends",Name) == 0) {
         PyObject *List = PyList_New(0);

         vector<pkgSrcRecords::Parser::BuildDepRec> bd;
	 if(!Struct.Last->BuildDepends(bd, false /* arch-only*/))
	    return NULL; // error

	 PyObject *v;
	 for(unsigned int i=0;i<bd.size();i++) {
	    v = Py_BuildValue("(ssii)", bd[i].Package.c_str(), 
			      bd[i].Version.c_str(), bd[i].Op, bd[i].Type);
	    PyList_Append(List, v);
	    Py_DECREF(v);
	 }
         return List;
      }
   }
   
   return Py_FindMethod(PkgSrcRecordsMethods,Self,Name);
}
PyTypeObject PkgSrcRecordsType =
{
   PyObject_HEAD_INIT(&PyType_Type)
   0,			                // ob_size
   "pkgSrcRecords",                          // tp_name
   sizeof(CppOwnedPyObject<PkgSrcRecordsStruct>),   // tp_basicsize
   0,                                   // tp_itemsize
   // Methods
   CppOwnedDealloc<PkgSrcRecordsStruct>,   // tp_dealloc
   0,                                   // tp_print
   PkgSrcRecordsAttr,                      // tp_getattr
   0,                                   // tp_setattr
   0,                                   // tp_compare
   0,                                   // tp_repr
   0,                                   // tp_as_number
   0,                                   // tp_as_sequence
   0,                                   // tp_as_mapping
   0,                                   // tp_hash
};

									/*}}}*/

PyObject *GetPkgSrcRecords(PyObject *Self,PyObject *Args)
{
   PyObject *Owner;
   if (PyArg_ParseTuple(Args,"O!",&PkgCacheType,&Owner) == 0)
      return 0;

   return HandleErrors(CppOwnedPyObject_NEW<PkgSrcRecordsStruct>(Owner,
			   &PkgSrcRecordsType));
}

