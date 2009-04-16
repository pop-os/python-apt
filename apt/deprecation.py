# deprecation.py - Module providing classes and functions for deprecation.
#
#  Copyright (c) 2009 Julian Andres Klode <jak@debian.org>
#  Copyright (c) 2009 Ben Finney <ben+debian@benfinney.id.au>
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License as
#  published by the Free Software Foundation; either version 2 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
#  USA
"""Classes and functions for deprecating features.

This is used for internal purposes only and not part of the official API. Do
not use it for anything outside the apt package.
"""
import re
import operator
import warnings

__all__ = []


class AttributeDeprecatedBy(object):
    """Property acting as a proxy for a new attribute.

    When accessed, the property issues a DeprecationWarning and (on get) calls
    attrgetter() for the attribute 'attribute' on the current object or (on
    set) uses setattr to set the value of the wrapped attribute.
    """

    def __init__(self, attribute):
        """Initialize the property."""
        self.attribute = attribute
        self.__doc__ = 'Deprecated, please use \'%s\' instead' % attribute
        self.getter = operator.attrgetter(attribute)

    def __get__(self, obj, type=None):
        """Issue a  DeprecationWarning and return the requested value."""
        if obj is None:
            return getattr(type, self.attribute, self)
        warnings.warn(self.__doc__, DeprecationWarning, stacklevel=2)
        return self.getter(obj or type)

    def __set__(self, obj, value):
        """Issue a  DeprecationWarning and set the requested value."""
        warnings.warn(self.__doc__, DeprecationWarning, stacklevel=2)
        setattr(obj, self.attribute, value)


def function_deprecated_by(func, convert_names=True):
    """Return a function that warns it is deprecated by another function.

    Returns a new function that warns it is deprecated by function 'func',
    then acts as a pass-through wrapper for 'func'.

    This function also converts all keyword argument names from mixedCase to
    lowercase_with_underscores, but only if 'convert_names' is True (default).
    """
    warning = 'Deprecated, please use \'%s\' instead' % func.func_name

    def deprecated_function(*args, **kwds):
        warnings.warn(warning, DeprecationWarning, stacklevel=2)
        if convert_names:
            for key in kwds.keys():
                kwds[re.sub('([A-Z])', '_\\1', key).lower()] = kwds.pop(key)
        return func(*args, **kwds)
    return deprecated_function
