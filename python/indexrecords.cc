/*
 * indexrecords.cc - Wrapper around indexRecords
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
#include <Python.h>
#include "apt_pkgmodule.h"
#include "generic.h"
#include <apt-pkg/indexrecords.h>

static PyObject *IndexRecords_NEW(PyTypeObject *type,PyObject *Args,
                                  PyObject *kwds)
{
    char * kwlist[] = {NULL};
    if (PyArg_ParseTupleAndKeywords(Args, kwds, "", kwlist) == 0)
        return 0;
    indexRecords *records = new indexRecords();
    CppPyObject<indexRecords*> *New = CppPyObject_NEW<indexRecords*>(type,
                                      records);
    return New;
}

static PyObject *IndexRecords_Load(PyObject *self,PyObject *args)
{
    const char *filename;
    if (PyArg_ParseTuple(args, "s", &filename) == 0)
        return 0;
    indexRecords *records = GetCpp<indexRecords*>(self);
    return HandleErrors(Py_BuildValue("i", records->Load(filename)));
}

static char *IndexRecords_Lookup_doc = "lookup(metakey)\n\n"
    "Lookup the filename given by metakey, return a tuple (hash, size).\n"
    "The hash part is a HashString() object.";
static PyObject *IndexRecords_Lookup(PyObject *self,PyObject *args)
{
    const char *keyname;
    if (PyArg_ParseTuple(args, "s", &keyname) == 0)
        return 0;
    indexRecords *records = GetCpp<indexRecords*>(self);
    const indexRecords::checkSum *result = records->Lookup(keyname);
    if (result == 0) {
        PyErr_SetString(PyExc_KeyError,keyname);
        return 0;
    }
    // Copy the HashString(), to prevent crashes and to not require the
    // indexRecords object to exist.
    PyObject *py_hash = PyHashString_FromCpp(new HashString(result->Hash));
    PyObject *value = Py_BuildValue("(Oi)",py_hash,result->Size);
    Py_DECREF(py_hash);
    return value;
}

static PyObject *IndexRecords_GetDist(PyObject *self)
{
    indexRecords *records = GetCpp<indexRecords*>(self);
    return HandleErrors(PyString_FromString(records->GetDist().c_str()));
}

static PyMethodDef IndexRecords_Methods[] = {
    {"load",IndexRecords_Load,METH_VARARGS,
     "load(filename: str)\n\nLoad the file given by filename."},
    {"get_dist",(PyCFunction)IndexRecords_GetDist,METH_NOARGS,
     "get_dist() -> str\n\nReturn a distribution set in the release file."},
    {"lookup",IndexRecords_Lookup,METH_VARARGS,IndexRecords_Lookup_doc},
    {}
};

static char *IndexRecords_doc = "IndexRecords()\n\n"
    "Representation of a release file.";
PyTypeObject PyIndexRecords_Type = {
    PyVarObject_HEAD_INIT(&PyType_Type, 0)
    "apt_pkg.IndexRecords",              // tp_name
    sizeof(CppPyObject<indexRecords*>),  // tp_basicsize
    0,                                   // tp_itemsize
    // Methods
    CppDeallocPtr<indexRecords*>,        // tp_dealloc
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
    IndexRecords_doc,                    // tp_doc
    0,                                   // tp_traverse
    0,                                   // tp_clear
    0,                                   // tp_richcompare
    0,                                   // tp_weaklistoffset
    0,                                   // tp_iter
    0,                                   // tp_iternext
    IndexRecords_Methods,                // tp_methods
    0,                                   // tp_members
    0,                                   // tp_getset
    0,                                   // tp_base
    0,                                   // tp_dict
    0,                                   // tp_descr_get
    0,                                   // tp_descr_set
    0,                                   // tp_dictoffset
    0,                                   // tp_init
    0,                                   // tp_alloc
    IndexRecords_NEW,                    // tp_new
};
