/*
 * client-example.cc - A simple example for using the python-apt C++ API.
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
#include <python-apt/python-apt.h>

int main(int argc, char *argv[]) {
    Py_Initialize();
    if (import_apt_pkg() < 0)
        return 1;

    // Initialize a module.
    PyObject *Module = Py_InitModule("client", NULL);

    // Create a HashString, which will be added to the module.
    HashString *hash = new HashString("0966a120bb936bdc6fdeac445707aa6b");
    // Create a Python object for the hashstring and add it to the module
    PyModule_AddObject(Module, "hash", PyHashString_FromCpp(hash));

    // Another example: Add the HashString type to the module.
    Py_INCREF(&PyHashString_Type);
    PyModule_AddObject(Module, "HashString", (PyObject*)(&PyHashString_Type));

    // Run IPython, adding the client module to the namespace.
    PySys_SetArgv(argc, argv);
    PyRun_SimpleString("from IPython.Shell import start\n");
    PyRun_SimpleString("import client\n");
    PyRun_SimpleString("start(user_ns=dict(client=client)).mainloop()\n");
    Py_Finalize();
}
