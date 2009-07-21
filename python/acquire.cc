// Description								/*{{{*/
// $Id: acquire.cc,v 1.1 2003/06/03 03:03:23 mvo Exp $
/* ######################################################################

   Acquire - Wrapper for the acquire code

   ##################################################################### */

#include "generic.h"
#include "apt_pkgmodule.h"
#include "progress.h"

#include <apt-pkg/acquire-item.h>
#include <apt-pkg/acquire-worker.h>

typedef CppOwnedPyObject<pkgAcquire::Item*> PyAcquireItemObject;
typedef CppOwnedPyObject<pkgAcquire::ItemDesc*> PyAcquireItemDescObject;
typedef CppOwnedPyObject<pkgAcqFile*> PyAcquireFileObject;
typedef CppOwnedPyObject<pkgAcquire::Worker*> PyAcquireWorkerObject;


struct PyAcquireItems {
    PyAcquireFileObject *file;
    PyAcquireItemObject *item;
};

// Keep a vector to PyAcquireItemObject pointers, so we can set the Object
// pointers to NULL when deallocating the main object (mostly AcquireFile).
struct PyAcquireObject : public CppPyObject<pkgAcquire*> {
    map <pkgAcquire::Item*,PyAcquireItems> item_map;
    map <pkgAcquire::ItemDesc*,PyAcquireItemDescObject*> itemdesc_map;
    map <pkgAcquire::Worker*,PyAcquireWorkerObject*> worker_map;
};


static PyObject *acquireworker_get_current_item(PyObject *self, void *closure)
{
    pkgAcquire::Worker *worker = GetCpp<pkgAcquire::Worker*>(self);

    if (worker->CurrentItem == NULL) {
        Py_RETURN_NONE;
    }

    PyAcquireObject *PyAcquire = (PyAcquireObject *)GetOwner<pkgAcquire::Worker*>(self);

    pkgAcquire::Item *Item = worker->CurrentItem->Owner;

    PyObject *PyItem;
    if (PyAcquire->item_map[Item].item)
        PyItem = PyAcquire->item_map[Item].item;
    else
        PyItem = PyAcquire->item_map[Item].item = (PyAcquireItemObject*)PyAcquireItem_FromCpp(Item,false,PyAcquire);

    return PyAcquireItemDesc_FromCpp(worker->CurrentItem,false,PyItem);
}

static PyObject *acquireworker_get_status(PyObject *self, void *closure)
{
    return CppPyString(GetCpp<pkgAcquire::Worker*>(self)->Status);
}

static PyObject *acquireworker_get_current_size(PyObject *self, void *closure)
{
    return Py_BuildValue("k",GetCpp<pkgAcquire::Worker*>(self)->CurrentSize);
}

static PyObject *acquireworker_get_total_size(PyObject *self, void *closure)
{
    return Py_BuildValue("k",GetCpp<pkgAcquire::Worker*>(self)->TotalSize);
}

static PyObject *acquireworker_get_resumepoint(PyObject *self, void *closure)
{
    return Py_BuildValue("k",GetCpp<pkgAcquire::Worker*>(self)->ResumePoint);
}

static PyGetSetDef acquireworker_getset[] = {
    {"current_item",acquireworker_get_current_item},
    {"status",acquireworker_get_status},
    {"current_size",acquireworker_get_current_size},
    {"total_size",acquireworker_get_total_size},
    {"resumepoint",acquireworker_get_resumepoint},
    {NULL}
};


PyTypeObject PyAcquireWorker_Type =
{
   PyVarObject_HEAD_INIT(&PyType_Type, 0)
   "apt_pkg.AcquireWorker",                // tp_name
   sizeof(CppOwnedPyObject<pkgAcquire::Worker*>),// tp_basicsize
   0,                                   // tp_itemsize
   // Methods
   CppOwnedDealloc<pkgAcquire::Worker*>, // tp_dealloc
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
   Py_TPFLAGS_DEFAULT|                // tp_flags
   Py_TPFLAGS_HAVE_GC,
   0,                 // tp_doc
   CppOwnedTraverse<pkgAcquire::Worker*>, // tp_traverse
   CppOwnedClear<pkgAcquire::Worker*>,    // tp_clear
   0,                                    // tp_richcompare
   0,                                    // tp_weaklistoffset
   0,                                    // tp_iter
   0,                                    // tp_iternext
   0,                                    // tp_methods
   0,                                    // tp_members
   acquireworker_getset,                 // tp_getset
};

