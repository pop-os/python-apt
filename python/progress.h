// Description								/*{{{*/
// $Id: progress.h,v 1.5 2003/06/03 03:03:23 mdz Exp $
/* ######################################################################

   Progress - Wrapper for the progress related functions

   ##################################################################### */

#ifndef PROGRESS_H
#define PROGRESS_H

#include <apt-pkg/progress.h>
#include <Python.h>

struct PyOpProgress : public OpProgress
{
   PyObject *callbackInst;

   void setCallbackInst(PyObject *o) {
      callbackInst = o;
   }

   virtual void Update();
   virtual void Done();

   PyOpProgress() : OpProgress(), callbackInst(0) {};
};

#endif
