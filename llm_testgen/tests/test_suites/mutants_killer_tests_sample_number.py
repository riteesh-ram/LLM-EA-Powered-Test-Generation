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

# Import the source module. This will be the *original* module.
# We import it to ensure it's available in the test environment,
# but for testing the __main__ block, we'll use runpy.
import sample_number

@pytest.fixture
def mock_print(monkeypatch):
    """
    Fixture to mock builtins.print and return a Mock instance.
    This allows capturing all calls to print for assertion.
    """
    mock = Mock()
    monkeypatch.setattr('builtins.print', mock)
    return mock

class TestKillerMutants:
    """Killer tests for surviving mutants."""

    def test_kill_mutant_main_block_sample_value_change(self, mock_print):
        """
        Kills mutant_sample_number_0.py and mutant_sample_number_1.py.

        These mutants modify the `sample` list within the
        `if __name__ == "__main__":` block, changing `-3` to `3` (or `+3`).
        The original code processes `-3` by skipping it, while the mutants
        process `3` as 'light work' and include it in the sum.

        This test executes the module as `__main__` and asserts on the exact
        sequence of print statements, which will differ between the original
        and the mutated versions.
        """
        # Arrange - mock_print is provided by the fixture

        # Act: Execute the module as if it were run from the command line.
        # This will trigger the `if __name__ == "__main__":` block in the original code.
        # runpy.run_module executes the module's top-level code in a fresh namespace.
        runpy.run_module('sample_number', run_name='__main__')

        # Assert: Check the print calls.
        # Expected output for the original `sample = [0, 1, -3, 4, 7, 2, 9]`
        expected_calls_original = [
            call("Zero encountered – adding nothing."),
            call("Value 0: do nothing"),
            call("Value 1: light work"),
            call("Skipping negative value -3"),  # This line is key for killing the mutant
            call("Value 4: moderate work"),
            call("Value 7: heavy lifting"),
            call("Value 2: light work"),
            call("Value 9: heavy lifting"),
            call("Sum of positive numbers: 23")  # The sum will also differ (23 vs 29 for mutant)
        ]

        assert mock_print.call_args_list == expected_calls_original

    def test_kill_mutant_main_block_guard_inversion(self, mock_print):
        """
        Kills mutant_sample_number_14.py and mutant_sample_number_8.py.

        These mutants invert the condition of `if __name__ == "__main__":`
        to `if __name__ != '__main__':` or `if not (__name__ == '__main__'):`.
        This means that when the script is run directly, the code inside this
        block (which calls `classify_numbers`) will *not* execute in the mutant.

        This test executes the module as `__main__`. The original code will
        execute the block and produce print output. The mutant code will
        skip the block and produce no print output.
        """
        # Arrange - mock_print is provided by the fixture

        # Act: Execute the module as if it were run from the command line.
        # This will trigger the `if __name__ == "__main__":` block in the original.
        runpy.run_module('sample_number', run_name='__main__')

        # Assert:
        # For the original code, `classify_numbers` is called, and print statements are made.
        # Therefore, `mock_print.call_count` should be greater than 0.
        assert mock_print.call_count > 0

        # For the mutant, the `if __name__ == "__main__":` block is skipped,
        # so `mock_print.call_count` would be 0, causing the test to fail.

        # For added robustness, assert on specific calls that are guaranteed to be present
        # if the __main__ block executes correctly.
        assert mock_print.call_args_list[0] == call("Zero encountered – adding nothing.")
        assert mock_print.call_args_list[-1] == call("Sum of positive numbers: 23")