static PyObject *acquireitemdesc_get_uri(PyObject *self, void *closure)
{
    return CppPyString(GetCpp<pkgAcquire::ItemDesc*>(self)->URI);
}
static PyObject *acquireitemdesc_get_description(PyObject *self, void *closure)
{
    return CppPyString(GetCpp<pkgAcquire::ItemDesc*>(self)->Description);
}
static PyObject *acquireitemdesc_get_shortdesc(PyObject *self, void *closure)
{
    return CppPyString(GetCpp<pkgAcquire::ItemDesc*>(self)->ShortDesc);
}
static PyObject *acquireitemdesc_get_owner(CppOwnedPyObject<pkgAcquire::ItemDesc*> *self, void *closure)
{
    if (self->Owner != NULL) {
        Py_INCREF(self->Owner);
        return self->Owner;
    }
    else if (self->Object && self->Object->Owner != NULL) {
        self->Owner = PyAcquireItem_FromCpp(self->Object->Owner);
        Py_INCREF(self->Owner);
        return self->Owner;
    }
    Py_RETURN_NONE;
}

static PyGetSetDef acquireitemdesc_getset[] = {
   {"uri",acquireitemdesc_get_uri,0,"The URI from which to download this item."},
   {"description",acquireitemdesc_get_description},
   {"shortdesc",acquireitemdesc_get_shortdesc},
   {"owner",(getter)acquireitemdesc_get_owner},
   {NULL}
};

static char *acquireitemdesc_doc =
    "Represent an AcquireItemDesc";

PyTypeObject PyAcquireItemDesc_Type =
{
   PyVarObject_HEAD_INIT(&PyType_Type, 0)
   "apt_pkg.AcquireItemDesc",                // tp_name
   sizeof(CppOwnedPyObject<pkgAcquire::ItemDesc*>),// tp_basicsize
   0,                                   // tp_itemsize
   // Methods
   CppOwnedDealloc<pkgAcquire::ItemDesc*>, // tp_dealloc
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
    Py_TPFLAGS_HAVE_GC),
   acquireitemdesc_doc,                 // tp_doc
   CppOwnedTraverse<pkgAcquire::ItemDesc*>,// tp_traverse
   CppOwnedClear<pkgAcquire::ItemDesc*>, // tp_clear
   0,                                   // tp_richcompare
   0,                                   // tp_weaklistoffset
   0,                                   // tp_iter
   0,                                   // tp_iternext
   0,                                   // tp_methods
   0,                                   // tp_members
   acquireitemdesc_getset,              // tp_getset
   0,                                   // tp_base
   0,                                   // tp_dict
   0,                                   // tp_descr_get
   0,                                   // tp_descr_set
   0,                                   // tp_dictoffset
   0,                                   // tp_init
   0,                                   // tp_alloc
   0,                                   // tp_new
};

inline pkgAcquire::Item *acquireitem_tocpp(PyObject *self) {
    pkgAcquire::Item *itm = GetCpp<pkgAcquire::Item*>(self);
    if (itm == 0)
        PyErr_SetString(PyExc_ValueError, "Acquire() has been shut down or "
                        "the AcquireFile() object has been deallocated.");
    return itm;
}

#define MkGet(PyFunc,Ret) static PyObject *PyFunc(PyObject *Self,void*) \
{ \
    pkgAcquire::Item *Itm = acquireitem_tocpp(Self); \
    if (Itm == 0) \
        return 0; \
    return Ret; \
}

// Define our getters
MkGet(AcquireItemGetComplete,Py_BuildValue("i",Itm->Complete));
MkGet(AcquireItemGetDescURI,Safe_FromString(Itm->DescURI().c_str()));
MkGet(AcquireItemGetDestFile,Safe_FromString(Itm->DestFile.c_str()));
MkGet(AcquireItemGetErrorText,Safe_FromString(Itm->ErrorText.c_str()));
MkGet(AcquireItemGetFileSize,Py_BuildValue("i",Itm->FileSize));
MkGet(AcquireItemGetID,Py_BuildValue("k",Itm->ID));
MkGet(AcquireItemGetMode,Py_BuildValue("s",Itm->Mode));
MkGet(AcquireItemGetIsTrusted,Py_BuildValue("i",Itm->IsTrusted()));
MkGet(AcquireItemGetLocal,Py_BuildValue("i",Itm->Local));
MkGet(AcquireItemGetStatus,Py_BuildValue("i",Itm->Status));

// Constants
MkGet(AcquireItemGetStatIdle,Py_BuildValue("i", pkgAcquire::Item::StatIdle));
MkGet(AcquireItemGetStatFetching,Py_BuildValue("i", pkgAcquire::Item::StatFetching));
MkGet(AcquireItemGetStatDone,Py_BuildValue("i", pkgAcquire::Item::StatDone));
MkGet(AcquireItemGetStatError,Py_BuildValue("i", pkgAcquire::Item::StatError));
MkGet(AcquireItemGetStatAuthError,Py_BuildValue("i", pkgAcquire::Item::StatAuthError));
#undef MkGet

