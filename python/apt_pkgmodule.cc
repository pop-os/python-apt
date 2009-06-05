// -*- mode: cpp; mode: fold -*-
// Description								/*{{{*/
// $Id: apt_pkgmodule.cc,v 1.5 2003/07/23 02:20:24 mdz Exp $
/* ######################################################################

   apt_pkgmodule - Top level for the python module. Create the internal
                   structures for the module in the interpriter.

   ##################################################################### */
									/*}}}*/
// Include Files							/*{{{*/
#include "apt_pkgmodule.h"
#include "generic.h"

#include <apt-pkg/configuration.h>
#include <apt-pkg/version.h>
#include <apt-pkg/deblistparser.h>
#include <apt-pkg/pkgcache.h>
#include <apt-pkg/tagfile.h>
#include <apt-pkg/md5.h>
#include <apt-pkg/sha1.h>
#include <apt-pkg/sha256.h>
#include <apt-pkg/init.h>
#include <apt-pkg/pkgsystem.h>

#include <sys/stat.h>
#include <unistd.h>
#include <Python.h>
									/*}}}*/

// newConfiguration - Build a new configuration class			/*{{{*/
// ---------------------------------------------------------------------
#ifdef COMPAT_0_7
static char *doc_newConfiguration = "Construct a configuration instance";
static PyObject *newConfiguration(PyObject *self,PyObject *args)
{
   return CppPyObject_NEW<Configuration>(&ConfigurationType);
}
#endif
									/*}}}*/

// Version Wrappers							/*{{{*/
// These are kind of legacy..
static char *doc_VersionCompare = "VersionCompare(a,b) -> int";
static PyObject *VersionCompare(PyObject *Self,PyObject *Args)
{
   char *A;
   char *B;
   int LenA;
   int LenB;

   if (PyArg_ParseTuple(Args,"s#s#",&A,&LenA,&B,&LenB) == 0)
      return 0;

   if (_system == 0)
   {
      PyErr_SetString(PyExc_ValueError,"_system not initialized");
      return 0;
   }

   return Py_BuildValue("i",_system->VS->DoCmpVersion(A,A+LenA,B,B+LenB));
}

static char *doc_CheckDep = "CheckDep(PkgVer,DepOp,DepVer) -> int";
static PyObject *CheckDep(PyObject *Self,PyObject *Args)
{
   char *A;
   char *B;
   char *OpStr;
   unsigned int Op = 0;

   if (PyArg_ParseTuple(Args,"sss",&A,&OpStr,&B) == 0)
      return 0;
   if (*debListParser::ConvertRelation(OpStr,Op) != 0)
   {
      PyErr_SetString(PyExc_ValueError,"Bad comparision operation");
      return 0;
   }

   if (_system == 0)
   {
      PyErr_SetString(PyExc_ValueError,"_system not initialized");
      return 0;
   }

   return Py_BuildValue("i",_system->VS->CheckDep(A,Op,B));
//   return Py_BuildValue("i",pkgCheckDep(B,A,Op));
}

static char *doc_UpstreamVersion = "UpstreamVersion(a) -> string";
static PyObject *UpstreamVersion(PyObject *Self,PyObject *Args)
{
   char *Ver;
   if (PyArg_ParseTuple(Args,"s",&Ver) == 0)
      return 0;
   return CppPyString(_system->VS->UpstreamVersion(Ver));
}

