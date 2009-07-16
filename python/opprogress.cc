/* op-progress.cc - Base class for OpProgress classes.
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

#include "generic.h"
#include <Python.h>
#include <structmember.h>

typedef struct {
    PyObject_HEAD
    PyObject *op;
    PyObject *subop;
    int major_change;
    float percent;
} PyOpProgressObject;

static PyObject *opprogress_update(PyObject *Self, PyObject *args)
{
    Py_RETURN_NONE;
}

static PyObject *opprogress_done(PyObject *Self, PyObject *args)
{
    Py_RETURN_NONE;
}

static PyObject *opprogress_get_op(PyOpProgressObject *self, void *closure)
{
    Py_INCREF(self->op);
    return self->op;
}

static int opprogress_set_op(PyOpProgressObject *self, PyObject *value,
                             void *closure)
{
    if (value == NULL) {
        PyErr_SetString(PyExc_TypeError, "Cannot delete 'op'");
        return -1;
    }
    if (!PyString_Check(value)) {
        PyErr_SetString(PyExc_TypeError,"'op' must be a string.");
        return -1;
    }
    Py_DECREF(self->op);
    Py_INCREF(value);

    self->op = value;
    return 0;
}

static PyObject *opprogress_get_subop(PyOpProgressObject *self, void *closure)
{
    Py_INCREF(self->subop);
    return self->subop;
}

static int opprogress_set_subop(PyOpProgressObject *self, PyObject *value,
                                void *closure)
{
    if (value == NULL) {
        PyErr_SetString(PyExc_TypeError, "Cannot delete 'subop'.");
        return -1;
    }
    if (!PyString_Check(value)) {
        PyErr_SetString(PyExc_TypeError,"'subop' must be a string.");
        return -1;
    }
    Py_DECREF(self->subop);
    Py_INCREF(value);
    self->subop = value;
    return 0;
}

static PyMethodDef opprogress_methods[] = {
    {"update",opprogress_update,METH_NOARGS,"update()\n\nCalled periodically."},
    {"done",opprogress_done,METH_NOARGS,"update()\n\nCalled when done."},
    {NULL},
};

static PyMemberDef opprogress_members[] = {
    {"major_change", T_INT, offsetof(PyOpProgressObject, major_change), 0,
     "Boolean value indicating whether the change is a major change."},
    {"percent", T_FLOAT, offsetof(PyOpProgressObject, percent), 0,
     "Percentage of completion (float value)."},
    {NULL}
};

static PyGetSetDef opprogress_getset[] = {
    {"op", (getter)opprogress_get_op, (setter)opprogress_set_op,
     "Description of the current operation"},
    {"subop", (getter)opprogress_get_subop, (setter)opprogress_set_subop,
     "Description of the current sub-operation"},
    {NULL},
};

static void opprogress_dealloc(PyObject *self)
{
    Py_XDECREF(((PyOpProgressObject *)self)->op);
    Py_XDECREF(((PyOpProgressObject *)self)->subop);
    self->ob_type->tp_free(self);
}

static PyObject *opprogress_new(PyTypeObject *type, PyObject *args,
                                PyObject *kwds)
{
    PyOpProgressObject *res = (PyOpProgressObject *)type->tp_alloc(type, 0);
    res->op = PyString_FromString("");
    res->subop = PyString_FromString("");
    return (PyObject *)res;
}

static char *opprogress_doc = "OpProgress()\n\n"
    "A base class for writing custom operation progress classes. Subclasses\n"
    "should override all the methods (and call the parent ones) but shall\n"
    "not override any of the inherited descriptors because they may be\n"
    "ignored.";

PyTypeObject PyOpProgress_Type = {
    PyVarObject_HEAD_INIT(&PyType_Type, 0)
    "apt_pkg.OpProgress",              // tp_name
    sizeof(PyOpProgressObject),        // tp_basicsize
    0,                                 // tp_itemsize
    // Methods
    opprogress_dealloc,                // tp_dealloc
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
    opprogress_doc,                    // tp_doc
    0,                                 // tp_traverse
    0,                                 // tp_clear
    0,                                 // tp_richcompare
    0,                                 // tp_weaklistoffset
    0,                                 // tp_iter
    0,                                 // tp_iternext
    opprogress_methods,                // tp_methods
    opprogress_members,                // tp_members
    opprogress_getset,                 // tp_getset
    0,                                 // tp_base
    0,                                 // tp_dict
    0,                                 // tp_descr_get
    0,                                 // tp_descr_set
    0,                                 // tp_dictoffset
    0,                                 // tp_init
    0,                                 // tp_alloc
    opprogress_new,                    // tp_new
};