static int AcquireItemSetID(PyObject *self, PyObject *value, void *closure)
{
    pkgAcquire::Item *Itm = acquireitem_tocpp(self);
    if (Itm == 0)
        return -1;
    if (PyLong_Check(value)) {
        Itm->ID = PyLong_AsLong(value);
    }
    else if (PyInt_Check(value)) {
        Itm->ID = PyInt_AsLong(value);
    }
    else {
        PyErr_SetString(PyExc_TypeError, "value must be integer.");
        return -1;
    }
    return 0;
}


static PyGetSetDef AcquireItemGetSet[] = {
    {"complete",AcquireItemGetComplete},
    {"desc_uri",AcquireItemGetDescURI},
    {"destfile",AcquireItemGetDestFile},
    {"error_text",AcquireItemGetErrorText},
    {"filesize",AcquireItemGetFileSize},
    {"id",AcquireItemGetID,AcquireItemSetID},
    {"mode",AcquireItemGetMode},
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
   pkgAcquire::Item *Itm = acquireitem_tocpp(Self);
   if (Itm == 0)
      return 0;

   return PyString_FromFormat("<%s object: "
			"Status: %i Complete: %i Local: %i IsTrusted: %i "
	                "FileSize: %lu DestFile:'%s' "
                        "DescURI: '%s' ID:%lu ErrorText: '%s'>",
        Self->ob_type->tp_name,
	    Itm->Status, Itm->Complete, Itm->Local, Itm->IsTrusted(),
	    Itm->FileSize, Itm->DestFile.c_str(), Itm->DescURI().c_str(),
	    Itm->ID,Itm->ErrorText.c_str());
}

static void AcquireItemDealloc(PyObject *self) {
   pkgAcquire::Item *file = GetCpp<pkgAcquire::Item*>(self);
   PyAcquireObject *owner = (PyAcquireObject *)GetOwner<pkgAcquire::Item*>(self);

   // Simply deallocate the object if we have no owner.
   if (owner != NULL && !((CppPyObject<pkgAcquire::Item*> *)self)->NoDelete) {
      PyAcquireItems &items = owner->item_map[file];

      if (items.item && items.item != self)
          items.item->Object = NULL;
      if (items.file && items.item != self)
          items.file->Object = NULL;
      owner->item_map.erase(file);
   }

   CppOwnedDeallocPtr<pkgAcquire::Item*>(self);
}



