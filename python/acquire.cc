// Description								/*{{{*/
// $Id: acquire.cc,v 1.1 2003/06/03 03:03:23 mvo Exp $
/* ######################################################################

   Acquire - Wrapper for the acquire code

   ##################################################################### */

#include "generic.h"
#include "apt_pkgmodule.h"
#include "progress.h"

#include <apt-pkg/acquire-item.h>

#define MkGet(PyFunc,Ret) static PyObject *PyFunc(PyObject *Self,void*) \
{ \
    pkgAcquire::ItemIterator &I = GetCpp<pkgAcquire::ItemIterator>(Self); \
    return Ret; \
}

// Define our getters
MkGet(AcquireItemGetComplete,Py_BuildValue("i",(*I)->Complete));
MkGet(AcquireItemGetDescURI,Safe_FromString((*I)->DescURI().c_str()));
MkGet(AcquireItemGetDestFile,Safe_FromString((*I)->DestFile.c_str()));
MkGet(AcquireItemGetErrorText,Safe_FromString((*I)->ErrorText.c_str()));
MkGet(AcquireItemGetFileSize,Py_BuildValue("i",(*I)->FileSize));
MkGet(AcquireItemGetID,Py_BuildValue("i",(*I)->ID));
MkGet(AcquireItemGetIsTrusted,Py_BuildValue("i",(*I)->IsTrusted()));
MkGet(AcquireItemGetLocal,Py_BuildValue("i",(*I)->Local));
MkGet(AcquireItemGetStatus,Py_BuildValue("i",(*I)->Status));

// Constants
MkGet(AcquireItemGetStatIdle,Py_BuildValue("i", pkgAcquire::Item::StatIdle));
MkGet(AcquireItemGetStatFetching,Py_BuildValue("i", pkgAcquire::Item::StatFetching));
MkGet(AcquireItemGetStatDone,Py_BuildValue("i", pkgAcquire::Item::StatDone));
MkGet(AcquireItemGetStatError,Py_BuildValue("i", pkgAcquire::Item::StatError));
MkGet(AcquireItemGetStatAuthError,Py_BuildValue("i", pkgAcquire::Item::StatAuthError));
#undef MkGet

static PyGetSetDef AcquireItemGetSet[] = {
    {"complete",AcquireItemGetComplete},
    {"desc_uri",AcquireItemGetDescURI},
    {"destfile",AcquireItemGetDestFile},
    {"error_text",AcquireItemGetErrorText},
    {"filesize",AcquireItemGetFileSize},
    {"is",AcquireItemGetID},
    {"is_trusted",AcquireItemGetIsTrusted},
    {"local",AcquireItemGetLocal},
    {"status",AcquireItemGetStatus},
    {"stat_idle",AcquireItemGetStatIdle},
    {"stat_fetching",AcquireItemGetStatFetching},
    {"stat_done",AcquireItemGetStatDone},
    {"stat_error",AcquireItemGetStatError},
    {"stat_auth_error",AcquireItemGetStatAuthError},
#ifdef COMPAT_0_7
    {"Complete",AcquireItemGetComplete},
    {"DescURI",AcquireItemGetDescURI},
    {"DestFile",AcquireItemGetDestFile},
    {"ErrorText",AcquireItemGetErrorText},
    {"FileSize",AcquireItemGetFileSize},
    {"ID",AcquireItemGetID},
    {"IsTrusted",AcquireItemGetIsTrusted},
    {"Local",AcquireItemGetLocal},
    {"Status",AcquireItemGetStatus},
    {"StatIdle",AcquireItemGetStatIdle},
    {"StatFetching",AcquireItemGetStatFetching},
    {"StatDone",AcquireItemGetStatDone},
    {"StatError",AcquireItemGetStatError},
    {"StatAuthError",AcquireItemGetStatAuthError},
#endif
    {}
};



