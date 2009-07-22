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


typedef CppOwnedPyObject<pkgAcquire::Worker*> PyAcquireWorkerObject;
struct PyAcquireItems {
    CppOwnedPyObject<pkgAcqFile*> *file;
    CppOwnedPyObject<pkgAcquire::Item*> *item;
    CppOwnedPyObject<pkgAcquire::ItemDesc*> *desc;
};

typedef map<pkgAcquire::Item*,PyAcquireItems> item_map;
typedef map<pkgAcquire::Worker*,PyAcquireWorkerObject*> worker_map;

// Keep a vector to PyAcquireItemObject pointers, so we can set the Object
// pointers to NULL when deallocating the main object (mostly AcquireFile).
struct PyAcquireObject : public CppPyObject<pkgAcquire*> {
    item_map items;
    worker_map workers;
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
    // FIXME: PyAcquire_FromCpp needs to initialize item_map.
    if (PyAcquire && false && PyAcquire->items[Item].item) {
        Py_INCREF(PyItem);
        PyItem = PyAcquire->items[Item].item;
    }
    else {
        PyItem = PyAcquireItem_FromCpp(Item,false,PyAcquire);
        // FIXME: PyAcquire_FromCpp needs to initialize item_map.
        if (PyAcquire && false)
            PyAcquire->items[Item].item = (CppOwnedPyObject<pkgAcquire::Item*>*)PyItem;
    }

    PyObject *ret = PyAcquireItemDesc_FromCpp(worker->CurrentItem,false,PyItem);
    Py_DECREF(PyItem);
    return ret;
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
   item_map &items = ((PyAcquireObject *)Self)->items;
   for (item_map::iterator I = items.begin(); I != items.end(); I++) {
       if ((*I).second.file)
            (*I).second.file->Object = NULL;
        if ((*I).second.item) {
            (*I).second.item->Object = NULL;
            Py_DECREF((*I).second.item);
        }
        if ((*I).second.desc) {
            (*I).second.desc->Object = NULL;
            Py_DECREF((*I).second.desc);
        }
   }
   items.clear();
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
        Py_DECREF(PyWorker);
    }
    return List;
}
static PyObject *PkgAcquireGetItems(PyObject *Self,void*)
{
   pkgAcquire *fetcher = GetCpp<pkgAcquire*>(Self);
   PyObject *List = PyList_New(0);
   CppOwnedPyObject<pkgAcquire::Item*> *Obj;
   for (pkgAcquire::ItemIterator I = fetcher->ItemsBegin();
        I != fetcher->ItemsEnd(); I++)
   {

      if (((PyAcquireObject *)Self)->items[*I].item)
        PyList_Append(List, ((PyAcquireObject *)Self)->items[*I].item);
      else {
        Obj = CppOwnedPyObject_NEW<pkgAcquire::Item*>(Self,&PyAcquireItem_Type,*I);
        Obj->NoDelete = true;

        PyList_Append(List,Obj);
        ((PyAcquireObject *)Self)->items[*I].item = Obj;


        // Not DECREFING it, we want to manage it somewhere else.
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

   PyFetchProgress *progress = 0;
   if (pyFetchProgressInst != NULL) {
      // FIXME: memleak?
      progress = new PyFetchProgress();
      progress->setCallbackInst(pyFetchProgressInst);
      fetcher = new pkgAcquire(progress);
   } else {
      fetcher = new pkgAcquire();
   }

   PyAcquireObject *FetcherObj = (PyAcquireObject *)
	   CppPyObject_NEW<pkgAcquire*>(type, fetcher);

   if (progress != 0)
      progress->setPyAcquire(FetcherObj);
   // prepare our map of items.
   new (&FetcherObj->items) item_map();
   new (&FetcherObj->workers) worker_map();
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