PyTypeObject PyAcquireItem_Type =
{
   PyVarObject_HEAD_INIT(&PyType_Type, 0)
   "apt_pkg.AcquireItem",         // tp_name
   sizeof(CppOwnedPyObject<pkgAcquire::Item*>),   // tp_basicsize
   0,                                   // tp_itemsize
   // Methods
   AcquireItemDealloc,                  // tp_dealloc
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

   // TODO: Delete all objects here
   map<pkgAcquire::Item*,PyAcquireItems> items = ((PyAcquireObject *)Self)->item_map;
   for (map<pkgAcquire::Item*,PyAcquireItems>::iterator I = items.begin();
        I != items.end(); I++) {
        (*I).second.file->Object = NULL;
        (*I).second.item->Object = NULL;
   }



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

static PyObject *PkgAcquireGetWorkers(PyObject *self, void *closure)
{
    PyObject *List = PyList_New(0);
    pkgAcquire *Owner = GetCpp<pkgAcquire*>(self);
    CppOwnedPyObject<pkgAcquire::Worker*> *PyWorker = NULL;
    for(pkgAcquire::Worker *Worker = Owner->WorkersBegin();
        Worker != 0; Worker = Owner->WorkerStep(Worker)) {
        PyWorker = CppOwnedPyObject_NEW<pkgAcquire::Worker*>(self,&PyAcquireWorker_Type, Worker);
        PyWorker->NoDelete = true;
        PyList_Append(List, PyWorker);
    }
    return List;
}
static PyObject *PkgAcquireGetItems(PyObject *Self,void*)
{
   pkgAcquire *fetcher = GetCpp<pkgAcquire*>(Self);
   PyObject *List = PyList_New(0);
   PyAcquireItemObject *Obj;
   for (pkgAcquire::ItemIterator I = fetcher->ItemsBegin();
        I != fetcher->ItemsEnd(); I++)
   {

      if (((PyAcquireObject *)Self)->item_map[*I].item)
        PyList_Append(List, ((PyAcquireObject *)Self)->item_map[*I].item);
      else {
        Obj = CppOwnedPyObject_NEW<pkgAcquire::Item*>(Self,&PyAcquireItem_Type,*I);
        Obj->NoDelete = true;
        PyList_Append(List,Obj);
        ((PyAcquireObject *)Self)->item_map[*I].item = Obj;
        Py_DECREF(Obj);
    }
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
    {"workers",PkgAcquireGetWorkers},
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
   char *kwlist[] = {"progress", 0};
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

   PyAcquireObject *FetcherObj = (PyAcquireObject *)
	   CppPyObject_NEW<pkgAcquire*>(type, fetcher);

   // prepare our map of items.
   new (&FetcherObj->item_map) map<pkgAcquire::Item*,PyAcquireItems>();
   return FetcherObj;
}

static char *doc_PkgAcquire = "Acquire(progress) -> Acquire() object.\n\n"
    "Create a new acquire object. The parameter *progress* can be used to\n"
    "specify a apt.progress.FetchProgress() object, which will display the\n"
    "progress of the fetching.";

PyTypeObject PyAcquire_Type =
{
   PyVarObject_HEAD_INIT(&PyType_Type, 0)
   "apt_pkg.Acquire",                   // tp_name
   sizeof(PyAcquireObject),             // tp_basicsize
   0,                                   // tp_itemsize
   // Methods
   CppDeallocPtr<pkgAcquire*>,          // tp_dealloc
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
   (Py_TPFLAGS_DEFAULT |                // tp_flags
    Py_TPFLAGS_BASETYPE),
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
    PyErr_WarnEx(PyExc_DeprecationWarning,"apt_pkg.GetAcquire() is deprecated."
                 " Please see apt_pkg.Acquire() for the replacement.", 1);
    return PkgAcquireNew(&PyAcquire_Type,Args,0);
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
				   &PyAcquire_Type, &pyfetcher, &uri, &md5,
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
   CppOwnedPyObject<pkgAcqFile*> *AcqFileObj = CppOwnedPyObject_NEW<pkgAcqFile*>(pyfetcher, type);
   AcqFileObj->Object = af;

   // Register the file so we can remove it later.
   ((PyAcquireObject *)pyfetcher)->item_map[af].file = AcqFileObj;

   return AcqFileObj;
}


static char *doc_PkgAcquireFile =
    "AcquireFile(owner, uri[, md5, size, descr, short_descr, destdir,"
    "destfile]) -> New AcquireFile() object\n\n"
    "The parameter *owner* refers to an apt_pkg.Acquire() object. You can use\n"
    "*destdir* OR *destfile* to specify the destination directory/file.";

PyTypeObject PyAcquireFile_Type =
{
   PyVarObject_HEAD_INIT(&PyType_Type, 0)
   "apt_pkg.AcquireFile",                // tp_name
   sizeof(CppOwnedPyObject<pkgAcqFile*>),// tp_basicsize
   0,                                   // tp_itemsize
   // Methods
   AcquireItemDealloc,                  // tp_dealloc
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
    Py_TPFLAGS_BASETYPE |
    Py_TPFLAGS_HAVE_GC),
   doc_PkgAcquireFile,                  // tp_doc
   CppOwnedTraverse<pkgAcqFile*>,       // tp_traverse
   CppOwnedClear<pkgAcqFile*>,          // tp_clear
   0,                                   // tp_richcompare
   0,                                   // tp_weaklistoffset
   0,                                   // tp_iter
   0,                                   // tp_iternext
   0,                                   // tp_methods
   0,                                   // tp_members
   0,                   // tp_getset
   &PyAcquireItem_Type,                    // tp_base
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
   PyErr_WarnEx(PyExc_DeprecationWarning, "apt_pkg.GetPkgAcqFile() is "
                "deprecated. Please see apt_pkg.AcquireFile() for the "
                "replacement", 1);
   PyObject *pyfetcher;
   char *uri, *md5, *descr, *shortDescr, *destDir, *destFile;
   int size = 0;
   uri = md5 = descr = shortDescr = destDir = destFile = "";

   char * kwlist[] = {"owner","uri", "md5", "size", "descr", "shortDescr",
                      "destDir", "destFile", NULL};

   if (PyArg_ParseTupleAndKeywords(Args, kwds, "O!s|sissss", kwlist,
				   &PyAcquire_Type, &pyfetcher, &uri, &md5,
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
   CppPyObject<pkgAcqFile*> *AcqFileObj =   CppPyObject_NEW<pkgAcqFile*>(&PyAcquireFile_Type);
   AcqFileObj->Object = af;
   AcqFileObj->NoDelete = true;

   return AcqFileObj;
}
#endif
