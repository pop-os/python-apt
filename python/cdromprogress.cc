/* cdromprogress.cc - Base class for CdromProgress classes.
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
#include "progress.h"
#include <Python.h>
#include <structmember.h>

// Takes two arguments (string, int)
static PyObject *cdromprogress_update(PyObject *self, PyObject *args)
{
    Py_RETURN_NONE;
}

// Takes no arguments
static PyObject *cdromprogress_change_cdrom(PyObject *self, PyObject *args)
{
    Py_RETURN_FALSE;
}

// Takes a single PyObject argument as *arg
static PyObject *cdromprogress_ask_cdrom_name(PyObject *self, PyObject *arg)
{
    Py_RETURN_NONE;
}

static PyMethodDef cdromprogress_methods[] = {
    {"update",cdromprogress_update,METH_VARARGS,
     "update(text: str, current: int)\n\nCalled regularly."},
    {"change_cdrom",cdromprogress_change_cdrom,METH_NOARGS,
     "change_cdrom() -> bool\n\nAsk for the CD-ROM to be changed.\n"
     "Return False if the user requested to cancel the action (default)."},
    {"ask_cdrom_name",cdromprogress_ask_cdrom_name,METH_O,
     "ask_cdrom_name() -> str\n\nAsk for the name of the CD-ROM.\n"
     "Return None if the user requested to cancel the action (default)."},
    {NULL}
};

static PyMemberDef cdromprogress_members[] = {
    {"total_steps", T_INT, offsetof(PyCdromProgressObject,total_steps), 0,
     "The number of total steps to be taken."},
    {NULL}
};

static char *cdromprogress_doc = "CdromProgress()\n\n"
    "Base class for reporting the progress of adding a cdrom. Can be used\n"
    "with apt_pkg.Cdrom to produce an utility like apt-cdrom.";

PyTypeObject PyCdromProgress_Type = {
    PyVarObject_HEAD_INIT(&PyType_Type, 0)
    "apt_pkg.CdromProgress",           // tp_name
    sizeof(PyCdromProgressObject),     // tp_basicsize
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
    cdromprogress_doc,                 // tp_doc
    0,                                 // tp_traverse
    0,                                 // tp_clear
    0,                                 // tp_richcompare
    0,                                 // tp_weaklistoffset
    0,                                 // tp_iter
    0,                                 // tp_iternext
    cdromprogress_methods,             // tp_methods
    cdromprogress_members,             // tp_members
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
