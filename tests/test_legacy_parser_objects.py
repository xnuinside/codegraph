from codegraph import parser as legacy


def test_object_children_and_repr():
    parent = legacy._Object("parent", "file.py", 1, None)
    child = legacy.Function("child", "file.py", 2)
    parent._addchild("child", child)

    assert parent.children["child"] is child
    assert child.main is parent
    assert "parent" in repr(parent)
    assert "parent" in str(parent)


def test_class_methods_and_nesting():
    cls = legacy.Class("MyClass", [], "file.py", 1)
    method = legacy._nest_function(cls, "method", 2)
    async_method = legacy._nest_function(cls, "amethod", 3, async_f=True)
    nested_class = legacy._nest_class(cls, "Nested", 4)

    assert "method" in cls.methods
    assert "amethod" in cls.async_methods
    assert cls.children["Nested"] is nested_class
    assert method in cls.methods.values()
    assert async_method in cls.async_methods.values()


def test_import_add():
    imp = legacy.Import(["os"])
    imp.add("sys")
    assert "os" in imp.modules
    assert "sys" in imp.modules
