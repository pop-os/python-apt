// -*- mode: cpp; mode: fold -*-
// Description								/*{{{*/
// $Id: apt_instmodule.cc,v 1.3 2002/01/08 06:53:04 jgg Exp $
/* ######################################################################

   apt_intmodule - Top level for the python module. Create the internal
                   structures for the module in the interpriter.
      
   Note, this module shares state (particularly global config) with the
   apt_pkg module.
   
   ##################################################################### */
									/*}}}*/
// Include Files							/*{{{*/
#include "apt_instmodule.h"
#include "generic.h"

#include <apt-pkg/debfile.h>
#include <apt-pkg/error.h>
    
#include <sys/stat.h>
#include <unistd.h>
#include <Python.h>
									/*}}}*/

// debExtractControl - Exctract an arbitary control member		/*{{{*/
// ---------------------------------------------------------------------
/* This is a common operation so this function will stay, but others that
   expose the full range of the apt-inst .deb processing will join it some
   day. */
static char *doc_debExtractControl =
"debExtractControl(File[,Member]) -> String\n"
"Returns the indicated file from the control tar. The default is 'control'\n";
static PyObject *debExtractControl(PyObject *Self,PyObject *Args)
{
   char *Member = "control";
   PyObject *File;
   if (PyArg_ParseTuple(Args,"O!|s",&PyFile_Type,&File,&Member) == 0)
      return 0;
   
   // Subscope makes sure any clean up errors are properly handled.
   PyObject *Res = 0;
   {
      // Open the file and associate the .deb
      FileFd Fd(fileno(PyFile_AsFile(File)),false);
      debDebFile Deb(Fd);
      if (_error->PendingError() == true)
	 return HandleErrors();
      
      debDebFile::MemControlExtract Extract(Member);
      if (Extract.Read(Deb) == false)
	 return HandleErrors();
      
      // Build the return result
      
      if (Extract.Control == 0)
      {
	 Py_INCREF(Py_None);
	 Res = Py_None;
      }
      else
	 Res = PyString_FromStringAndSize(Extract.Control,Extract.Length+2);
   }
   
   return HandleErrors(Res);
}
									/*}}}*/

// initapt_inst - Core Module Initialization				/*{{{*/
// ---------------------------------------------------------------------
/* */
static PyMethodDef methods[] =
{
   // Stuff
   {"debExtractControl",debExtractControl,METH_VARARGS,doc_debExtractControl},
   {"tarExtract",tarExtract,METH_VARARGS,doc_tarExtract},
   {"debExtract",debExtract,METH_VARARGS,doc_debExtract},

   {}
};

extern "C" void initapt_inst()
{
   Py_InitModule("apt_inst",methods);
}
									/*}}}*/
