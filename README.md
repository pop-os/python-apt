# Python-apt is a wrapper to use features of apt from python.

It contains the following modules:

## C++ Wrapper:

* apt_pkg - access to libapt-pkg (wrapper to the lowlevel c++ code)
* apt_inst - access to libapt-inst (wrapper to the lowlevel c++ code)

## Python module:

* apt - high level python interface build on top of apt_pkg, apt_inst
* aptsources - high level manipulation of sources.list


# Development

## Building

To build python-apt run:
```
$ python setup.py build
```
You may need to install the build-dependencies via:
```
$ sudo apt build-dep ./
```
first.

## Running the tests

Run the tests with:
```
$ python tests/test_all.py
$ python3 tests/test_all.py
```

