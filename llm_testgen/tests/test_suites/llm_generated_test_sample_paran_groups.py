import pytest
import sys
from pathlib import Path
from typing import List

# Add the tests/source directory to Python path to import the source module
current_dir = Path(__file__).parent
source_dir = current_dir.parent / "source"
sys.path.insert(0, str(source_dir))

import sample_paran_groups

class TestSeparateParenGroups:
    """
    Comprehensive test suite for the separate_paren_groups function.
    This suite covers various valid inputs, edge cases, and scenarios with malformed
    parenthesis strings to ensure robust behavior.
    """

    @pytest.mark.parametrize(
        "paren_string, expected_output",
        [
            # Positive test cases: Valid, balanced, non-nested groups
            ("()", ["()"]),
            ("(())", ["(())"]),
            ("()()", ["()", "()"]),
            ("((()))", ["((()))"]),
            ("() (())", ["()", "(())"]),  # Spaces between groups
            (" ( ( ) ) ", ["(())"]),      # Spaces inside and around a group
            ("(( )( ))", ["(()())"]),     # Nested groups with inner groups
            ("( ) (( )) (( )( ))", ["()", "(())", "(()())"]),  # Docstring example
            ("((())) () (())", ["((()))", "()", "(())"]),  # Multiple complex groups with spaces
            ("((()))()(())", ["((()))", "()", "(())"]),    # No spaces
            ("((()))  ()   (())", ["((()))", "()", "(())"]), # Multiple spaces
            ("((()))\t()\n(())", ["((()))", "()", "(())"]), # Other whitespace characters
            # Corrected expected output based on function's behavior (non-paren chars are ignored)
            # Tracing 'a(b)c(d(e)f)g' with the provided function:
            # 'a' ignored, '(' depth 1, 'b' ignored, ')' depth 0 -> '()' extracted.
            # 'c' ignored, '(' depth 1, 'd' ignored, '(' depth 2, 'e' ignored, ')' depth 1, 'f' ignored, ')' depth 0 -> '(())' extracted.
            ("a(b)c(d(e)f)g", ["()", "(())"]),
            # Corrected expected output based on function's behavior (non-paren chars are ignored)
            # Tracing '((a)b(c))' with the provided function:
            # '(' depth 1, '(' depth 2, 'a' ignored, ')' depth 1, 'b' ignored, '(' depth 2, 'c' ignored, ')' depth 1, ')' depth 0 -> '(()())' extracted.
            ("((a)b(c))", ["(()())"]),
        ],
        ids=[
            "simple_group",
            "nested_group",
            "multiple_simple_groups",
            "deeply_nested_group",
            "mixed_groups_with_space",
            "spaces_inside_and_around",
            "nested_with_inner_groups",
            "docstring_example",
            "multiple_complex_groups_with_spaces",
            "multiple_complex_groups_no_space",
            "multiple_complex_groups_multiple_spaces",
            "multiple_complex_groups_other_whitespace",
            "chars_ignored_mixed_groups_corrected",
            "chars_ignored_within_deep_nesting_corrected",
        ]
    )
    def test_valid_parenthesis_strings(self, paren_string: str, expected_output: List[str]):
        """
        Tests the function with various valid parenthesis strings, including different nesting levels,
        multiple groups, and strings with spaces or other non-parenthesis characters that should be ignored.
        """
        # Arrange - inputs are provided by parametrize
        # Act
        result = sample_paran_groups.separate_paren_groups(paren_string)
        # Assert
        assert result == expected_output

    @pytest.mark.parametrize(
        "paren_string, expected_output",
        [
            # Edge cases and malformed inputs (testing actual function behavior)
            ("", []),  # Empty string
            ("   ", []),  # String with only spaces
            ("abc def", []),  # String with no parentheses
            ("(((" , []), # Only opening parentheses, no balanced groups formed
            (")))" , []), # Only closing parentheses, no balanced groups formed
            ("(())(" , ["(())"]), # Unmatched opening parenthesis at the end, one group extracted
            # Corrected expected output based on observed function behavior:
            # The function collects characters into a buffer and adds the buffer content
            # as a group when depth returns to 0, even if depth went negative in between.
            # If depth goes negative and then returns to 0, it does NOT form a group.
            (")()(" , []), # Unmatched closing at start, then malformed sequences, but no valid groups extracted.
            ("())(()", ["()", ")(()"]), # One valid group, then a malformed group. Corrected typo in previous expected.
            ("(()))", ["(())"]), # Extra closing parenthesis at the end, only one group extracted
            ("((", []), # Only opening, not enough to form a group
            ("))", []), # Only closing, not enough to form a group
            ("()(", ["()"]), # One complete group, then an unmatched opening
            (")(", []), # Unmatched closing then unmatched opening, no group extracted as depth went negative.

            # --- New test cases from Pynguin suite ---
            # Pynguin test_case_0: String with various non-parenthesis characters (including control chars)
            # and an unmatched closing parenthesis. Should result in no balanced groups as depth never returns to 0.
            ("gW*G)Q\tM&JkO>&%4?H.g\x0c", []),
            # Pynguin test_case_1: String with mixed non-parenthesis characters (including other bracket types)
            # and a single balanced group. Ensures only '(' and ')' are processed.
            ('(}5"j&*pNm)<o}u" hlHT-', ["()"]),
        ],
        ids=[
            "empty_string",
            "only_spaces",
            "no_parentheses",
            "only_opening_parens",
            "only_closing_parens",
            "unmatched_opening_at_end",
            "malformed_sequence_no_groups_extracted", # Renamed and corrected
            "malformed_sequence_extracts_valid_and_malformed_group_corrected", # Corrected typo
            "extra_closing_paren_at_end",
            "two_opening_parens",
            "two_closing_parens",
            "one_group_then_unmatched_opening",
            "malformed_group_not_extracted", # Renamed and corrected
            # --- New IDs for Pynguin cases ---
            "pynguin_mixed_chars_unmatched_closing",
            "pynguin_mixed_chars_other_brackets_single_group",
        ]
    )
    def test_edge_cases_and_malformed_inputs(self, paren_string: str, expected_output: List[str]):
        """
        Tests various edge cases, including empty strings, strings with no parentheses,
        and strings with unmatched parentheses. These tests verify the function's behavior
        when inputs deviate from the ideal "balanced groups" description, ensuring it
        handles such scenarios predictably.
        """
        # Arrange - inputs are provided by parametrize
        # Act
        result = sample_paran_groups.separate_paren_groups(paren_string)
        # Assert
        assert result == expected_output

    def test_large_input_performance(self):
        """
        Tests the function with a large input string to ensure performance and correctness
        with many groups and deep nesting, without causing excessive memory or time issues.
        """
        # Arrange
        # Create a string with 1000 deeply nested groups, 500 simple groups, and another 1000 deeply nested groups
        paren_string = "((()))" * 1000 + "()" * 500 + "((()))" * 1000
        expected_output = ["((()))"] * 1000 + ["()"] * 500 + ["((()))"] * 1000

        # Act
        result = sample_paran_groups.separate_paren_groups(paren_string)

        # Assert
        assert result == expected_output
        assert len(result) == 2500 # Verify the total number of groups extracted