"""Test module for aliased imports."""
from tests.test_data import module_a as ma
from tests.test_data import module_b as mb


def use_aliases():
    """Uses aliased imports."""
    ma.func_a()
    mb.func_b()