static char *doc_ParseDepends =
"ParseDepends(s) -> list of tuples\n"
"\n"
"The resulting tuples are (Pkg,Ver,Operation). Each anded dependency is a\n"
"list of or'd dependencies\n"
"Source depends are evaluated against the curernt arch and only those that\n"
"Match are returned.";
static PyObject *RealParseDepends(PyObject *Self,PyObject *Args,
				  bool ParseArchFlags)
{
   string Package;
   string Version;
   unsigned int Op;

   const char *Start;
   const char *Stop;
   int Len;

   if (PyArg_ParseTuple(Args,"s#",&Start,&Len) == 0)
      return 0;
   Stop = Start + Len;
   PyObject *List = PyList_New(0);
   PyObject *LastRow = 0;
   while (1)
   {
      if (Start == Stop)
	 break;

      Start = debListParser::ParseDepends(Start,Stop,Package,Version,Op,
					  ParseArchFlags);
      if (Start == 0)
      {
	 PyErr_SetString(PyExc_ValueError,"Problem Parsing Dependency");
	 Py_DECREF(List);
	 return 0;
      }

      if (LastRow == 0)
	 LastRow = PyList_New(0);

      if (Package.empty() == false)
      {
	 PyObject *Obj;
	 PyList_Append(LastRow,Obj = Py_BuildValue("sss",Package.c_str(),
						   Version.c_str(),
						pkgCache::CompTypeDeb(Op)));
	 Py_DECREF(Obj);
      }

      // Group ORd deps into a single row..
      if ((Op & pkgCache::Dep::Or) != pkgCache::Dep::Or)
      {
	 if (PyList_Size(LastRow) != 0)
	    PyList_Append(List,LastRow);
	 Py_DECREF(LastRow);
	 LastRow = 0;
      }
   }
   return List;
}
static PyObject *ParseDepends(PyObject *Self,PyObject *Args)
{
   return RealParseDepends(Self,Args,false);
}
static PyObject *ParseSrcDepends(PyObject *Self,PyObject *Args)
{
   return RealParseDepends(Self,Args,true);
}
									/*}}}*/
// md5sum - Compute the md5sum of a file or string			/*{{{*/
// ---------------------------------------------------------------------
static char *doc_md5sum = "md5sum(String) -> String or md5sum(File) -> String";
static PyObject *md5sum(PyObject *Self,PyObject *Args)
{
   PyObject *Obj;
   if (PyArg_ParseTuple(Args,"O",&Obj) == 0)
      return 0;

   // Digest of a string.
   if (PyBytes_Check(Obj) != 0)
   {
      char *s;
      Py_ssize_t len;
      MD5Summation Sum;
      PyBytes_AsStringAndSize(Obj, &s, &len);
      Sum.Add((const unsigned char*)s, len);
      return CppPyString(Sum.Result().Value());
   }

   // Digest of a file
   int Fd = PyObject_AsFileDescriptor(Obj);
   if (Fd != -1)
   {
      MD5Summation Sum;
      struct stat St;
      if (fstat(Fd,&St) != 0 ||
	  Sum.AddFD(Fd,St.st_size) == false)
      {
	 PyErr_SetFromErrno(PyExc_SystemError);
	 return 0;
      }

      return CppPyString(Sum.Result().Value());
   }

   PyErr_SetString(PyExc_TypeError,"Only understand strings and files");
   return 0;
}
									/*}}}*/
// sha1sum - Compute the sha1sum of a file or string			/*{{{*/
// ---------------------------------------------------------------------
static char *doc_sha1sum = "sha1sum(String) -> String or sha1sum(File) -> String";
static PyObject *sha1sum(PyObject *Self,PyObject *Args)
{
   PyObject *Obj;
   if (PyArg_ParseTuple(Args,"O",&Obj) == 0)
      return 0;

   // Digest of a string.
   if (PyBytes_Check(Obj) != 0)
   {
      char *s;
      Py_ssize_t len;
      SHA1Summation Sum;
      PyBytes_AsStringAndSize(Obj, &s, &len);
      Sum.Add((const unsigned char*)s, len);
      return CppPyString(Sum.Result().Value());
   }

   // Digest of a file
   int Fd = PyObject_AsFileDescriptor(Obj);
   if (Fd != -1)
   {
      SHA1Summation Sum;
      struct stat St;
      if (fstat(Fd,&St) != 0 ||
	  Sum.AddFD(Fd,St.st_size) == false)
      {
	 PyErr_SetFromErrno(PyExc_SystemError);
	 return 0;
      }

      return CppPyString(Sum.Result().Value());
   }

   PyErr_SetString(PyExc_TypeError,"Only understand strings and files");
   return 0;
}
									/*}}}*/
