/* acquireprogress.cc - Base class for FetchProgress classes.
 *
 * Copyright 2009 Julian Andres Klode <jak@debian.org>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
 * MA 02110-1301, USA.
 */

#include "apt_pkgmodule.h"
#include <Python.h>
#include <structmember.h>

typedef struct {
    PyObject_HEAD
    double last_bytes;
    double current_cps;
    double current_bytes;
    double total_bytes;
    double fetched_bytes;
    unsigned long elapsed_time;
    unsigned long total_items;
    unsigned long current_items;
} PyAcquireProgressObject;


// DUMMY IMPLEMENTATIONS.
static char *acquireprogress_media_change_doc =
    "media_change(media: str, drive: str) -> bool\n\n"
    "Invoked when the user should be prompted to change the inserted\n"
    "removable media.\n\n"
    "This method should not return until the user has confirmed to the user\n"
    "interface that the media change is complete.\n\n"
    ":param:media The name of the media type that should be changed.\n"
    ":param:drive The identifying name of the drive whose media should be\n"
    "             changed.\n\n"
    "Return True if the user confirms the media change, False if it is\n"
    "cancelled.";
static PyObject *acquireprogress_media_change(PyObject *self, PyObject *args)
{
    Py_RETURN_FALSE;
}

static char *acquireprogress_ims_hit_doc = "ims_hit(item: AcquireItemDesc)\n\n"
    "Invoked when an item is confirmed to be up-to-date. For instance,\n"
    "when an HTTP download is informed that the file on the server was\n"
    "not modified.";
static PyObject *acquireprogress_ims_hit(PyObject *self, PyObject *arg)
{
    if (!PyAcquireItemDesc_Check(arg)) {
        PyErr_SetString(PyExc_TypeError, "ims_hit() argument must be "
                                         "apt_pkg.AcquireItemDesc");
        return 0;
    }
    Py_RETURN_NONE;
}

static char *acquireprogress_fetch_doc = "fetch(item: AcquireItemDesc)\n\n"
    "Invoked when some of an item's data is fetched.";
static PyObject *acquireprogress_fetch(PyObject *self, PyObject *arg)
{
    if (!PyAcquireItemDesc_Check(arg)) {
        PyErr_SetString(PyExc_TypeError, "fetch() argument must be "
                                         "apt_pkg.AcquireItemDesc");
        return 0;
    }
    Py_RETURN_NONE;
}

static char *acquireprogress_done_doc = "done(item: AcquireItemDesc)\n\n"
    "Invoked when an item is successfully and completely fetched.";
static PyObject *acquireprogress_done(PyObject *self, PyObject *arg)
{
    if (!PyAcquireItemDesc_Check(arg)) {
        PyErr_SetString(PyExc_TypeError, "done() argument must be "
                                         "apt_pkg.AcquireItemDesc");
        return 0;
    }
    Py_RETURN_NONE;
}

static char *acquireprogress_fail_doc = "fail(item: AcquireItemDesc)\n\n"
    "Invoked when the process of fetching an item encounters a fatal error.";
static PyObject *acquireprogress_fail(PyObject *self, PyObject *arg)
{
    if (!PyAcquireItemDesc_Check(arg)) {
        PyErr_SetString(PyExc_TypeError, "fail() argument must be "
                                         "apt_pkg.AcquireItemDesc");
        return 0;
    }
    Py_RETURN_NONE;
}

static char *acquireprogress_pulse_doc = "pulse(owner: Acquire) -> bool\n\n"
    "Periodically invoked while the Acquire process is underway.\n\n"
    "Return False if the user asked to cancel the whole Acquire process.";
static PyObject *acquireprogress_pulse(PyObject *self, PyObject *arg)
{
    if (!PyAcquire_Check(arg)) {
        PyErr_SetString(PyExc_TypeError, "pulse() argument must be "
                                         "apt_pkg.Acquire");
        return 0;
    }
    Py_RETURN_TRUE;
}

static char *acquireprogress_start_doc = "start()\n\n"
    "Invoked when the Acquire process starts running.";
static PyObject *acquireprogress_start(PyObject *self, PyObject *args)
{
    Py_RETURN_NONE;
}

static char *acquireprogress_stop_doc = "stop()\n\n"
    "Invoked when the Acquire process stops running.";
static PyObject *acquireprogress_stop(PyObject *self, PyObject *args)
{
    Py_RETURN_NONE;
}