static PyObject *AcquireItemRepr(PyObject *Self)
{
   pkgAcquire::ItemIterator &I = GetCpp<pkgAcquire::ItemIterator>(Self);

   char S[300];
   snprintf(S,sizeof(S),"<pkgAcquire::ItemIterator object: "
			"Status: %i Complete: %i Local: %i IsTrusted: %i "
	                "FileSize: %i DestFile:'%s' "
                        "DescURI: '%s' ID:%i ErrorText: '%s'>",
	    (*I)->Status, (*I)->Complete, (*I)->Local, (*I)->IsTrusted(),
	    (*I)->FileSize, (*I)->DestFile.c_str(), (*I)->DescURI().c_str(),
	    (*I)->ID,(*I)->ErrorText.c_str());
   return PyString_FromString(S);
}


PyTypeObject AcquireItemType =
{
   PyObject_HEAD_INIT(&PyType_Type)
   #if PY_MAJOR_VERSION < 3
   0,			                // ob_size
   #endif
   "apt_pkg.AcquireItem",         // tp_name
   sizeof(CppOwnedPyObject<pkgAcquire::ItemIterator>),   // tp_basicsize
   0,                                   // tp_itemsize
   // Methods
   CppOwnedDealloc<pkgAcquire::ItemIterator>,          // tp_dealloc
   0,                                   // tp_print
   0,                                   // tp_getattr
   0,                                   // tp_setattr
   0,                                   // tp_compare
   AcquireItemRepr,                     // tp_repr
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
   "AcquireItem Object",                // tp_doc
   0,                                   // tp_traverse
   0,                                   // tp_clear
   0,                                   // tp_richcompare
   0,                                   // tp_weaklistoffset
   0,                                   // tp_iter
   0,                                   // tp_iternext
   0,                                   // tp_methods
   0,                                   // tp_members
   AcquireItemGetSet,                   // tp_getset
};


static PyObject *PkgAcquireRun(PyObject *Self,PyObject *Args)
{
   pkgAcquire *fetcher = GetCpp<pkgAcquire*>(Self);

   int pulseInterval = 500000;
   if (PyArg_ParseTuple(Args, "|i", &pulseInterval) == 0)
      return 0;

   pkgAcquire::RunResult run = fetcher->Run(pulseInterval);

   return HandleErrors(Py_BuildValue("i",run));
}

static PyObject *PkgAcquireShutdown(PyObject *Self,PyObject *Args)
{
   pkgAcquire *fetcher = GetCpp<pkgAcquire*>(Self);

   if (PyArg_ParseTuple(Args, "") == 0)
      return 0;

   fetcher->Shutdown();

   Py_INCREF(Py_None);
   return HandleErrors(Py_None);
}

static PyMethodDef PkgAcquireMethods[] =
{
   {"run",PkgAcquireRun,METH_VARARGS,"Run the fetcher"},
   {"shutdown",PkgAcquireShutdown, METH_VARARGS,"Shutdown the fetcher"},
   #ifdef COMPAT_0_7
   {"Run",PkgAcquireRun,METH_VARARGS,"Run the fetcher"},
   {"Shutdown",PkgAcquireShutdown, METH_VARARGS,"Shutdown the fetcher"},
   #endif
   {}
};

#define fetcher (GetCpp<pkgAcquire*>(Self))
static PyObject *PkgAcquireGetTotalNeeded(PyObject *Self,void*) {
   return Py_BuildValue("d", fetcher->TotalNeeded());
}
static PyObject *PkgAcquireGetFetchNeeded(PyObject *Self,void*) {
   return Py_BuildValue("d", fetcher->FetchNeeded());
}
static PyObject *PkgAcquireGetPartialPresent(PyObject *Self,void*) {
      return Py_BuildValue("d", fetcher->PartialPresent());
}
#undef fetcher
static PyObject *PkgAcquireGetItems(PyObject *Self,void*)
{
   pkgAcquire *fetcher = GetCpp<pkgAcquire*>(Self);
   PyObject *List = PyList_New(0);
   for (pkgAcquire::ItemIterator I = fetcher->ItemsBegin();
        I != fetcher->ItemsEnd(); I++)
   {
      PyObject *Obj;
      Obj = CppOwnedPyObject_NEW<pkgAcquire::ItemIterator>(Self,
                                                           &AcquireItemType,I);
      PyList_Append(List,Obj);
      Py_DECREF(Obj);

   }
   return List;
}
// some constants
static PyObject *PkgAcquireGetResultContinue(PyObject *Self,void*) {
      return Py_BuildValue("i", pkgAcquire::Continue);
}
static PyObject *PkgAcquireGetResultFailed(PyObject *Self,void*) {
      return Py_BuildValue("i", pkgAcquire::Failed);
}
static PyObject *PkgAcquireGetResultCancelled(PyObject *Self,void*) {
      return Py_BuildValue("i", pkgAcquire::Cancelled);
}

