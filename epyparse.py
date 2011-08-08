"""
epyparse.py
"""

__version__ = '0.1.1'

import os
import sys
from os.path import dirname, basename, abspath, splitext
from os.path import exists as pathexists, join as pathjoin, dirname, basename, abspath
import operator
import re
import json
import textwrap
from inspect import cleandoc

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
    """Return True if val is neither None or UNKNOWN"""
    return not any(operator.is_(val, obj) for obj in NULLS)

def valid_dotted_name(name):
    """validate that 'name' is a possible module name"""
    return bool(RX_DOTTED_NAME.match(name))

def sort_key(parent_type, reverse):
    """
    Sort a `APIDoc.variables` dictionary - by default, 'functions then classes'
    for modules and 'inner classes then methods' for classes. You can have the
    order of module members be 'classes then functions' by setting reverse to
    True, but this doesn't affect the order of a class's members, which will
    always be the default. Objects of the same type will be ordered alphabetically.
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

def parsed(module_or_filename):
    """
    Parse a Python module or file, return a nested dictionary of API objects
    """
    return Parser().parse(module_or_filename)

def flattened(module_or_filename):
    """
    Parse a Python module or file, return a list of dictionaries of API objects
    """
    return list(Parser().flatten(module_or_filename))

def pprint(module_or_filename, out=sys.stdout, reverse=False):
    """
    Pretty print the contents of a Python module or file

    Module contents are printed 'functions first, then classes', unless reverse
    is True, in which case classes are printed first.
    """
    Parser().pprint(module_or_filename, out)

def objectify(json_file):
    """
    Convert a JSON-serialized API object to a dict-like object
    """
    return Object.from_json(json_file)

class Object(dict):

    @classmethod
    def from_json(cls, path):
        with open(path) as fp:
            obj = cls(json.load(fp))
        obj['src'] = path
        return obj

    @property
    def name(self):
        return self.__getitem__('fullname').rpartition('.')[2]

    def get_parent(self):
        src = self.get('src', None)
        if src is not None:
            parent = self['fullname'].rpartition('.')[0]
            if parent:
                fname = '%s/%s' % (dirname(src), parent)
                return self.from_json(fname)
        return None

    def get_children(self):
        members = self.get('members')
        if not members:
            return []
        root = dirname(self['src'])
        return [self.from_json(root + '/' + m) for m in members]

Object.__getattr__ = dict.__getitem__
Object.__setattr__ = dict.__setitem__
Object.__delattr__ = dict.__delitem__

class Parser(object):
    func_arg_items = (
        'vararg', 'kwarg', 'lineno', 'return_descr', 'return_type', 
    )
    func_arg_lists = (
        'arg_descrs', 'arg_types', 'exception_descrs',
    )

    def _update_function(self, info, apidoc):
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
    def get_module_api_doc(module_or_filename):
        """returns the epydoc parse-only APIDoc object for the file or module"""
        if pathexists(module_or_filename):
            return parse_docs(filename=module_or_filename)
        else:
            if valid_dotted_name(module_or_filename):
                return parse_docs(name=module_or_filename)
        raise IOError("No such file %s" % module_or_filename)

    def iterparse(self, apidoc, parent_type=None, reverse=False):
        """
        Recursively iterate through APIDoc objects produced by epydoc.

        We use a pair of try/except clauses to force any given object to
        be skipped if it doesn't quack as we would like - ie. if it has a
        valid canonical_name and a variables attribute. This works for
        the moment because we are only interested in modules, classes and
        functions, but a more thorough interrogation of the object will
        be required if we want to handle imports and class attributes etc.
        """
        if isinstance(apidoc, basestring):
            apidoc = self.get_module_api_doc(apidoc)
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
            info['docstring'] = apidoc.docstring
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

    def parse(self, module_or_filename):
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
        return visit(self.iterparse(module_or_filename))

    def flatten(self, module_or_filename):
        def visit(iterable):
            for info, children in iterable:
                members = []
                for child in children:
                    for item in visit(child):
                        members.append(item['fullname'])
                        yield item
                if members:
                    info['members'] = members
                yield info
        return visit(self.iterparse(module_or_filename))

    def pprint(self, module_or_filename, out, reverse=False):
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
                for line in cleandoc(doc).splitlines():
                    out.write(lead + line + '\n')
                out.write(lead + quote + '\n')
                out.write('\n')
                if typ != 'module':
                    level += 1
                for child in children:
                    visit(child, level)
        visit(self.iterparse(module_or_filename, reverse=reverse))


if __name__ == '__main__':
    import doctest
    doctest.testmod()

