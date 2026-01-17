"""Test module A for multi-module connection testing."""
from tests.test_data import module_b, module_c


def func_a():
    """Function in module A."""
    module_b.func_b()
    module_c.func_c1()


def func_a2():
    """Another function in module A."""
    pass