// sha256sum - Compute the sha1sum of a file or string			/*{{{*/
// ---------------------------------------------------------------------
static char *doc_sha256sum = "sha256sum(String) -> String or sha256sum(File) -> String";
static PyObject *sha256sum(PyObject *Self,PyObject *Args)
{
   PyObject *Obj;
   if (PyArg_ParseTuple(Args,"O",&Obj) == 0)
      return 0;

   // Digest of a string.
   if (PyBytes_Check(Obj) != 0)
   {
      char *s;
      Py_ssize_t len;
      SHA256Summation Sum;
      PyBytes_AsStringAndSize(Obj, &s, &len);
      Sum.Add((const unsigned char*)s, len);
      return CppPyString(Sum.Result().Value());
   }

   // Digest of a file
   int Fd = PyObject_AsFileDescriptor(Obj);
   if (Fd != -1)
   {
      SHA256Summation Sum;
      struct stat St;
      if (fstat(Fd,&St) != 0 ||
	  Sum.AddFD(Fd,St.st_size) == false)
      {
	 PyErr_SetFromErrno(PyExc_SystemError);
	 return 0;
      }

      return CppPyString(Sum.Result().Value());
   }

   PyErr_SetString(PyExc_TypeError,"Only understand strings and files");
   return 0;
}
									/*}}}*/
// init - 3 init functions						/*{{{*/
// ---------------------------------------------------------------------
static char *doc_Init =
"init() -> None\n"
"Legacy. Do InitConfig then parse the command line then do InitSystem\n";
static PyObject *Init(PyObject *Self,PyObject *Args)
{
   if (PyArg_ParseTuple(Args,"") == 0)
      return 0;

   pkgInitConfig(*_config);
   pkgInitSystem(*_config,_system);

   Py_INCREF(Py_None);
   return HandleErrors(Py_None);
}

static char *doc_InitConfig =
"initconfig() -> None\n"
"Load the default configuration and the config file\n";
static PyObject *InitConfig(PyObject *Self,PyObject *Args)
{
   if (PyArg_ParseTuple(Args,"") == 0)
      return 0;

   pkgInitConfig(*_config);

   Py_INCREF(Py_None);
   return HandleErrors(Py_None);
}

static char *doc_InitSystem =
"initsystem() -> None\n"
"Construct the underlying system\n";
static PyObject *InitSystem(PyObject *Self,PyObject *Args)
{
   if (PyArg_ParseTuple(Args,"") == 0)
      return 0;

   pkgInitSystem(*_config,_system);

   Py_INCREF(Py_None);
   return HandleErrors(Py_None);
}
									/*}}}*/

// fileutils.cc: GetLock						/*{{{*/
// ---------------------------------------------------------------------
static char *doc_GetLock =
"GetLock(string) -> int\n"
"This will create an empty file of the given name and lock it. Once this"
" is done all other calls to GetLock in any other process will fail with"
" -1. The return result is the fd of the file, the call should call"
" close at some time\n";
static PyObject *GetLock(PyObject *Self,PyObject *Args)
{
   const char *file;
   char errors = false;
   if (PyArg_ParseTuple(Args,"s|b",&file,&errors) == 0)
      return 0;

   int fd = GetLock(file, errors);

   return  HandleErrors(Py_BuildValue("i", fd));
}

static char *doc_PkgSystemLock =
"PkgSystemLock() -> boolean\n"
"Get the global pkgsystem lock\n";
static PyObject *PkgSystemLock(PyObject *Self,PyObject *Args)
{
   if (PyArg_ParseTuple(Args,"") == 0)
      return 0;

   bool res = _system->Lock();

   Py_INCREF(Py_None);
   return HandleErrors(Py_BuildValue("b", res));
}

static char *doc_PkgSystemUnLock =
"PkgSystemUnLock() -> boolean\n"
"Unset the global pkgsystem lock\n";
static PyObject *PkgSystemUnLock(PyObject *Self,PyObject *Args)
{
   if (PyArg_ParseTuple(Args,"") == 0)
      return 0;

   bool res = _system->UnLock();

   Py_INCREF(Py_None);
   return HandleErrors(Py_BuildValue("b", res));
}

									/*}}}*/

