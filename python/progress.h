// Description								/*{{{*/
// $Id: progress.h,v 1.5 2003/06/03 03:03:23 mdz Exp $
/* ######################################################################

   Progress - Wrapper for the progress related functions

   ##################################################################### */

#ifndef PROGRESS_H
#define PROGRESS_H

#include <apt-pkg/progress.h>
#include <apt-pkg/acquire.h>
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


struct PyFetchProgress : public pkgAcquireStatus 
{
   PyObject *callbackInst;

   void setCallbackInst(PyObject *o) {
      callbackInst = o;
   }


   void updateStatus(pkgAcquire::ItemDesc & Itm, int status);

   // apt interface
   virtual bool MediaChange(string Media, string Drive);
   virtual void IMSHit(pkgAcquire::ItemDesc &Itm);
   virtual void Fetch(pkgAcquire::ItemDesc &Itm);
   virtual void Done(pkgAcquire::ItemDesc &Itm);
   virtual void Fail(pkgAcquire::ItemDesc &Itm);
   virtual void Start();
   virtual void Stop();

   bool Pulse(pkgAcquire * Owner);
};



#endif
