import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, call
import runpy
import importlib
import time # Import time for potential mocking, though not directly used in this specific killer test

# Add the tests/source directory to Python path to import the source module
current_dir = Path(__file__).parent
source_dir = current_dir.parent / "source"
sys.path.insert(0, str(source_dir))

import sample_timing # Import the module to test its __all__ attribute

# Fixture for mocking builtins.print (included for consistency with existing test suite,
# though not directly used by the current killer test)
@pytest.fixture
def mock_print(monkeypatch):
    """
    Fixture to mock builtins.print and capture its calls for assertion.
    """
    mock = Mock()
    monkeypatch.setattr('builtins.print', mock)
    return mock

class TestKillerMutants:
    """Killer tests for surviving mutants."""

    def test_kill_mutant_all_variable_content(self):
        """
        Kills mutants where the `__all__` variable in `sample_timing` is modified
        from its original, intended state.

        This test specifically targets mutations that:
        1. Delete the `__all__` attribute entirely.
        2. Change `__all__` to an empty list (`[]`).
        3. Modify `__all__` to include items other than, or in addition to,
           "work_in_progress".

        The original implementation explicitly defines `__all__ = ["work_in_progress"]`.
        This test asserts that this exact definition is maintained.
        """
        # Assert that the module has the __all__ attribute
        assert hasattr(sample_timing, '__all__'), \
            "Mutant deleted the __all__ attribute from sample_timing module."

        # Assert that __all__ contains exactly "work_in_progress"
        expected_all = ["work_in_progress"]
        assert sample_timing.__all__ == expected_all, \
            (f"Mutant changed __all__ from {expected_all} to {sample_timing.__all__}. "
             "This could be due to an empty list, extra items, or different items.")