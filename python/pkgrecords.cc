// -*- mode: cpp; mode: fold -*-
// Description								/*{{{*/
// $Id: pkgrecords.cc,v 1.1 2001/02/20 06:32:01 jgg Exp $
/* ######################################################################

   Package Records - Wrapper for the package records functions

   ##################################################################### */
									/*}}}*/
// Include Files							/*{{{*/
#include "generic.h"
#include "apt_pkgmodule.h"

#include <apt-pkg/pkgrecords.h>

#include <python/Python.h>
									/*}}}*/

struct PkgRecordsStruct
{
   pkgRecords Records;
   pkgRecords::Parser *Last;
   
   PkgRecordsStruct(pkgCache *Cache) : Records(*Cache), Last(0) {};
   PkgRecordsStruct() : Records(*(pkgCache *)0) {abort();};  // G++ Bug..
};
    
// PkgRecords Class							/*{{{*/
// ---------------------------------------------------------------------
static PyMethodDef PkgRecordsMethods[];

static PyObject *PkgRecordsAttr(PyObject *Self,char *Name)
{
   PkgRecordsStruct &Struct = GetCpp<PkgRecordsStruct>(Self);

   if (Struct.Last != 0)
   {
      if (strcmp("FileName",Name) == 0)
	 return CppPyString(Struct.Last->FileName());
      else if (strcmp("MD5Hash",Name) == 0)
	 return CppPyString(Struct.Last->MD5Hash());
      else if (strcmp("SourcePkg",Name) == 0)
	 return CppPyString(Struct.Last->SourcePkg());
      else if (strcmp("Maintainer",Name) == 0)
	 return CppPyString(Struct.Last->Maintainer());
      else if (strcmp("ShortDesc",Name) == 0)
	 return CppPyString(Struct.Last->ShortDesc());
      else if (strcmp("LongDesc",Name) == 0)
	 return CppPyString(Struct.Last->LongDesc());
      else if (strcmp("Name",Name) == 0)
	 return CppPyString(Struct.Last->Name());
   }
   
   return Py_FindMethod(PkgRecordsMethods,Self,Name);
}

static PyObject *PkgRecordsLookup(PyObject *Self,PyObject *Args)
{   
   PkgRecordsStruct &Struct = GetCpp<PkgRecordsStruct>(Self);
   
   PyObject *PkgFObj;
   long int Index;
   if (PyArg_ParseTuple(Args,"(O!l)",&PackageFileType,&PkgFObj,&Index) == 0)
      return 0;
   
   // Get the index and check to make sure it is reasonable
   pkgCache::PkgFileIterator &PkgF = GetCpp<pkgCache::PkgFileIterator>(PkgFObj);
   pkgCache *Cache = PkgF.Cache();
   if (Cache->DataEnd() <= Cache->VerFileP + Index + 1 ||
       Cache->VerFileP[Index].File != PkgF.Index())
   {
      PyErr_SetNone(PyExc_IndexError);
      return 0;
   }
   
   // Do the lookup
   Struct.Last = &Struct.Records.Lookup(pkgCache::VerFileIterator(*Cache,Cache->VerFileP+Index));
   Py_INCREF(Py_None);
   return HandleErrors(Py_None);   
}

static PyMethodDef PkgRecordsMethods[] = 
{
   {"Lookup",PkgRecordsLookup,METH_VARARGS,"Changes to a new package"},
   {}
};

PyTypeObject PkgRecordsType =
{
   PyObject_HEAD_INIT(&PyType_Type)
   0,			                // ob_size
   "pkgRecords",                          // tp_name
   sizeof(CppOwnedPyObject<PkgRecordsStruct>),   // tp_basicsize
   0,                                   // tp_itemsize
   // Methods
   CppOwnedDealloc<PkgRecordsStruct>,   // tp_dealloc
   0,                                   // tp_print
   PkgRecordsAttr,                      // tp_getattr
   0,                                   // tp_setattr
   0,                                   // tp_compare
   0,                                   // tp_repr
   0,                                   // tp_as_number
   0,                                   // tp_as_sequence
   0,                                   // tp_as_mapping
   0,                                   // tp_hash
};

									/*}}}*/

PyObject *GetPkgRecords(PyObject *Self,PyObject *Args)
{
   PyObject *Owner;
   if (PyArg_ParseTuple(Args,"O!",&PkgCacheType,&Owner) == 0)
      return 0;

   return HandleErrors(CppOwnedPyObject_NEW<PkgRecordsStruct>(Owner,&PkgRecordsType,
							      GetCpp<pkgCache *>(Owner)));
}