// initapt_pkg - Core Module Initialization				/*{{{*/
// ---------------------------------------------------------------------
/* */
static PyMethodDef methods[] =
{
   // Constructors
   #ifdef COMPAT_0_7
   {"newConfiguration",newConfiguration,METH_VARARGS,doc_newConfiguration},
   #endif
   {"init",Init,METH_VARARGS,doc_Init},
   {"init_config",InitConfig,METH_VARARGS,doc_InitConfig},
   {"init_system",InitSystem,METH_VARARGS,doc_InitSystem},
   #ifdef COMPAT_0_7
   {"InitConfig",InitConfig,METH_VARARGS,doc_InitConfig},
   {"InitSystem",InitSystem,METH_VARARGS,doc_InitSystem},
   #endif

   // Tag File
   #ifdef COMPAT_0_7
   {"ParseSection",ParseSection,METH_VARARGS,doc_ParseSection},
   {"ParseTagFile",ParseTagFile,METH_VARARGS,doc_ParseTagFile},
   {"RewriteSection",RewriteSection,METH_VARARGS,doc_RewriteSection},
   #endif
   {"rewrite_section",RewriteSection,METH_VARARGS,doc_RewriteSection},

   // Locking
   {"get_lock",GetLock,METH_VARARGS,doc_GetLock},
   {"pkgsystem_lock",PkgSystemLock,METH_VARARGS,doc_PkgSystemLock},
   {"pkgsystem_unlock",PkgSystemUnLock,METH_VARARGS,doc_PkgSystemUnLock},
   #ifdef COMPAT_0_7
   {"GetLock",GetLock,METH_VARARGS,doc_GetLock},
   {"PkgSystemLock",PkgSystemLock,METH_VARARGS,doc_PkgSystemLock},
   {"PkgSystemUnLock",PkgSystemUnLock,METH_VARARGS,doc_PkgSystemUnLock},
   #endif

   // Command line
   {"read_config_file",LoadConfig,METH_VARARGS,doc_LoadConfig},
   {"read_config_dir",LoadConfigDir,METH_VARARGS,doc_LoadConfigDir},
   {"read_config_file_isc",LoadConfigISC,METH_VARARGS,doc_LoadConfig},
   {"parse_commandline",ParseCommandLine,METH_VARARGS,doc_ParseCommandLine},
   #ifdef COMPAT_0_7
   {"ReadConfigFile",LoadConfig,METH_VARARGS,doc_LoadConfig},
   {"ReadConfigDir",LoadConfigDir,METH_VARARGS,doc_LoadConfigDir},
   {"ReadConfigFileISC",LoadConfigISC,METH_VARARGS,doc_LoadConfig},
   {"ParseCommandLine",ParseCommandLine,METH_VARARGS,doc_ParseCommandLine},
   #endif

   // Versioning
   {"version_compare",VersionCompare,METH_VARARGS,doc_VersionCompare},
   {"check_dep",CheckDep,METH_VARARGS,doc_CheckDep},
   {"upstream_version",UpstreamVersion,METH_VARARGS,doc_UpstreamVersion},
   #ifdef COMPAT_0_7
   {"VersionCompare",VersionCompare,METH_VARARGS,doc_VersionCompare},
   {"CheckDep",CheckDep,METH_VARARGS,doc_CheckDep},
   {"UpstreamVersion",UpstreamVersion,METH_VARARGS,doc_UpstreamVersion},
   #endif

   // Depends
   {"parse_depends",ParseDepends,METH_VARARGS,doc_ParseDepends},
   {"parse_src_depends",ParseSrcDepends,METH_VARARGS,doc_ParseDepends},
   #ifdef COMPAT_0_7
   {"ParseDepends",ParseDepends,METH_VARARGS,doc_ParseDepends},
   {"ParseSrcDepends",ParseSrcDepends,METH_VARARGS,doc_ParseDepends},
   #endif

   // Stuff
   {"md5sum",md5sum,METH_VARARGS,doc_md5sum},
   {"sha1sum",sha1sum,METH_VARARGS,doc_sha1sum},
   {"sha256sum",sha256sum,METH_VARARGS,doc_sha256sum},

   // Strings
   {"check_domain_list",StrCheckDomainList,METH_VARARGS,"CheckDomainList(String,String) -> Bool"},
   {"quote_string",StrQuoteString,METH_VARARGS,"QuoteString(String,String) -> String"},
   {"dequote_string",StrDeQuote,METH_VARARGS,"DeQuoteString(String) -> String"},
   {"size_to_str",StrSizeToStr,METH_VARARGS,"SizeToStr(int) -> String"},
   {"time_to_str",StrTimeToStr,METH_VARARGS,"TimeToStr(int) -> String"},
   {"uri_to_filename",StrURItoFileName,METH_VARARGS,"URItoFileName(String) -> String"},
   {"base64_encode",StrBase64Encode,METH_VARARGS,"Base64Encode(String) -> String"},
   {"string_to_bool",StrStringToBool,METH_VARARGS,"StringToBool(String) -> int"},
   {"time_rfc1123",StrTimeRFC1123,METH_VARARGS,"TimeRFC1123(int) -> String"},
   {"str_to_time",StrStrToTime,METH_VARARGS,"StrToTime(String) -> Int"},
   #ifdef COMPAT_0_7
   {"CheckDomainList",StrCheckDomainList,METH_VARARGS,"CheckDomainList(String,String) -> Bool"},
   {"QuoteString",StrQuoteString,METH_VARARGS,"QuoteString(String,String) -> String"},
   {"DeQuoteString",StrDeQuote,METH_VARARGS,"DeQuoteString(String) -> String"},
   {"SizeToStr",StrSizeToStr,METH_VARARGS,"SizeToStr(int) -> String"},
   {"TimeToStr",StrTimeToStr,METH_VARARGS,"TimeToStr(int) -> String"},
   {"URItoFileName",StrURItoFileName,METH_VARARGS,"URItoFileName(String) -> String"},
   {"Base64Encode",StrBase64Encode,METH_VARARGS,"Base64Encode(String) -> String"},
   {"StringToBool",StrStringToBool,METH_VARARGS,"StringToBool(String) -> int"},
   {"TimeRFC1123",StrTimeRFC1123,METH_VARARGS,"TimeRFC1123(int) -> String"},
   {"StrToTime",StrStrToTime,METH_VARARGS,"StrToTime(String) -> Int"},
   #endif

   // Cache
   #ifdef COMPAT_0_7
   {"GetCache",TmpGetCache,METH_VARARGS,"GetCache() -> PkgCache"},
   {"GetDepCache",GetDepCache,METH_VARARGS,"GetDepCache(Cache) -> DepCache"},
   {"GetPkgRecords",GetPkgRecords,METH_VARARGS,"GetPkgRecords(Cache) -> PkgRecords"},
   {"GetPkgSrcRecords",GetPkgSrcRecords,METH_VARARGS,"GetPkgSrcRecords() -> PkgSrcRecords"},
   {"GetPkgSourceList",GetPkgSourceList,METH_VARARGS,"GetPkgSourceList() -> PkgSourceList"},

   // misc
   {"GetPkgProblemResolver",GetPkgProblemResolver,METH_VARARGS,"GetDepProblemResolver(DepCache) -> PkgProblemResolver"},
   {"GetPkgActionGroup",GetPkgActionGroup,METH_VARARGS,"GetPkgActionGroup(DepCache) -> PkgActionGroup"},

   // Cdrom
   {"GetCdrom",GetCdrom,METH_VARARGS,"GetCdrom() -> Cdrom"},

   // Acquire
   {"GetAcquire",GetAcquire,METH_VARARGS,"GetAcquire() -> Acquire"},
   {"GetPkgAcqFile",(PyCFunction)GetPkgAcqFile,METH_KEYWORDS|METH_VARARGS, doc_GetPkgAcqFile},

   // PkgManager
   {"GetPackageManager",GetPkgManager,METH_VARARGS,"GetPackageManager(DepCache) -> PackageManager"},
   #endif

   {}
};