static PyMethodDef acquireprogress_methods[] = {
    {"media_change", acquireprogress_media_change, METH_VARARGS,
     acquireprogress_media_change_doc},
    {"ims_hit",acquireprogress_ims_hit,METH_O,
     acquireprogress_ims_hit_doc},
    {"fetch",acquireprogress_fetch,METH_O,acquireprogress_fetch_doc},
    {"done",acquireprogress_done,METH_O,acquireprogress_done_doc},
    {"fail",acquireprogress_fail,METH_O,acquireprogress_fail_doc},
    {"pulse",acquireprogress_pulse,METH_O,acquireprogress_pulse_doc},
    {"start",acquireprogress_start,METH_NOARGS,acquireprogress_start_doc},
    {"stop",acquireprogress_stop,METH_NOARGS,acquireprogress_stop_doc},
    {NULL}
};

static PyMemberDef acquireprogress_members[] = {
    {"last_bytes", T_DOUBLE, offsetof(PyAcquireProgressObject, last_bytes), 0,
     "The number of bytes fetched as of the previous call to pulse(),\n"
     "including local items."},
    {"current_cps", T_DOUBLE, offsetof(PyAcquireProgressObject, current_cps), 0,
     "The current rate of download, in bytes per second."},
    {"current_bytes", T_DOUBLE, offsetof(PyAcquireProgressObject, current_bytes),
     0, "The number of bytes fetched."},
    {"total_bytes", T_DOUBLE, offsetof(PyAcquireProgressObject, total_bytes), 0,
     "The total number of bytes that need to be fetched. This member is\n"
     "inaccurate, as new items might be enqueued while the download is\n"
     "in progress!"},
    {"fetched_bytes", T_DOUBLE,offsetof(PyAcquireProgressObject, fetched_bytes),
     0, "The total number of bytes accounted for by items that were\n"
     "successfully fetched."},
    {"elapsed_time", T_ULONG, offsetof(PyAcquireProgressObject, elapsed_time),0,
     "The amount of time that has elapsed since the download started."},
    {"total_items", T_ULONG, offsetof(PyAcquireProgressObject, total_items),0,
     "The total number of items that need to be fetched. This member is\n"
     "inaccurate, as new items might be enqueued while the download is\n"
     "in progress!"},
    {"current_items", T_ULONG, offsetof(PyAcquireProgressObject, current_items),
     0, "The number of items that have been successfully downloaded."},
    {NULL}
};

static char *acquireprogress_doc = "AcquireProgress()\n\n"
    "A monitor object for downloads controlled by the Acquire class. This is\n"
    "an mostly abstract class. You should subclass it and implement the\n"
    "methods to get something useful.";

PyTypeObject PyAcquireProgress_Type = {
    PyVarObject_HEAD_INIT(&PyType_Type, 0)
    "apt_pkg.AcquireProgress",         // tp_name
    sizeof(PyAcquireProgressObject),   // tp_basicsize
    0,                                 // tp_itemsize
    // Methods
    0,                                 // tp_dealloc
    0,                                 // tp_print
    0,                                 // tp_getattr
    0,                                 // tp_setattr
    0,                                 // tp_compare
    0,                                 // tp_repr
    0,                                 // tp_as_number
    0,                                 // tp_as_sequence
    0,                                 // tp_as_mapping
    0,                                 // tp_hash
    0,                                 // tp_call
    0,                                 // tp_str
    0,                                 // tp_getattro
    0,                                 // tp_setattro
    0,                                 // tp_as_buffer
    Py_TPFLAGS_DEFAULT |               // tp_flags
    Py_TPFLAGS_BASETYPE,
    acquireprogress_doc,                 // tp_doc
    0,                                 // tp_traverse
    0,                                 // tp_clear
    0,                                 // tp_richcompare
    0,                                 // tp_weaklistoffset
    0,                                 // tp_iter
    0,                                 // tp_iternext
    acquireprogress_methods,             // tp_methods
    acquireprogress_members,             // tp_members
    0,                                 // tp_getset
    0,                                 // tp_base
    0,                                 // tp_dict
    0,                                 // tp_descr_get
    0,                                 // tp_descr_set
    0,                                 // tp_dictoffset
    0,                                 // tp_init
    0,                                 // tp_alloc
    PyType_GenericNew,                 // tp_new
};
