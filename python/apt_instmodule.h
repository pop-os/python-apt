// -*- mode: cpp; mode: fold -*-
// Description								/*{{{*/
// $Id: apt_instmodule.h,v 1.1 2001/09/30 03:52:58 jgg Exp $
/* ######################################################################

   Prototypes for the module
   
   ##################################################################### */
									/*}}}*/
#ifndef APT_INSTMODULE_H
#define APT_INSTMODULE_H

#include <python/Python.h>

PyObject *debExtract(PyObject *Self,PyObject *Args);
extern char *doc_debExtract;
PyObject *tarExtract(PyObject *Self,PyObject *Args);
extern char *doc_tarExtract;

#endif
