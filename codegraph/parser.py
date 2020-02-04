# 'cut of' code from pythons pyclrb with some additionals
import io
import tokenize
from token import NAME, DEDENT, NL
from typing import List, Text

__all__ = ["Class", "Function"]


class _Object:
    """Information about Python class or function."""
    def __init__(self, name: Text, file: Text, lineno: int, parent: object):
        self.name = name
        self.file = file
        self.lineno = lineno
        self.parent = parent if parent else object
        self.children = {}
        self.endno = None

    def _addchild(self, name, obj):
        self.children[name] = obj
        obj.main = self

    def __repr__(self):
        return f"{self.name} <{self.__class__.__name__}: Parent {self.parent}>"

    def __str__(self):
        return f"{self.name} <{self.__class__.__name__}>"


class Import(object):
    def __init__(self, modules: List):
        self.modules = set()
        for module in modules:
            self.modules.add(module)

    def add(self, module):
        self.modules.add(module)


class Function(_Object):
    "Information about a Python function, including methods."
    def __init__(self, name, file, lineno, parent=None):
        _Object.__init__(self, name, file, lineno, parent)


class AsyncFunction(_Object):
    "Information about a Python async function, including methods."
    def __init__(self, name, file, lineno, parent=None):
        _Object.__init__(self, name, file, lineno, parent)


class Class(_Object):
    """Information about a Python class."""
    def __init__(self, name, super, file, lineno, parent=None):
        _Object.__init__(self, name, file, lineno, parent)
        self.super = [] if super is None else super
        self.methods = {}
        self.async_methods = {}

    def _addmethod(self, name, newfunc):
        self.methods[name] = newfunc

    def _add_async_method(self, name, newfunc):
        self.async_methods[name] = newfunc


def _nest_function(ob, func_name, lineno, async_f=False):
    "Return a Function after nesting within ob."
    newfunc = Function(func_name, ob.file, lineno, ob)
    ob._addchild(func_name, newfunc)
    if isinstance(ob, Class):
        if not async_f:
            ob._addmethod(func_name, newfunc)
        else:
            ob._add_async_method(func_name, newfunc)
    return newfunc


def _nest_class(ob, class_name, lineno, super=None):
    "Return a Class after nesting within ob."
    newclass = Class(class_name, super, ob.file, lineno, ob)
    ob._addchild(class_name, newclass)
    return newclass


def create_objects_array(fname, source):
    """ Return an object list for a particular module. """
    tree = []
    f = io.StringIO(source)

    stack = []

    g = tokenize.generate_tokens(f.readline)
    try:
        new_lines = 0
        imports = None
        cur_func = None
        for tokentype, token, start, _end, _line in g:
            if tokentype == DEDENT:
                lineno, thisindent = start
                # Close previous nested classes and defs.
                while stack and stack[-1][1] >= thisindent:
                    if isinstance(stack[-1][0], _Object):
                        if getattr(stack[-1][0], 'main', None):
                            stack[-1][0].endno = lineno - 1 - new_lines
                        else:
                            stack[-1][0].endno = lineno -1 - new_lines
                    del stack[-1]
                else:
                    if tree:
                        tree[-1].endno = lineno - 1 - new_lines
                new_lines = 0
            elif tokentype == NL:
                new_lines += 1

            elif token == 'import':
                modules = [_line.replace('\n', '').split('import ')[1]]
                if not imports:
                    imports = Import(modules)
                else:
                    for module in modules:
                        imports.add(module)
            elif token == 'from':
                modules = [_line.replace('\n', '').split('from ')[1].replace(' import ', '.')]
                if not imports:
                    imports = Import(modules)
                else:
                    for module in modules:
                        imports.add(module)
            elif token == 'async':
                new_lines = 0
                lineno, thisindent = start
                # Close previous nested classes and defs.
                while stack and stack[-1][1] >= thisindent:
                    del stack[-1]
                # next will be def
                _, _, _ = next(g)[0:3]
                # we need method name
                tokentype, func_name, start = next(g)[0:3]
                if tokentype != NAME:
                    continue  # Skip def with syntax error.
                cur_func = None
                if stack:
                    cur_obj = stack[-1][0]
                    cur_func = _nest_function(cur_obj, func_name, lineno, async_f=True)
                    cur_obj.endno = lineno - new_lines
                else:
                    tree.append(AsyncFunction(func_name, fname, lineno))
                stack.append((cur_func, thisindent))
            elif token == 'def':
                new_lines = 0
                lineno, thisindent = start
                # Close previous nested classes and defs.
                while stack and stack[-1][1] >= thisindent:
                    del stack[-1]
                tokentype, func_name, start = next(g)[0:3]
                if tokentype != NAME:
                    continue  # Skip def with syntax error.
                if stack:
                    cur_obj = stack[-1][0]
                    cur_func = _nest_function(cur_obj, func_name, lineno)
                    cur_obj.endno = lineno - new_lines
                else:
                    cur_func = Function(func_name, fname, lineno)
                    tree.append(cur_func)
                if cur_func:
                    stack.append((cur_func, thisindent))
            elif token == 'class':
                new_lines = 0
                lineno, thisindent = start
                # Close previous nested classes and defs.
                while stack and stack[-1][1] >= thisindent:
                    del stack[-1]
                tokentype, class_name, start = next(g)[0:3]

                if tokentype != NAME:
                    continue
                inherit = None

                if stack:
                    cur_obj = stack[-1][0]
                    cur_class = _nest_class(
                            cur_obj, class_name, lineno, inherit)
                    cur_obj.endno = lineno - new_lines
                else:
                    cur_class = Class(class_name, inherit,
                                      fname, lineno)
                    tree.append(cur_class)
                stack.append((cur_class, thisindent))

    except StopIteration:
        pass

    f.close()
    if imports:
        tree.append(imports)
    return tree

