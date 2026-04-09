"""Test module B for multi-module connection testing."""

from tests.test_data import module_c


def func_b():
    """Function in module B."""
    module_c.func_c2()


def func_b2():
    """Another function in module B."""
    pass
