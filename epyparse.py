"""
epyparse.py
"""

__version__ = '0.2.1'

import os
import sys
import types
from os.path import dirname, basename, abspath, splitext
from os.path import exists as pathexists, join as pathjoin, dirname, basename, abspath
import operator
import re
import json
import inspect
from itertools import ifilter

from epydoc.docparser import parse_docs
from epydoc.apidoc import UNKNOWN, ModuleDoc, ClassDoc, RoutineDoc, ValueDoc

NULLS = set([None, UNKNOWN])

MODULE_ORDER = [
    ModuleDoc,
    UNKNOWN,
    RoutineDoc,
    ClassDoc,
]

CLASS_ORDER = [
    UNKNOWN,
    ClassDoc,
    RoutineDoc,
]

RX_DOTTED_NAME = re.compile(r'^[a-zA-Z_]+[a-zA-Z_.]*$')

def notnull(val):
    """Return True if val is neither None nor UNKNOWN"""
    return not any(operator.is_(val, obj) for obj in NULLS)

def valid_dotted_name(name):
    """validate that 'name' is a syntactically valid python name"""
    return bool(RX_DOTTED_NAME.match(name))

def sort_key(parent_type, reverse):
    """
    Sort a `APIDoc.variables` dictionary - by default, 'functions then classes'
    for modules and 'inner classes then methods' for classes. You can have the
    order of module members be 'classes then functions' by setting reverse to
    True, but this doesn't affect the order of a class's members, which will
    always be the default. Objects of the same type will be ordered alphabetically.

    This is a factory function which returns the appropriate key function for
    the parent_type.
    """
    ordering = MODULE_ORDER
    if parent_type is ClassDoc:
        ordering = CLASS_ORDER
    elif reverse:
        ordering = list(reversed(ordering))
    def object_order(var):
        try:
            return ordering.index(type(var.value)), str(var.value.canonical_name)
        except ValueError:
            return (-1, '')
    return object_order

__all__ = [
    'Parser', 'Object',
    'parsed', 'flattened', 'pprint', 'objectify',
]

def parsed(name_or_path):
    """
    Parse a Python object or file, return a nested dictionary of API objects
    """
    return Parser().parse(name_or_path)

def flattened(name_or_path):
    """
    Parse a Python object or file, return a list of dictionaries of API objects
    """
    return list(Parser().flatten(name_or_path))

def pprint(name_or_path, out=sys.stdout, reverse=False):
    """
    Pretty print the contents of a Python object or file

    Module contents are printed 'functions first, then classes', unless reverse
    is True, in which case classes are printed first.
    """
    Parser().pprint(name_or_path, out)

def objectify(json_file):
    """
    Convert a JSON-serialized API object to a dict-like object
    """
    return Object.from_json(json_file)

