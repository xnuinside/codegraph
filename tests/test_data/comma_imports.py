"""Test module for comma-separated imports."""

from tests.test_data import module_a, module_b, module_c


def use_all():
    """Uses functions from multiple modules."""
    module_a.func_a()
    module_b.func_b()
    module_c.func_c1()
