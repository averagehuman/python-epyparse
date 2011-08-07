"""

Parse bad file name::

    >>> parsed('does/not/exist')
    Traceback (most recent call last):
        ...
    IOError: No such file does/not/exist

Parse bad module name::

    >>> parsed('does.not.exist')
    Traceback (most recent call last):
        ...
    ImportError: No Python source file found.

Parse module::

    >>> d = parsed('epydoc.apidoc')
    >>> sorted(d.keys())
    ['children', 'docstring', 'fullname', 'type']
    >>> d['type']
    'module'
    >>> for item in sorted(d['children'], key=lambda d: (d['type'], d['fullname'])):
    ...     print item['type'], ' -> ', item['fullname']
    class  ->  epydoc.apidoc.APIDoc
    class  ->  epydoc.apidoc.ClassDoc
    class  ->  epydoc.apidoc.ClassMethodDoc
    class  ->  epydoc.apidoc.DocIndex
    class  ->  epydoc.apidoc.DottedName
    class  ->  epydoc.apidoc.GenericValueDoc
    class  ->  epydoc.apidoc.ModuleDoc
    class  ->  epydoc.apidoc.NamespaceDoc
    class  ->  epydoc.apidoc.PropertyDoc
    class  ->  epydoc.apidoc.RoutineDoc
    class  ->  epydoc.apidoc.StaticMethodDoc
    class  ->  epydoc.apidoc.ValueDoc
    class  ->  epydoc.apidoc.VariableDoc
    function  ->  epydoc.apidoc.pp_apidoc
    function  ->  epydoc.apidoc.reachable_valdocs

Flatten and JSON-serialize. For the `Object.get_parent` and `Object.get_children`
deserialization methods to work, we rely on the convention that api objects have
been saved to the same directory with the canonical name as file name and with no
file extension::

    >>> assert not pathexists('TESTOUT')
    >>> os.mkdir('TESTOUT')
    >>> for item in flattened('epydoc.apidoc'):
    ...     print item['fullname']
    ...     with open('TESTOUT/' + item['fullname'], 'w+b') as fp:
    ...         json.dump(item, fp)
    ...
    epydoc.apidoc.StaticMethodDoc
    epydoc.apidoc.VariableDoc.is_detailed
    epydoc.apidoc.VariableDoc.__repr__
    epydoc.apidoc.VariableDoc.apidoc_links
    epydoc.apidoc.VariableDoc.__init__
    epydoc.apidoc.VariableDoc
    epydoc.apidoc.ClassMethodDoc
    epydoc.apidoc.ClassDoc.is_newstyle_class
    epydoc.apidoc.ClassDoc.apidoc_links
    epydoc.apidoc.ClassDoc.is_exception
    epydoc.apidoc.ClassDoc.select_variables
    epydoc.apidoc.ClassDoc.is_type
    epydoc.apidoc.ClassDoc.mro
    epydoc.apidoc.ClassDoc
    epydoc.apidoc.RoutineDoc.all_args
    epydoc.apidoc.RoutineDoc.is_detailed
    epydoc.apidoc.RoutineDoc
    epydoc.apidoc.pp_apidoc
    epydoc.apidoc.NamespaceDoc.apidoc_links
    epydoc.apidoc.NamespaceDoc.init_sorted_variables
    epydoc.apidoc.NamespaceDoc.is_detailed
    epydoc.apidoc.NamespaceDoc.init_variable_groups
    epydoc.apidoc.NamespaceDoc.report_unused_groups
    epydoc.apidoc.NamespaceDoc.group_names
    epydoc.apidoc.NamespaceDoc.__init__
    epydoc.apidoc.NamespaceDoc
    epydoc.apidoc.DottedName.contextualize
    epydoc.apidoc.DottedName.dominates
    epydoc.apidoc.DottedName.container
    epydoc.apidoc.DottedName.__getitem__
    epydoc.apidoc.DottedName.__str__
    epydoc.apidoc.DottedName.InvalidDottedName
    epydoc.apidoc.DottedName.__radd__
    epydoc.apidoc.DottedName.__len__
    epydoc.apidoc.DottedName.__repr__
    epydoc.apidoc.DottedName.__add__
    epydoc.apidoc.DottedName.__hash__
    epydoc.apidoc.DottedName.__cmp__
    epydoc.apidoc.DottedName.__init__
    epydoc.apidoc.DottedName
    epydoc.apidoc.reachable_valdocs
    epydoc.apidoc.APIDoc.pp
    epydoc.apidoc.APIDoc.is_detailed
    epydoc.apidoc.APIDoc.__init__
    epydoc.apidoc.APIDoc.pp
    epydoc.apidoc.APIDoc.__cmp__
    epydoc.apidoc.APIDoc.apidoc_links
    epydoc.apidoc.APIDoc.merge_and_overwrite
    epydoc.apidoc.APIDoc.specialize_to
    epydoc.apidoc.APIDoc.__repr__
    epydoc.apidoc.APIDoc.__hash__
    epydoc.apidoc.APIDoc
    epydoc.apidoc.PropertyDoc.apidoc_links
    epydoc.apidoc.PropertyDoc.is_detailed
    epydoc.apidoc.PropertyDoc
    epydoc.apidoc.GenericValueDoc.is_detailed
    epydoc.apidoc.GenericValueDoc
    epydoc.apidoc.DocIndex.reachable_valdocs
    epydoc.apidoc.DocIndex.get_vardoc
    epydoc.apidoc.DocIndex.read_profiling_info
    epydoc.apidoc.DocIndex.get_valdoc
    epydoc.apidoc.DocIndex.container
    epydoc.apidoc.DocIndex.find
    epydoc.apidoc.DocIndex.__init__
    epydoc.apidoc.DocIndex
    epydoc.apidoc.ModuleDoc.apidoc_links
    epydoc.apidoc.ModuleDoc.init_submodule_groups
    epydoc.apidoc.ModuleDoc.select_variables
    epydoc.apidoc.ModuleDoc
    epydoc.apidoc.ValueDoc.summary_pyval_repr
    epydoc.apidoc.ValueDoc.apidoc_links
    epydoc.apidoc.ValueDoc.__setstate__
    epydoc.apidoc.ValueDoc.__getstate__
    epydoc.apidoc.ValueDoc.__repr__
    epydoc.apidoc.ValueDoc.pyval_repr
    epydoc.apidoc.ValueDoc
    epydoc.apidoc

Deserialize to `Object`::

    >>> obj = objectify('TESTOUT/epydoc.apidoc.APIDoc.merge_and_overwrite')
    >>> sorted(obj.keys())
    [u'args', u'docstring', u'fullname', u'is_method', u'lineno', u'params', 'src', u'type']
    >>> obj.args
    [u'self', u'other']
    >>> obj.is_method
    True
    >>> obj.lineno * 0
    0
    >>> obj.params
    [[u'ignore_hash_conflict', u'False']]
    >>> obj.name
    u'merge_and_overwrite'

Object parent::

    >>> parent = obj.get_parent()
    >>> parent.fullname
    u'epydoc.apidoc.APIDoc'
    >>> parent.type
    u'class'
    >>> parent.name
    u'APIDoc'
    >>> for name in sorted(parent.members):
    ...     print name
    epydoc.apidoc.APIDoc.__cmp__
    epydoc.apidoc.APIDoc.__hash__
    epydoc.apidoc.APIDoc.__init__
    epydoc.apidoc.APIDoc.__repr__
    epydoc.apidoc.APIDoc.apidoc_links
    epydoc.apidoc.APIDoc.is_detailed
    epydoc.apidoc.APIDoc.merge_and_overwrite
    epydoc.apidoc.APIDoc.pp
    epydoc.apidoc.APIDoc.pp
    epydoc.apidoc.APIDoc.specialize_to

Object children::

    >>> obj.get_children()
    []
    >>> for child in sorted(parent.get_children(), key=lambda d: d['fullname']):
    ...     print child.type, ' -> ', child.name
    function  ->  __cmp__
    function  ->  __hash__
    function  ->  __init__
    function  ->  __repr__
    function  ->  apidoc_links
    function  ->  is_detailed
    function  ->  merge_and_overwrite
    function  ->  pp
    function  ->  pp
    function  ->  specialize_to

Tidy up::

    >>> import shutil
    >>> shutil.rmtree('TESTOUT')

"""

