/*
 * arfile.cc - Wrapper around ARArchive and ARArchive::Member.
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
#include "generic.h"
#include <apt-pkg/arfile.h>
#include <apt-pkg/error.h>

PyObject *armember_get_name(PyObject *self, void *closure)
{
    return CppPyString(GetCpp<ARArchive::Member*>(self)->Name);
}

PyObject *armember_get_mtime(PyObject *self, void *closure)
{
    return Py_BuildValue("k", GetCpp<ARArchive::Member*>(self)->MTime);
}

PyObject *armember_get_uid(PyObject *self, void *closure)
{
    return Py_BuildValue("k", GetCpp<ARArchive::Member*>(self)->UID);
}

PyObject *armember_get_gid(PyObject *self, void *closure)
{
    return Py_BuildValue("k", GetCpp<ARArchive::Member*>(self)->GID);
}

PyObject *armember_get_mode(PyObject *self, void *closure)
{
    return Py_BuildValue("k", GetCpp<ARArchive::Member*>(self)->Mode);
}

PyObject *armember_get_size(PyObject *self, void *closure)
{
    return Py_BuildValue("k", GetCpp<ARArchive::Member*>(self)->Size);
}

PyObject *armember_get_start(PyObject *self, void *closure)
{
    return Py_BuildValue("k", GetCpp<ARArchive::Member*>(self)->Start);
}

PyGetSetDef armember_getset[] = {
    {"gid",armember_get_gid,0,"The group id of the owner."},
    {"mode",armember_get_mode,0,"The mode of the file."},
    {"mtime",armember_get_mtime,0,"Last time of modification."},
    {"name",armember_get_name,0,"The name of the file."},
    {"size",armember_get_size,0,"The size of the files."},
    {"start",armember_get_start,0,
     "The offset in the archive where the file starts."},
    {"uid",armember_get_uid,0,"The user id of the owner."},
    {NULL}
};

static const char *armember_doc =
    "An ArMember object represents a single file within an AR archive. For\n"
    "Debian packages this can be e.g. control.tar.gz. This class provides\n"
    "information about this file, such as the mode and size.";
PyTypeObject PyArMember_Type = {
    PyVarObject_HEAD_INIT(&PyType_Type, 0)
    "apt_inst.ArMember",                 // tp_name
    sizeof(CppOwnedPyObject<ARArchive::Member*>),  // tp_basicsize
    0,                                   // tp_itemsize
    // Methods
    CppOwnedDeallocPtr<ARArchive::Member*>, // tp_dealloc
    0,                                   // tp_print
    0,                                   // tp_getattr
    0,                                   // tp_setattr
    0,                                   // tp_compare
    0,                                   // tp_repr
    0,                                   // tp_as_number
    0,                                   // tp_as_sequence
    0,                                  // tp_as_mapping
    0,                                   // tp_hash
    0,                                   // tp_call
    0,                                   // tp_str
    0,                                   // tp_getattro
    0,                                   // tp_setattro
    0,                                   // tp_as_buffer
    Py_TPFLAGS_DEFAULT |                 // tp_flags
    Py_TPFLAGS_HAVE_GC,
    armember_doc,                        // tp_doc
    CppOwnedTraverse<ARArchive::Member*>,// tp_traverse
    CppOwnedClear<ARArchive::Member*>,   // tp_clear
    0,                                   // tp_richcompare
    0,                                   // tp_weaklistoffset
    0,                                   // tp_iter
    0,                                   // tp_iternext
    0,                                   // tp_methods
    0,                                   // tp_members
    armember_getset,                     // tp_getset
};

struct PyArArchiveObject : public CppOwnedPyObject<ARArchive*> {
    FileFd Fd;
};

static const char *ararchive_getmember_doc =
     "getmember(name: str) -> ArMember\n\n"
     "Return a ArMember object for the member given by name. Raise\n"
     "LookupError if there is no ArMember with the given name.";
PyObject *ararchive_getmember(PyArArchiveObject *self, PyObject *arg)
{
    const char *name;
    CppOwnedPyObject<ARArchive::Member*> *ret;
    if (! (name = PyObject_AsString(arg)))
        return 0;

    const ARArchive::Member *member = self->Object->FindMember(name);
    if (!member) {
        PyErr_Format(PyExc_LookupError,"No member named '%s'",name);
        return 0;
    }

    // Create our object.
    ret = CppOwnedPyObject_NEW<ARArchive::Member*>(self,&PyArMember_Type);
    ret->Object = const_cast<ARArchive::Member*>(member);
    ret->NoDelete = true;
    return ret;
}

static const char *ararchive_getdata_doc =
    "getdata(name: str) -> bytes\n\n"
     "Return the contents of the member, as a bytes object. Raise\n"
     "LookupError if there is no ArMember with the given name.";
PyObject *ararchive_getdata(PyArArchiveObject *self, PyObject *args)
{
    char *name = 0;
    if (PyArg_ParseTuple(args, "s:getdata", &name) == 0)
        return 0;
    const ARArchive::Member *member = self->Object->FindMember(name);
    if (!member) {
        PyErr_Format(PyExc_LookupError,"No member named '%s'",name);
        return 0;
    }
    if (!self->Fd.Seek(member->Start))
        return HandleErrors();

    char* value = new char[member->Size];
    self->Fd.Read(value, member->Size, true);
    PyObject *result = PyBytes_FromStringAndSize(value, member->Size);
    delete[] value;
    return result;
}

static const char *ararchive_extract_doc =
    "extract(name: str[, target: str]) -> bool\n\n"
     "Extract the member given by name into the directory given by target.\n"
     "If the extraction failed, an error is raised. Otherwise, the method\n"
     "returns True if the owner could be set or False if the owner could not\n"
     "be changed. It may also raise LookupError if there is member with\n"
     "the given name.";
PyObject *ararchive_extract(PyArArchiveObject *self, PyObject *args)
{
    char *name = 0;
    char *target = "";
    if (PyArg_ParseTuple(args, "s|s:extract", &name, &target) == 0)
        return 0;

    const ARArchive::Member *member = self->Object->FindMember(name);

    if (!member) {
        PyErr_Format(PyExc_LookupError,"No member named '%s'",name);
        return 0;
    }

    if (!self->Fd.Seek(member->Start))
        return HandleErrors();

    // Open the target file
    FileFd outfd(flCombine(target,name), FileFd::WriteAny, member->Mode);
    if (_error->PendingError() == true)
        return HandleErrors();

    // Temporary buffer. We should probably split this into smaller parts.
    char* value = new char[member->Size];

    // Read into the buffer
    if (!self->Fd.Read(value, member->Size, true)) {
        delete[] value;
        return HandleErrors();
    }
    if (!outfd.Write(value, member->Size)) {
        delete[] value;
        return HandleErrors();
    }
    if (fchown(outfd.Fd(), member->UID, member->GID) == -1) {
        delete[] value;
        Py_RETURN_FALSE;
    }
    Py_RETURN_TRUE;
}

PyMethodDef ararchive_methods[] = {
    {"getmember",(PyCFunction)ararchive_getmember,METH_O,
     ararchive_getmember_doc},
    {"getdata",(PyCFunction)ararchive_getdata,METH_VARARGS,
     ararchive_getdata_doc},
    {"extract",(PyCFunction)ararchive_extract,METH_VARARGS,
     ararchive_extract_doc},
    {NULL}
};

PyObject *ararchive_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    PyObject *file;
    PyArArchiveObject *self;
    char *filename = 0;
    int fileno;
    if (PyArg_ParseTuple(args,"O:__new__",&file) == 0)
        return 0;

    // We receive a filename.
    if ((filename = (char*)PyObject_AsString(file))) {
        self = (PyArArchiveObject *)CppOwnedPyObject_NEW<ARArchive*>(0,type);
        new (&self->Fd) FileFd(filename,FileFd::ReadOnly);
    }
    // We receive a file object.
    else if ((fileno = PyObject_AsFileDescriptor(file)) != -1) {
        // Clear the error set by PyObject_AsString().
        PyErr_Clear();
        self = (PyArArchiveObject *)CppOwnedPyObject_NEW<ARArchive*>(file,type);
        new (&self->Fd) FileFd(fileno,false);
    }
    else {
        return 0;
    }
    self->Object = new ARArchive(self->Fd);
    if (_error->PendingError() == true)
        return HandleErrors();
    return self;
}

static void ararchive_dealloc(PyObject *self) {
    ((PyArArchiveObject *)(self))->Fd.~FileFd();
    CppOwnedDeallocPtr<ARArchive*>(self);
}

// Return bool or -1 (exception).
static int ararchive_contains(PyObject *self, PyObject *arg)
{
    const char *name = PyObject_AsString(arg);
    if (!name)
        return -1;
    return (GetCpp<ARArchive*>(self)->FindMember(name) != 0);
}

static PySequenceMethods ararchive_as_sequence =
    {0,0,0,0,0,0,0,ararchive_contains,0,0};

static PyMappingMethods ararchive_as_mapping =
    {0,(PyCFunction)ararchive_getmember,0};

static const char *ararchive_doc =
    "ArArchive(file: str/int/file)\n\n"
    "An ArArchive object represents an archive in the 4.4 BSD AR format, \n"
    "which is used for e.g. deb packages.\n\n"
    "The parameter 'file' may be a string specifying the path of a file, or\n"
    "a file-like object providing the fileno() method. It may also be an int\n"
    "specifying a file descriptor (returned by e.g. os.open()).\n"
    "The recommended way is to pass in the path to the file.";

PyTypeObject PyArArchive_Type = {
    PyVarObject_HEAD_INIT(&PyType_Type, 0)
    "apt_inst.ArArchive",                // tp_name
    sizeof(PyArArchiveObject),           // tp_basicsize
    0,                                   // tp_itemsize
    // Methods
    ararchive_dealloc,                   // tp_dealloc
    0,                                   // tp_print
    0,                                   // tp_getattr
    0,                                   // tp_setattr
    0,                                   // tp_compare
    0,                                   // tp_repr
    0,                                   // tp_as_number
    &ararchive_as_sequence,              // tp_as_sequence
    &ararchive_as_mapping,               // tp_as_mapping
    0,                                   // tp_hash
    0,                                   // tp_call
    0,                                   // tp_str
    0,                                   // tp_getattro
    0,                                   // tp_setattro
    0,                                   // tp_as_buffer
    Py_TPFLAGS_DEFAULT |                 // tp_flags
    Py_TPFLAGS_HAVE_GC,
    ararchive_doc,                       // tp_doc
    CppOwnedTraverse<ARArchive*>,        // tp_traverse
    CppOwnedClear<ARArchive*>,           // tp_clear
    0,                                   // tp_richcompare
    0,                                   // tp_weaklistoffset
    0,                                   // tp_iter
    0,                                   // tp_iternext
    ararchive_methods,                   // tp_methods
    0,                                   // tp_members
    0,                                   // tp_getset
    0,                                   // tp_base
    0,                                   // tp_dict
    0,                                   // tp_descr_get
    0,                                   // tp_descr_set
    0,                                   // tp_dictoffset
    0,                                   // tp_init
    0,                                   // tp_alloc
    ararchive_new                        // tp_new
};
