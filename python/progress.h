#ifndef PROGRESS_H
#define PROGRESS_H

#include<iostream>

struct PyOpProgressStruct : public OpProgress
{

   PyObject *py_update_callback_func;
   PyObject *py_update_callback_args;

   virtual void Update() {
      if(py_update_callback_func == 0)
	 return;

      // Build up the argument list... 
      PyObject *arglist = Py_BuildValue("fO", Percent,py_update_callback_args);

      // ...for calling the Python compare function.
      PyObject *result = PyEval_CallObject(py_update_callback_func,arglist);

      Py_XDECREF(result);
      Py_DECREF(arglist);

      return;
   };

   PyOpProgressStruct() : OpProgress(), py_update_callback_func(0) {};
};

#endif