__version__ = '0.0.1'

import os
import sys
from os.path import dirname, basename, abspath, splitext
from os.path import exists as pathexists, join as pathjoin, dirname, basename, abspath
import operator
import re
import json

from epydoc.docparser import parse_docs
from epydoc.apidoc import UNKNOWN, ModuleDoc, ClassDoc, RoutineDoc, ValueDoc

nulls = set([None, UNKNOWN])

def notnull(val):
    return not any(operator.is_(val, obj) for obj in nulls)

rx_dotted_name = re.compile(r'^[a-zA-Z_]+[a-zA-Z_.]*$')

def valid_dotted_name(name):
    return bool(rx_dotted_name.match(name))

__all__ = [
    'Parser', 'Object',
    'parsed', 'flattened', 'pprint', 'objectify',
]

def parsed(module_or_filename):
    return Parser().parse(module_or_filename)

def flattened(module_or_filename):
    return Parser().flatten(module_or_filename)

def pprint(module_or_filename, out=sys.stdout):
    Parser().pprint(module_or_filename, out)

def objectify(json_file):
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

    def iterparse(self, apidoc, parent_type=None):
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
            children = (self.iterparse(val.value, parent_type=apitype) for val in vals)
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

    def pprint(self, module_or_filename, out):
        def visit(iterable, indent=0):
            for info, children in iterable:
                s = ' ' * indent + info['fullname']
                if info['type'] == 'function':
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
                    s += '(%s)' % ', '.join(args)
                doc = info.get('docstring')
                if doc:
                    if '"' in doc:
                        quote = "'''"
                    else:
                        quote = '"""'
                    s += '\n' + ' ' * (indent+4) + quote + doc[:50]
                    if len(doc) > 50:
                        s += '...'
                    s += quote
                out.write(s+'\n')
                for child in children:
                    visit(child, indent+4)
        visit(self.iterparse(module_or_filename))


if __name__ == '__main__':
    import doctest
    doctest.testmod()

