# 'cut of' code from pythons pyclrb with some additionals
import io
import tokenize
from token import DEDENT, NAME, NEWLINE, NL
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


def create_objects_array(fname, source):  # noqa: C901
    # todo: need to do optimization
    """Return an object list for a particular module."""
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
                        if getattr(stack[-1][0], "main", None):
                            stack[-1][0].endno = lineno - 1 - new_lines
                        else:
                            stack[-1][0].endno = lineno - 1 - new_lines
                    del stack[-1]
                else:
                    if tree:
                        tree[-1].endno = lineno - 1 - new_lines
                new_lines = 0
            elif tokentype == NL:
                new_lines += 1

            elif token == "import":
                modules = [_line.replace("\n", "").split("import ")[1]]
                if not imports:
                    imports = Import(modules)
                else:
                    for module in modules:
                        imports.add(module)
            elif token == "from":
                # Parse "from X import a, b, c" into ["X.a", "X.b", "X.c"]
                # Also handles multi-line imports with parentheses
                # Collect tokens to build base module path
                base_parts = []
                for tokentype2, token2, start2, _end2, _line2 in g:
                    if token2 == "import":
                        break
                    if tokentype2 == NAME:
                        base_parts.append(token2)
                    elif token2 == ".":
                        base_parts.append(".")

                base_module = "".join(base_parts)

                # Collect imported names (handle parentheses for multi-line)
                imported_names = []
                in_parens = False
                current_name = []
                alias = None

                for tokentype2, token2, start2, _end2, _line2 in g:
                    if token2 == "(":
                        in_parens = True
                        continue
                    if token2 == ")":
                        break
                    if token2 == "," or (tokentype2 == NEWLINE and not in_parens):
                        if current_name:
                            name = "".join(current_name)
                            if alias:
                                name = f"{name} as {alias}"
                                alias = None
                            imported_names.append(name)
                            current_name = []
                        if tokentype2 == NEWLINE and not in_parens:
                            break
                        continue
                    if token2 == "as":
                        # Next NAME token is the alias
                        for tokentype3, token3, _, _, _ in g:
                            if tokentype3 == NAME:
                                alias = token3
                                break
                            if token3 in (",", ")", "\n"):
                                break
                        continue
                    if tokentype2 == NAME:
                        current_name.append(token2)
                    elif token2 == ".":
                        current_name.append(".")
                    if tokentype2 == NL:
                        continue

                # Don't forget the last name
                if current_name:
                    name = "".join(current_name)
                    if alias:
                        name = f"{name} as {alias}"
                    imported_names.append(name)

                # Build full module paths
                modules = [f"{base_module}.{name}" for name in imported_names if name]

                if not imports:
                    imports = Import(modules)
                else:
                    for module in modules:
                        imports.add(module)
            elif token == "async":
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
            elif token == "def":
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
            elif token == "class":
                new_lines = 0
                lineno, thisindent = start
                # Close previous nested classes and defs.
                while stack and stack[-1][1] >= thisindent:
                    del stack[-1]
                tokentype, class_name, start = next(g)[0:3]

                if tokentype != NAME:
                    continue

                # Parse base classes: class Name(Base1, Base2):
                inherit = []
                current_base = []
                in_parens = False

                for tokentype2, token2, start2, _end2, _line2 in g:
                    if token2 == "(":
                        in_parens = True
                        continue
                    if token2 == ")":
                        if current_base:
                            inherit.append("".join(current_base))
                        break
                    if token2 == ":":
                        if current_base:
                            inherit.append("".join(current_base))
                        break
                    if not in_parens:
                        if token2 == ":":
                            break
                        continue
                    if token2 == ",":
                        if current_base:
                            inherit.append("".join(current_base))
                            current_base = []
                        continue
                    if tokentype2 == NAME:
                        current_base.append(token2)
                    elif token2 == ".":
                        current_base.append(".")
                    if tokentype2 == NL:
                        continue

                if stack:
                    cur_obj = stack[-1][0]
                    cur_class = _nest_class(cur_obj, class_name, lineno, inherit)
                    cur_obj.endno = lineno - new_lines
                else:
                    cur_class = Class(class_name, inherit, fname, lineno)
                    tree.append(cur_class)
                stack.append((cur_class, thisindent))

    except StopIteration:
        pass

    f.close()
    if imports:
        tree.append(imports)
    return tree
