// Description								/*{{{*/
// $Id: progress.cc,v 1.5 2003/06/03 03:03:23 mdz Exp $
/* ######################################################################

   Progress - Wrapper for the progress related functions

   ##################################################################### */

#include "progress.h"


void PyOpProgress::Update() 
{
   if(callbackInst == 0)
      return;
   
   // Build up the argument list... 
   PyObject *arglist = Py_BuildValue("(f)", Percent);
   
   // ...for calling the Python compare function.
   PyObject *method = PyObject_GetAttrString(callbackInst, "Update");
   if(method == NULL) {
      // FIXME: make this silent
      Py_DECREF(arglist);
      return;
   }
   PyObject *result = PyEval_CallObject(method,arglist);
   
   Py_XDECREF(result);
   Py_XDECREF(method);
   Py_DECREF(arglist);
   
   return;
};

void PyOpProgress::Done()
{
   if(callbackInst == 0)
      return;
   
   // Build up the argument list... 
   PyObject *arglist = Py_BuildValue("()", NULL);
   
   // ...for calling the Python compare function.
   PyObject *method = PyObject_GetAttrString(callbackInst, "Done");
   if(method == NULL) {
      Py_DECREF(arglist);
      return;
   }
   PyObject *result = PyEval_CallObject(method,arglist);
   
   Py_XDECREF(result);
   Py_XDECREF(method);
   Py_DECREF(arglist);
}
