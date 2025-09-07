import pytest
import sys
from pathlib import Path

# Add the tests/source directory to Python path to import the source module
current_dir = Path(__file__).parent
source_dir = current_dir.parent / "source"
sys.path.insert(0, str(source_dir))

import sample_timing

from unittest.mock import MagicMock
import time

# Fixture for mocking builtins.print
@pytest.fixture
def mock_print(monkeypatch):
    """
    Fixture to mock builtins.print and capture its calls for assertion.
    """
    mock = MagicMock()
    monkeypatch.setattr('builtins.print', mock)
    return mock

# Test 1: Basic functionality - prints start, yields, prints end with correct time
def test_work_in_progress_basic_timing(mock_print, monkeypatch):
    """
    Verifies that `work_in_progress` correctly prints the start message,
    allows code execution, and then prints the end message with the calculated
    duration formatted to two decimal places.
    """
    # Arrange
    start_time = 100.0
    end_time = 101.234567
    expected_duration = end_time - start_time
    desc = "Performing a task"

    # Mock time.time to return specific values for start and end
    mock_time = MagicMock(side_effect=[start_time, end_time])
    monkeypatch.setattr(time, 'time', mock_time)

    # Act
    with sample_timing.work_in_progress(desc):
        # Simulate some work being done
        pass

    # Assert
    # Ensure print was called twice
    assert mock_print.call_count == 2

    # Verify the first print call (start message)
    mock_print.assert_any_call(desc + "... ", end='', flush=True)

    # Verify the second print call (end message with formatted time)
    expected_end_message = f"done. ({expected_duration:.2f}s)"
    mock_print.assert_any_call(expected_end_message)

    # Ensure time.time was called exactly twice
    assert mock_time.call_count == 2

# Test 2: Exception handling - prints start, re-raises exception, does not print end
def test_work_in_progress_with_exception(mock_print, monkeypatch):
    """
    Ensures that if an exception occurs within the `work_in_progress` block,
    the start message is printed, the exception is re-raised, and the
    "done" message is NOT printed.
    """
    # Arrange
    class CustomTestError(Exception):
        pass

    start_time = 200.0
    desc = "Failing task"

    # Mock time.time to return a value only for the start, as the end time
    # should not be recorded if an exception occurs before the yield completes.
    mock_time = MagicMock(side_effect=[start_time])
    monkeypatch.setattr(time, 'time', mock_time)

    # Act & Assert
    # Expect the CustomTestError to be raised
    with pytest.raises(CustomTestError, match="Something went wrong"):
        with sample_timing.work_in_progress(desc):
            raise CustomTestError("Something went wrong")

    # Verify print calls: only the start message should have been printed
    assert mock_print.call_count == 1
    mock_print.assert_called_once_with(desc + "... ", end='', flush=True)

    # Verify time.time calls: only once (for `begin_time`)
    assert mock_time.call_count == 1

# Test 3: Different descriptions (parametrized)
@pytest.mark.parametrize("desc_input, expected_start_output", [
    ("Short task", "Short task... "),
    ("A very long and descriptive task name that should still work correctly", "A very long and descriptive task name that should still work correctly... "),
    ("", "... "),  # Edge case: empty description
])
def test_work_in_progress_different_descriptions(mock_print, monkeypatch, desc_input, expected_start_output):
    """
    Tests `work_in_progress` with various description strings, including an empty string,
    to ensure the start message is correctly formatted.
    """
    # Arrange
    start_time = 300.0
    end_time = 300.5
    expected_duration = end_time - start_time

    # Mock time.time for consistent duration
    mock_time = MagicMock(side_effect=[start_time, end_time])
    monkeypatch.setattr(time, 'time', mock_time)

    # Act
    with sample_timing.work_in_progress(desc_input):
        pass

    # Assert
    assert mock_print.call_count == 2
    mock_print.assert_any_call(expected_start_output, end='', flush=True)
    expected_end_message = f"done. ({expected_duration:.2f}s)"
    mock_print.assert_any_call(expected_end_message)

# Test 4: Zero execution time
def test_work_in_progress_zero_time(mock_print, monkeypatch):
    """
    Tests `work_in_progress` when the execution time is effectively zero,
    ensuring the time is formatted as '0.00s'.
    """
    # Arrange
    fixed_time = 400.0
    desc = "Instant task"

    # Mock time.time to return the same value for both calls
    mock_time = MagicMock(side_effect=[fixed_time, fixed_time])
    monkeypatch.setattr(time, 'time', mock_time)

    # Act
    with sample_timing.work_in_progress(desc):
        pass

    # Assert
    assert mock_print.call_count == 2
    mock_print.assert_any_call(desc + "... ", end='', flush=True)
    mock_print.assert_any_call("done. (0.00s)") # Expect 0.00s for zero duration

# Test 5: Floating point precision and rounding
def test_work_in_progress_floating_point_rounding(mock_print, monkeypatch):
    """
    Tests that the time displayed is correctly formatted to two decimal places,
    including proper rounding behavior.
    """
    # Arrange
    start_time = 500.0
    end_time_with_rounding_up = 500.128
    expected_duration_rounded_up = end_time_with_rounding_up - start_time # 0.128 -> 0.13

    desc = "Rounding test"

    # Mock time.time for a specific rounding scenario
    mock_time = MagicMock(side_effect=[start_time, end_time_with_rounding_up])
    monkeypatch.setattr(time, 'time', mock_time)

    # Act
    with sample_timing.work_in_progress(desc):
        pass

    # Assert
    assert mock_print.call_count == 2
    mock_print.assert_any_call(desc + "... ", end='', flush=True)
    mock_print.assert_any_call(f"done. ({expected_duration_rounded_up:.2f}s)")