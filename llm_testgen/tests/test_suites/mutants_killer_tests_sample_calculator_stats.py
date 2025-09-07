import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, call
import runpy
import importlib

# Add the tests/source directory to Python path
current_dir = Path(__file__).parent
source_dir = current_dir.parent / "source"
sys.path.insert(0, str(source_dir))

# We will import the module inside the test function to control the import context.

class TestKillerMutants:
    """Killer tests for surviving mutants."""

    def test_kill_mutant_main_guard_inversion_on_import(self, monkeypatch):
        """
        Kills mutants that invert the `if __name__ == '__main__':` guard.

        This test asserts that the example usage block (which contains print statements)
        does NOT execute when the module is imported, which is the correct behavior
        for the original implementation.

        The surviving mutants (mutant_sample_calculator_stats_23.py and
        mutant_sample_calculator_stats_36.py) invert this guard, causing the
        `__main__` block to execute when the module is imported. This will lead
        to `sys.stdout.write` being called, causing this test to fail on the mutants.
        """
        # Mock sys.stdout.write to capture any output that would normally go to the console.
        mock_stdout_write = Mock()
        monkeypatch.setattr(sys.stdout, 'write', mock_stdout_write)

        # Ensure the module is not already in sys.modules from previous imports
        # (e.g., from the existing test suite), so we get a fresh import.
        module_name = "sample_calculator_stats"
        if module_name in sys.modules:
            del sys.modules[module_name]

        # Perform the import. This is the point where the `if __name__ == '__main__':`
        # condition is evaluated in the module's top-level code.
        import sample_calculator_stats as fresh_module

        # Assert that sys.stdout.write was NOT called.
        # If it was called, it means the `__main__` block executed, which is incorrect
        # when the module is imported (i.e., `__name__` is not `'__main__'`).
        assert mock_stdout_write.call_count == 0, \
            "The `if __name__ == '__main__':` block should not execute when the module is imported. " \
            "This indicates a mutation in the main guard condition."

        # Optionally, verify that the functions from the module are still accessible and functional.
        # This ensures the module was imported correctly and is usable, beyond just the main guard.
        result, error = fresh_module.calculator(10, 'add', 5)
        assert error is None
        assert result == 15

        result, error = fresh_module.statistics_calculator([1, 2, 3], 'mean')
        assert error is None
        assert result == 2.0