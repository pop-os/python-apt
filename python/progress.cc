// Description								/*{{{*/
// $Id: progress.cc,v 1.5 2003/06/03 03:03:23 mdz Exp $
/* ######################################################################

   Progress - Wrapper for the progress related functions

   ##################################################################### */

#include <iostream>
#include "progress.h"


// OpProgress interface 
// FIXME: add "string Op, string SubOp" as attribute to the callbackInst
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



// fetcher interface
// PyFetchProgress:: 

// apt interface
bool PyFetchProgress::MediaChange(string Media, string Drive)
{
   std::cout << "MediaChange" << std::endl;
}

void PyFetchProgress::IMSHit(pkgAcquire::ItemDesc &Itm)
{
   std::cout << "IMSHit" << std::endl;
}

void PyFetchProgress::Fetch(pkgAcquire::ItemDesc &Itm)
{
   std::cout << "Fetch" << std::endl;
}

void PyFetchProgress::Done(pkgAcquire::ItemDesc &Itm)
{
   std::cout << "Done" << std::endl;
}

void PyFetchProgress::Fail(pkgAcquire::ItemDesc &Itm)
{
   std::cout << "Fail" << std::endl;
}

void PyFetchProgress::Start()
{
   std::cout << "Start" << std::endl;
   pkgAcquireStatus::Start();

}

void PyFetchProgress::Stop()
{
   std::cout << "Stop" << std::endl;
   pkgAcquireStatus::Stop();
}

// FIXME: it should just set the attribute for
//         CurrentCPS, Current...
bool PyFetchProgress::Pulse(pkgAcquire * Owner)
{
   pkgAcquireStatus::Pulse(Owner);

   //std::cout << "Pulse" << std::endl;
   if(callbackInst == 0)
      return false;
   
   // set stats
   PyObject *o;
   o = Py_BuildValue("f", CurrentCPS);
   PyObject_SetAttrString(callbackInst, "CurrentCPS", o);
   o = Py_BuildValue("f", CurrentBytes);
   PyObject_SetAttrString(callbackInst, "CurrentBytes", o);
   o = Py_BuildValue("i", CurrentItems);
   PyObject_SetAttrString(callbackInst, "CurrentItems", o);
   o = Py_BuildValue("i", TotalItems);
   PyObject_SetAttrString(callbackInst, "TotalItems", o);
   o = Py_BuildValue("f", TotalBytes);
   PyObject_SetAttrString(callbackInst, "TotalBytes", o);
   
   // Call the pulse method
   PyObject *arglist = Py_BuildValue("()");
   PyObject *method = PyObject_GetAttrString(callbackInst, "Pulse");
   if(method == NULL) {
      // FIXME: make this silent
      std::cerr << "Can't find 'Pulse' method" << std::endl;
      Py_DECREF(arglist);
      return false;
   }
   PyObject *result = PyEval_CallObject(method,arglist);
   // FIXME: throw some exception here if the method was unsuccessfull

   Py_XDECREF(result);
   Py_XDECREF(method);
   Py_DECREF(arglist);
   
   // this can be canceld by returning false
   return true;
}