class Parser(object):
    func_arg_items = (
        'vararg', 'kwarg', 'lineno', 'return_descr', 'return_type', 
    )
    func_arg_lists = (
        'arg_descrs', 'arg_types', 'exception_descrs',
    )

    def _update_function(self, info, apidoc):
        """update a function object's api info"""
        for attr in self.func_arg_items:
            val = getattr(apidoc, attr, None)
            if notnull(val):
                attr = attr.replace('return_', 'r')
                info[attr] = val
        # function signature
        args = apidoc.posargs
        if notnull(args):
            req_args = []
            defaults = apidoc.posarg_defaults
            if notnull(defaults):
                assert len(args) == len(defaults), "can't resolve function signature"
                params = []
                for arg, default in zip(args, defaults):
                    try:
                        default = default.summary_pyval_repr().to_plaintext(None)
                    except AttributeError:
                        default = None
                    if default is None:
                        req_args.append(arg)
                    else:
                        params.append([arg, default])
                info['args'] = req_args
                info['params'] = params
            else:
                info['args'] = args

    def _update_class(self, info, apidoc):
        pass

    def _update_module(self, info, apidoc):
        pass

    def _update(self, info, apidoc, apitype, parent_type):
        objtype = None
        if apitype is RoutineDoc:
            objtype = 'function'
            if parent_type is ClassDoc:
                # TODO - review
                info['is_method'] = True
        else:
            # name after apitype without the final 'Doc'
            objtype = apitype.__name__.lower()[:-3]
        info['type'] = objtype
        getattr(self, '_update_' + objtype, lambda i, a: None)(info, apidoc)

    @staticmethod
    def get_object_api_doc(name_or_path):
        """returns the epydoc parse-only APIDoc object for the python file or object"""
        if pathexists(name_or_path):
            return parse_docs(filename=name_or_path)
        else:
            if valid_dotted_name(name_or_path):
                return parse_docs(name=name_or_path)
        raise IOError("No such file %s" % name_or_path)

    def iterparse(self, apidoc, parent_type=None, reverse=False):
        """
        Recursively iterate through the APIDoc objects produced by epydoc.

        We use a pair of try/except clauses to force any given object to
        be skipped if it doesn't quack as we would like - ie. if it doesn't
        have valid 'canonical_name' and 'variables' attributes. This works for
        the moment because we are only interested in modules, classes and
        functions, but a more thorough interrogation of the object will
        be required if we want to handle imports and class attributes etc.
        """
        if isinstance(apidoc, basestring):
            apidoc = self.get_object_api_doc(apidoc)
        skip = False
        try:
            name = apidoc.canonical_name[-1]
            skip = name[0] == '_' and name[1] != '_'
        except:
            skip = True
        if skip:
            raise StopIteration
        info = dict(
            fullname=str(apidoc.canonical_name).lstrip('.'),
        )
        if notnull(apidoc.docstring):
            info['docstring'] = inspect.cleandoc(apidoc.docstring)
        apitype = type(apidoc)
        self._update(info, apidoc, apitype, parent_type)
        try:
            vals = apidoc.variables.itervalues()
        except:
            children = ()
        else:
            vals = sorted(vals, key=sort_key(apitype, reverse))
            children = (self.iterparse(val.value, parent_type=apitype, reverse=reverse) for val in vals)
        yield info, children

    def parse(self, name_or_path):
        """Create a dictionary from the `iterparse` results"""
        def visit(iterable):
            d = {}
            for info, children in iterable:
                d.update(info)
                members = []
                for child in children:
                    child = visit(child)
                    if child:
                        members.append(child)
                if members:
                    d['children'] = members
            return d
        return visit(self.iterparse(name_or_path))

    def flatten(self, name_or_path):
        """Convert the recursive `iterparse` results to a flat iterable"""
        def visit(iterable):
            for info, children in iterable:
                allmembers = []
                for child in children:
                    for item in visit(child):
                        allmembers.append(item['fullname'].rpartition('.'))
                        yield item
                members = [m[2] for m in allmembers if m[0] == info['fullname']]
                if members:
                    info['members'] = members
                info['attributes'] = {
                    '__doc__': info.pop('docstring', ''),
                    '__name__': info['fullname'].rpartition('.')[2],
                }
                yield info
        return visit(self.iterparse(name_or_path))

    def pprint(self, name_or_path, out, reverse=False):
        """Pretty print the `iterparse` results."""
        tab = ' ' * 4
        quote = '"""'
        def visit(iterable, level=0):
            indent = level * tab
            for info, children in iterable:
                name = info['fullname'].rpartition('.')[2]
                typ = info['type']
                if typ == 'function':
                    typ = 'def'
                elif typ == 'module':
                    name = info['fullname']
                out.write(indent + typ + ' ' + name)
                if typ == 'def':
                    args = info.get('args', [])
                    params = info.get('params')
                    if params:
                        args.extend('='.join(pair) for pair in params)
                    opt = info.get('vararg')
                    if opt:
                        args.append('*' + opt)
                    opt = info.get('kwarg')
                    if opt:
                        args.append('**' + opt)
                    out.write('(%s)' % ', '.join(args))
                out.write(':\n')
                doc = info.get('docstring', '')
                lead = indent + tab
                if typ == 'module':
                    lead = lead[:-len(tab)]
                out.write(lead + quote + '\n')
                for line in doc.splitlines():
                    out.write(lead + line + '\n')
                out.write(lead + quote + '\n')
                out.write('\n')
                if typ != 'module':
                    level += 1
                for child in children:
                    visit(child, level)
        visit(self.iterparse(name_or_path, reverse=reverse))