#define ADDTYPE(mod,name,type) { \
    if (PyType_Ready(type) == -1) INIT_ERROR; \
    Py_INCREF(type); \
    PyModule_AddObject(mod,name,(PyObject *)type); }


#if PY_MAJOR_VERSION >= 3
struct module_state {
    PyObject *error;
};

#define GETSTATE(m) ((struct module_state*)PyModule_GetState(m))

static int apt_inst_traverse(PyObject *m, visitproc visit, void *arg) {
    Py_VISIT(GETSTATE(m)->error);
    return 0;
}

static int apt_inst_clear(PyObject *m) {
    Py_CLEAR(GETSTATE(m)->error);
    return 0;
}

static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        "apt_inst",
        NULL,
        sizeof(struct module_state),
        methods,
        NULL,
        apt_inst_traverse,
        apt_inst_clear,
        NULL
};

#define INIT_ERROR return 0
extern "C" PyObject * PyInit_apt_pkg()
#else
#define INIT_ERROR return
extern "C" void initapt_pkg()
#endif
{
   // Finalize our types to add slots, etc.
   if (PyType_Ready(&ConfigurationPtrType) == -1) INIT_ERROR;
   if (PyType_Ready(&ConfigurationSubType) == -1) INIT_ERROR;

   // Initialize the module
   #if PY_MAJOR_VERSION >= 3
   PyObject *Module = PyModule_Create(&moduledef);
   #else
   PyObject *Module = Py_InitModule("apt_pkg",methods);
   #endif

   // Global variable linked to the global configuration class
   CppPyObject<Configuration *> *Config = CppPyObject_NEW<Configuration *>(&ConfigurationPtrType);
   Config->Object = _config;
   PyModule_AddObject(Module,"config",Config);
   #ifdef COMPAT_0_7
   Py_INCREF(Config);
   PyModule_AddObject(Module,"Config",Config);
   #endif

   // Add our classes.
   /* ============================ tag.cc ============================ */
   ADDTYPE(Module,"TagSection",&TagSecType);
   ADDTYPE(Module,"TagFile",&TagFileType);
   /* ============================ acquire.cc ============================ */
   ADDTYPE(Module,"Acquire",&PkgAcquireType);
   ADDTYPE(Module,"AcquireFile",&PkgAcquireFileType);
   ADDTYPE(Module,"AcquireItem",&AcquireItemType); // NO __new__()
   /* ============================ cache.cc ============================ */
   ADDTYPE(Module,"Cache",&PkgCacheType);
   ADDTYPE(Module,"Dependency",&DependencyType); // NO __new__()
   ADDTYPE(Module,"Description",&DescriptionType); // NO __new__()
   ADDTYPE(Module,"PackageFile",&PackageFileType); // NO __new__()
   //ADDTYPE(Module,"PackageList",&PkgListType);  // NO __new__(), internal
   //ADDTYPE(Module,"DependencyList",&RDepListType); // NO __new__(), internal
   ADDTYPE(Module,"Package",&PackageType); // NO __new__()
   ADDTYPE(Module,"Version",&VersionType); // NO __new__()
   /* ============================ cdrom.cc ============================ */
   ADDTYPE(Module,"Cdrom",&PkgCdromType);
   /* ========================= configuration.cc ========================= */
   ADDTYPE(Module,"Configuration",&ConfigurationType);
   //ADDTYPE(Module,"ConfigurationSub",&ConfigurationSubType); // NO __new__()
   //ADDTYPE(Module,"ConfigurationPtr",&ConfigurationPtrType); // NO __new__()
   /* ========================= depcache.cc ========================= */
   ADDTYPE(Module,"ActionGroup",&PkgActionGroupType);
   ADDTYPE(Module,"DepCache",&PkgDepCacheType);
   ADDTYPE(Module,"ProblemResolver",&PkgProblemResolverType);
   /* ========================= indexfile.cc ========================= */
   ADDTYPE(Module,"PackageIndexFile",&PackageIndexFileType); // NO __new__()
   /* ========================= metaindex.cc ========================= */
   ADDTYPE(Module,"MetaIndex",&MetaIndexType); // NO __new__()
   /* ========================= pkgmanager.cc ========================= */
   ADDTYPE(Module,"PackageManager",&PkgManagerType);
   /* ========================= pkgrecords.cc ========================= */
   ADDTYPE(Module,"PackageRecords",&PkgRecordsType);
   /* ========================= pkgsrcrecords.cc ========================= */
   ADDTYPE(Module,"SourceRecords",&PkgSrcRecordsType);
   /* ========================= sourcelist.cc ========================= */
   ADDTYPE(Module,"SourceList",&PkgSourceListType);
   // Tag file constants
   PyModule_AddObject(Module,"REWRITE_PACKAGE_ORDER",
                      CharCharToList(TFRewritePackageOrder));

   PyModule_AddObject(Module,"REWRITE_SOURCE_ORDER",
                      CharCharToList(TFRewriteSourceOrder));
#ifdef COMPAT_0_7
   PyModule_AddObject(Module,"RewritePackageOrder",
                      CharCharToList(TFRewritePackageOrder));

   PyModule_AddObject(Module,"RewriteSourceOrder",
                      CharCharToList(TFRewriteSourceOrder));
#endif

   // Version..
   PyModule_AddStringConstant(Module,"VERSION",(char *)pkgVersion);
   PyModule_AddStringConstant(Module,"LIB_VERSION",(char *)pkgLibVersion);
   PyModule_AddStringConstant(Module,"DATE",__DATE__);
   PyModule_AddStringConstant(Module,"TIME",__TIME__);
#ifdef COMPAT_0_7
   PyModule_AddStringConstant(Module,"Version",(char *)pkgVersion);
   PyModule_AddStringConstant(Module,"LibVersion",(char *)pkgLibVersion);
   PyModule_AddStringConstant(Module,"Date",__DATE__);
   PyModule_AddStringConstant(Module,"Time",__TIME__);
#endif

   // My constants
   PyModule_AddIntConstant(Module,"DEP_DEPENDS",pkgCache::Dep::Depends);
   PyModule_AddIntConstant(Module,"DEP_PRE_DEPENDS",pkgCache::Dep::PreDepends);
   PyModule_AddIntConstant(Module,"DEP_SUGGESTS",pkgCache::Dep::Suggests);
   PyModule_AddIntConstant(Module,"DEP_RECOMMENDS",pkgCache::Dep::Recommends);
   PyModule_AddIntConstant(Module,"DEP_CONFLICTS",pkgCache::Dep::Conflicts);
   PyModule_AddIntConstant(Module,"DEP_REPLACES",pkgCache::Dep::Replaces);
   PyModule_AddIntConstant(Module,"DEP_OBSOLTES",pkgCache::Dep::Obsoletes);
#ifdef COMPAT_0_7
   PyModule_AddIntConstant(Module,"DepDepends",pkgCache::Dep::Depends);
   PyModule_AddIntConstant(Module,"DepPreDepends",pkgCache::Dep::PreDepends);
   PyModule_AddIntConstant(Module,"DepSuggests",pkgCache::Dep::Suggests);
   PyModule_AddIntConstant(Module,"DepRecommends",pkgCache::Dep::Recommends);
   PyModule_AddIntConstant(Module,"DepConflicts",pkgCache::Dep::Conflicts);
   PyModule_AddIntConstant(Module,"DepReplaces",pkgCache::Dep::Replaces);
   PyModule_AddIntConstant(Module,"DepObsoletes",pkgCache::Dep::Obsoletes);
#endif

   PyModule_AddIntConstant(Module,"PRI_IMPORTANT",pkgCache::State::Important);
   PyModule_AddIntConstant(Module,"PRI_REQUIRED",pkgCache::State::Required);
   PyModule_AddIntConstant(Module,"PRI_STANDARD",pkgCache::State::Standard);
   PyModule_AddIntConstant(Module,"PRI_OPTIONAL",pkgCache::State::Optional);
   PyModule_AddIntConstant(Module,"PRI_EXTRA",pkgCache::State::Extra);
#ifdef COMPAT_0_7
   PyModule_AddIntConstant(Module,"PriImportant",pkgCache::State::Important);
   PyModule_AddIntConstant(Module,"PriRequired",pkgCache::State::Required);
   PyModule_AddIntConstant(Module,"PriStandard",pkgCache::State::Standard);
   PyModule_AddIntConstant(Module,"PriOptional",pkgCache::State::Optional);
   PyModule_AddIntConstant(Module,"PriExtra",pkgCache::State::Extra);
#endif
   // CurState
   PyModule_AddIntConstant(Module,"CURSTATE_NOT_INSTALLED",pkgCache::State::NotInstalled);
   PyModule_AddIntConstant(Module,"CURSTATE_UNPACKED",pkgCache::State::UnPacked);
   PyModule_AddIntConstant(Module,"CURSTATE_HALF_CONFIGURED",pkgCache::State::HalfConfigured);
   PyModule_AddIntConstant(Module,"CURSTATE_HALF_INSTALLED",pkgCache::State::HalfInstalled);
   PyModule_AddIntConstant(Module,"CURSTATE_CONFIG_FILES",pkgCache::State::ConfigFiles);
   PyModule_AddIntConstant(Module,"CURSTATE_INSTALLED",pkgCache::State::Installed);
   // SelState
   PyModule_AddIntConstant(Module,"SELSTATE_UNKNOWN",pkgCache::State::Unknown);
   PyModule_AddIntConstant(Module,"SELSTATE_INSTALL",pkgCache::State::Install);
   PyModule_AddIntConstant(Module,"SELSTATE_HOLD",pkgCache::State::Hold);
   PyModule_AddIntConstant(Module,"SELSTATE_DEINSTALL",pkgCache::State::DeInstall);
   PyModule_AddIntConstant(Module,"SELSTATE_PURGE",pkgCache::State::Purge);
   // InstState
   PyModule_AddIntConstant(Module,"INSTSTATE_OK",pkgCache::State::Ok);
   PyModule_AddIntConstant(Module,"INSTSTATE_REINSTREQ",pkgCache::State::ReInstReq);
   PyModule_AddIntConstant(Module,"INSTSTATE_HOLD",pkgCache::State::Hold);
   PyModule_AddIntConstant(Module,"INSTSTATE_HOLD_REINSTREQ",pkgCache::State::HoldReInstReq);

#ifdef COMPAT_0_7
   PyModule_AddIntConstant(Module,"CurStateNotInstalled",pkgCache::State::NotInstalled);
   PyModule_AddIntConstant(Module,"CurStateUnPacked",pkgCache::State::UnPacked);
   PyModule_AddIntConstant(Module,"CurStateHalfConfigured",pkgCache::State::HalfConfigured);
   PyModule_AddIntConstant(Module,"CurStateHalfInstalled",pkgCache::State::HalfInstalled);
   PyModule_AddIntConstant(Module,"CurStateConfigFiles",pkgCache::State::ConfigFiles);
   PyModule_AddIntConstant(Module,"CurStateInstalled",pkgCache::State::Installed);

   PyModule_AddIntConstant(Module,"SelStateUnknown",pkgCache::State::Unknown);
   PyModule_AddIntConstant(Module,"SelStateInstall",pkgCache::State::Install);
   PyModule_AddIntConstant(Module,"SelStateHold",pkgCache::State::Hold);
   PyModule_AddIntConstant(Module,"SelStateDeInstall",pkgCache::State::DeInstall);
   PyModule_AddIntConstant(Module,"SelStatePurge",pkgCache::State::Purge);

   PyModule_AddIntConstant(Module,"InstStateOk",pkgCache::State::Ok);
   PyModule_AddIntConstant(Module,"InstStateReInstReq",pkgCache::State::ReInstReq);
   PyModule_AddIntConstant(Module,"InstStateHold",pkgCache::State::Hold);
   PyModule_AddIntConstant(Module,"InstStateHoldReInstReq",pkgCache::State::HoldReInstReq);
#endif

   #ifdef COMPAT_0_7
   PyModule_AddIntConstant(Module,"_COMPAT_0_7",1);
   #else
   PyModule_AddIntConstant(Module,"_COMPAT_0_7",0);
   #endif
   #if PY_MAJOR_VERSION >= 3
   return Module;
   #endif
}
									/*}}}*/