static PyGetSetDef PkgAcquireGetSet[] = {
    {"fetch_needed",PkgAcquireGetFetchNeeded},
    {"items",PkgAcquireGetItems},
    {"partial_present",PkgAcquireGetPartialPresent},
    {"result_cancelled",PkgAcquireGetResultCancelled},
    {"result_continue",PkgAcquireGetResultContinue},
    {"result_failed",PkgAcquireGetResultFailed},
    {"total_needed",PkgAcquireGetTotalNeeded},
    #ifdef COMPAT_0_7
    {"FetchNeeded",PkgAcquireGetFetchNeeded},
    {"Items",PkgAcquireGetItems},
    {"PartialPresent",PkgAcquireGetPartialPresent},
    {"ResultCancelled",PkgAcquireGetResultCancelled},
    {"ResultContinue",PkgAcquireGetResultContinue},
    {"ResultFailed",PkgAcquireGetResultFailed},
    {"TotalNeeded",PkgAcquireGetTotalNeeded},
    #endif
    {}
};

static PyObject *PkgAcquireNew(PyTypeObject *type,PyObject *Args,PyObject *kwds) {
   pkgAcquire *fetcher;

   PyObject *pyFetchProgressInst = NULL;
   static char *kwlist[] = {"progress", 0};
   if (PyArg_ParseTupleAndKeywords(Args,kwds,"|O",kwlist,&pyFetchProgressInst) == 0)
      return 0;

   if (pyFetchProgressInst != NULL) {
      // FIXME: memleak?
      PyFetchProgress *progress = new PyFetchProgress();
      progress->setCallbackInst(pyFetchProgressInst);
      fetcher = new pkgAcquire(progress);
   } else {
      fetcher = new pkgAcquire();
   }

   CppPyObject<pkgAcquire*> *FetcherObj =
	   CppPyObject_NEW<pkgAcquire*>(type, fetcher);

   return FetcherObj;
}

static char *doc_PkgAcquire = "Acquire(progress) -> Acquire() object.\n\n"
    "Create a new acquire object. The parameter *progress* can be used to\n"
    "specify a apt.progress.FetchProgress() object, which will display the\n"
    "progress of the fetching.";

PyTypeObject PkgAcquireType =
{
   PyObject_HEAD_INIT(&PyType_Type)
   #if PY_MAJOR_VERSION < 3
   0,                                   // ob_size
   #endif
   "apt_pkg.Acquire",                   // tp_name
   sizeof(CppPyObject<pkgAcquire*>),    // tp_basicsize
   0,                                   // tp_itemsize
   // Methods
   CppDealloc<pkgAcquire*>,             // tp_dealloc
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
   doc_PkgAcquire,                      // tp_doc
   0,                                   // tp_traverse
   0,                                   // tp_clear
   0,                                   // tp_richcompare
   0,                                   // tp_weaklistoffset
   0,                                   // tp_iter
   0,                                   // tp_iternext
   PkgAcquireMethods,                   // tp_methods
   0,                                   // tp_members
   PkgAcquireGetSet,                    // tp_getset
   0,                                   // tp_base
   0,                                   // tp_dict
   0,                                   // tp_descr_get
   0,                                   // tp_descr_set
   0,                                   // tp_dictoffset
   0,                                   // tp_init
   0,                                   // tp_alloc
   PkgAcquireNew,                       // tp_new
};

#ifdef COMPAT_0_7
PyObject *GetAcquire(PyObject *Self,PyObject *Args)
{
    return PkgAcquireNew(&PkgAcquireType,Args,0);
}
#endif