class Object(dict):
    """
    A dict subclass representing any API object.
    """

    @classmethod
    def from_json(cls, path):
        """
        Rehydrate a serialized Object.
        """
        with open(path) as fp:
            obj = cls(json.load(fp))
        obj['src'] = path
        obj['attributes']['__dict__'] = obj.to_dict()
        return obj

    @property
    def name(self):
        """Shorthand for the last item in the dotted string"""
        return self.__getitem__('fullname').rpartition('.')[2]

    @property
    def parent(self):
        """Return the name of the object's containing object"""
        return self.__getitem__('fullname').rpartition('.')[0]

    @property
    def members(self):
        """Return the names of the objects members in a, possibly empty, list"""
        return self.get('members', [])

    def get_parent(self):
        """Deserialize the object's container"""
        src = self.get('src', None)
        if src is not None:
            parent = self.parent
            if parent:
                fname = '%s/%s' % (dirname(src), parent)
                return self.from_json(fname)
        return None

    def get_member(self, key, default=None):
        """Deserialize a particular object member"""
        src = '%s/%s.%s' % (dirname(self['src']), self['fullname'], key)
        try:
            return self.from_json(src)
        except IOError:
            return default

    def get_members(self):
        """Deserialize all members"""
        return [self.get_member(m) for m in self.get('members', ())]

    def get_attribute(self, key, default=None):
        return self.attributes.get(key, default)

    def __dir__(self):
        return self.members + self.attributes.keys()

    @property
    def __doc__(self):
        return self.get_attribute('__doc__')

    @property
    def __name__(self):
        return self.get_attribute('__name__')

    def to_dict(self):
        d = dict(self.attributes)
        for m in self.members:
            d[m] = self.get_member(m)
        return d

    @property
    def __dict__(self):
        return self.attributes.setdefault('__dict__', self.to_dict())

Object.__getattr__ = dict.__getitem__
Object.__setattr__ = dict.__setitem__
Object.__delattr__ = dict.__delitem__

class Inspector(object):

    @staticmethod
    def ismodule(obj):
        return obj.get('type') == 'module'

    @staticmethod
    def isclass(obj):
        return obj.get('type') == 'class'

    @staticmethod
    def isfunction(obj):
        return obj.get('type') == 'function'

    @staticmethod
    def ismethod(obj):
        return obj.get('type') == 'function' and obj.get('is_method')

    @staticmethod
    def isclassmethod(obj):
        return obj.get('type') == 'classmethod'

    @staticmethod
    def isroutine(obj):
        return obj.get('type') == 'function'

    @staticmethod
    def getargspec(obj):
        params = obj.get('params')
        if params:
            defaults = tuple(t[1] for t in params)
        else:
            defaults = None
        args = obj.get('args')
        if args and params:
            args += [t[0] for t in params]
        return inspect.ArgSpec(args, obj.get('vararg'), obj.get('kwarg'), defaults)

    @staticmethod
    def getmembers(obj, predicate=None):
        if predicate:
            return [m for m in obj.get_members() if predicate(m)]
        return obj.get_members()

    @staticmethod
    def getdoc(obj):
        """Get the documentation string for an object.

        All tabs are expanded to spaces.  To clean up docstrings that are
        indented to line up with blocks of code, any whitespace than can be
        uniformly removed from the second line onwards is removed."""
        try:
            doc = obj.__doc__
        except AttributeError:
            return None
        if not isinstance(doc, types.StringTypes):
            return None
        return doc

    @staticmethod
    def hasattr(obj, attr):
        if not isinstance(obj, Object):
            return False
        return attr in obj.attributes or attr in obj.members

    @staticmethod
    def getattr(obj, attr, default=None):
        if not isinstance(obj, Object):
            return default
        try:
            return obj.attributes[attr]
        except KeyError:
            return obj.get_member(attr, default)