static PyObject *PkgAcquireFileNew(PyTypeObject *type, PyObject *Args, PyObject * kwds)
{
   PyObject *pyfetcher;
   char *uri, *md5, *descr, *shortDescr, *destDir, *destFile;
   int size = 0;
   uri = md5 = descr = shortDescr = destDir = destFile = "";

   char * kwlist[] = {"owner","uri", "md5", "size", "descr", "short_descr",
                      "destdir", "destfile", NULL};

   if (PyArg_ParseTupleAndKeywords(Args, kwds, "O!s|sissss", kwlist,
				   &PkgAcquireType, &pyfetcher, &uri, &md5,
				   &size, &descr, &shortDescr, &destDir, &destFile) == 0)
      return 0;

   pkgAcquire *fetcher = GetCpp<pkgAcquire*>(pyfetcher);
   pkgAcqFile *af = new pkgAcqFile(fetcher,  // owner
				   uri, // uri
				   md5,  // md5
				   size,   // size
				   descr, // descr
				   shortDescr,
				   destDir,
				   destFile); // short-desc
   CppPyObject<pkgAcqFile*> *AcqFileObj = CppPyObject_NEW<pkgAcqFile*>(type);
   AcqFileObj->Object = af;

   return AcqFileObj;
}


static char *doc_PkgAcquireFile =
    "AcquireFile(owner, uri[, md5, size, descr, short_descr, destdir,"
    "destfile]) -> New AcquireFile() object\n\n"
    "The parameter *owner* refers to an apt_pkg.Acquire() object. You can use\n"
    "*destdir* OR *destfile* to specify the destination directory/file.";

PyTypeObject PkgAcquireFileType =
{
   PyObject_HEAD_INIT(&PyType_Type)
   #if PY_MAJOR_VERSION < 3
   0,			                // ob_size
   #endif
   "apt_pkg.AcquireFile",                   // tp_name
   sizeof(CppPyObject<pkgAcqFile*>),// tp_basicsize
   0,                                   // tp_itemsize
   // Methods
   CppDealloc<pkgAcqFile*>,        // tp_dealloc
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
   doc_PkgAcquireFile,                  // tp_doc
   0,                                   // tp_traverse
   0,                                   // tp_clear
   0,                                   // tp_richcompare
   0,                                   // tp_weaklistoffset
   0,                                   // tp_iter
   0,                                   // tp_iternext
   0,                                   // tp_methods
   0,                                   // tp_members
   0,                                   // tp_getset
   0,                                   // tp_base
   0,                                   // tp_dict
   0,                                   // tp_descr_get
   0,                                   // tp_descr_set
   0,                                   // tp_dictoffset
   0,                                   // tp_init
   0,                                   // tp_alloc
   PkgAcquireFileNew,                   // tp_new
};

#ifdef COMPAT_0_7
char *doc_GetPkgAcqFile =
"GetPkgAcqFile(pkgAquire, uri[, md5, size, descr, shortDescr, destDir, destFile]) -> PkgAcqFile\n";
PyObject *GetPkgAcqFile(PyObject *Self, PyObject *Args, PyObject * kwds)
{
   PyObject *pyfetcher;
   char *uri, *md5, *descr, *shortDescr, *destDir, *destFile;
   int size = 0;
   uri = md5 = descr = shortDescr = destDir = destFile = "";

   char * kwlist[] = {"owner","uri", "md5", "size", "descr", "shortDescr",
                      "destDir", "destFile", NULL};

   if (PyArg_ParseTupleAndKeywords(Args, kwds, "O!s|sissss", kwlist,
				   &PkgAcquireType, &pyfetcher, &uri, &md5,
				   &size, &descr, &shortDescr, &destDir, &destFile) == 0)
      return 0;

   pkgAcquire *fetcher = GetCpp<pkgAcquire*>(pyfetcher);
   pkgAcqFile *af = new pkgAcqFile(fetcher,  // owner
				   uri, // uri
				   md5,  // md5
				   size,   // size
				   descr, // descr
				   shortDescr,
				   destDir,
				   destFile); // short-desc
   CppPyObject<pkgAcqFile*> *AcqFileObj =   CppPyObject_NEW<pkgAcqFile*>(&PkgAcquireFileType);
   AcqFileObj->Object = af;

   return AcqFileObj;
}
#endif
