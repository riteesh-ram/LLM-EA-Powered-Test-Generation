# Enhanced Coverage Analysis System

A comprehensive standalone coverage analysis tool that provides detailed coverage metrics for individual test files.

## Features

- **Multiple Coverage Types**: Line, Branch, Function, and Conditional coverage
- **Focused Analysis**: Analyzes only the specific test file and its corresponding source module
- **Rich Reporting**: Both terminal and HTML coverage reports
- **Automatic Detection**: Automatically detects which source module a test file is testing
- **Independent Operation**: Completely separate from the main pipeline

## Coverage Types Explained

### 1. Line Coverage (Statement Coverage)
- **What it measures**: Which lines of code were executed during testing
- **Importance**: Basic metric showing how much of your code is tested
- **Output**: Percentage of lines executed + list of missed lines

### 2. Branch Coverage
- **What it measures**: Which code branches (if/else, loops, etc.) were taken
- **Importance**: Ensures all possible execution paths are tested
- **Output**: Percentage of branches covered + detailed branch analysis

### 3. Function Coverage
- **What it measures**: Which functions/methods were called during testing
- **Importance**: Ensures all functions are tested at least once
- **Output**: List of all functions and their coverage status

### 4. Conditional Coverage
- **What it measures**: Which conditional expressions were evaluated
- **Importance**: Ensures complex boolean logic is properly tested
- **Output**: Analysis of if statements, while loops, and boolean expressions

## Directory Structure

```
llm_testgen/
├── coverage_analysis/
│   ├── run_coverage_analysis.py    # Main coverage analysis script
│   ├── README.md                   # This documentation
│   ├── .coveragerc                 # Coverage configuration (auto-generated)
│   └── reports/                    # Coverage reports directory
│       ├── coverage_MODULE_TIMESTAMP.coverage     # Coverage data files
│       ├── coverage_MODULE_TIMESTAMP_html/        # HTML reports
│       └── htmlcov/                               # Default HTML directory
```

## Usage

### Basic Usage
```bash
python coverage_analysis/run_coverage_analysis.py <test_file_name>
```

### Examples

**Using just the test file name:**
```bash
python coverage_analysis/run_coverage_analysis.py llm_generated_test_sample_utility
```

**Using relative path:**
```bash
python coverage_analysis/run_coverage_analysis.py tests/test_suites/llm_generated_test_sample_number
```

**For pynguin tests:**
```bash
python coverage_analysis/run_coverage_analysis.py pynguin_generated_test_sample_calculator
```

## Output

### Terminal Output
The script provides comprehensive terminal output including:

1. **Initialization Info**: Project paths and setup confirmation
2. **File Detection**: Test file and source module identification
3. **Coverage Execution**: Real-time pytest execution with coverage
4. **Coverage Summary**: Line and branch coverage percentages
5. **Function Analysis**: List of all functions and their coverage
6. **Conditional Analysis**: Analysis of conditional statements
7. **Report Locations**: Paths to generated coverage files

### Generated Files

1. **Coverage Data File**: `.coverage` file with raw coverage data
2. **HTML Report**: Interactive HTML coverage report with detailed analysis
3. **Configuration File**: `.coveragerc` with enhanced coverage settings

## Technical Details

### Automatic Source Detection
The script automatically detects which source module a test file is testing by:
1. Analyzing import statements in the test file
2. Matching test file naming patterns
3. Looking for corresponding source files in `tests/source/`

### Coverage Configuration
Enhanced `.coveragerc` configuration includes:
- Branch coverage enabled
- Source directory specification
- Exclusion of test files and virtual environments
- Missing line reporting
- HTML report customization

### File Structure Requirements
- **Test Files**: Must be in `tests/test_suites/` or subdirectories
- **Source Files**: Must be in `tests/source/`
- **Virtual Environment**: Automatically detected and used if available

## Troubleshooting

### Common Issues

**File Not Found Error:**
```
FileNotFoundError: Test file not found: test_name.py
```
- Ensure the test file exists in `tests/test_suites/`
- Check the file name spelling
- Try using the full relative path

**Source Module Detection Failed:**
```
ValueError: Could not detect source module for test file
```
- Ensure the corresponding source file exists in `tests/source/`
- Check that the test file has proper import statements
- Verify the naming convention matches

**Import Errors During Testing:**
```
ModuleNotFoundError: No module named 'module_name'
```
- Ensure the source module is in `tests/source/`
- Check that `__init__.py` files exist if needed
- Verify the Python path is set correctly

### Debug Mode
For additional debugging information, you can examine:
- The generated `.coveragerc` file
- Coverage data files in `reports/` directory
- HTML reports for detailed line-by-line analysis

## Example Output

```
===============================================================================
ENHANCED COVERAGE ANALYSIS
===============================================================================
✓ Test file found: /path/to/tests/test_suites/llm_generated_test_sample_utility.py
✓ Source module detected: sample_utility (/path/to/tests/source/sample_utility.py)
✓ Coverage data file: /path/to/coverage_analysis/reports/coverage_sample_utility_20250120_143022.coverage
✓ HTML report directory: /path/to/coverage_analysis/reports/coverage_sample_utility_20250120_143022_html

==================================================
RUNNING ENHANCED COVERAGE ANALYSIS
==================================================
Command: python -m pytest tests/test_suites/llm_generated_test_sample_utility.py --cov=tests/source/sample_utility.py --cov-branch --cov-report=term-missing:skip-covered --cov-report=html:reports/coverage_sample_utility_20250120_143022_html --cov-config=coverage_analysis/.coveragerc -v --tb=short
Working directory: /path/to/llm_testgen
Coverage file: coverage_sample_utility_20250120_143022.coverage
Analyzing ONLY: /path/to/tests/source/sample_utility.py

==================================================
COVERAGE ANALYSIS RESULTS
==================================================
PYTEST OUTPUT:
------------------------------
============================= test session starts ==============================
collected 8 items

tests/test_suites/llm_generated_test_sample_utility.py::test_add_numbers PASSED
tests/test_suites/llm_generated_test_sample_utility.py::test_multiply_numbers PASSED
[... more test results ...]

---------- coverage: platform darwin, python 3.13.1-final-0 -----------
Name                          Stmts   Miss Branch BrPart  Cover   Missing
---------------------------------------------------------------------------
tests/source/sample_utility.py    45      0     12      0   100%
---------------------------------------------------------------------------
TOTAL                            45      0     12      0   100%

------------------------------------------------------------
DETAILED COVERAGE ANALYSIS
------------------------------------------------------------
📊 LINE AND BRANCH COVERAGE SUMMARY:
----------------------------------------
Name                          Stmts   Miss Branch BrPart  Cover   Missing
---------------------------------------------------------------------------
tests/source/sample_utility.py    45      0     12      0   100%
---------------------------------------------------------------------------
TOTAL                            45      0     12      0   100%

🔧 FUNCTION/METHOD COVERAGE ANALYSIS:
----------------------------------------
Found 8 functions/methods in sample_utility.py:
  • add_numbers() - Lines 1-5
  • multiply_numbers() - Lines 7-11
  • divide_numbers() - Lines 13-20
  • calculate_factorial() - Lines 22-28
  [... more functions ...]

🧠 CONDITIONAL COVERAGE ANALYSIS:
----------------------------------------
Found 6 conditional statements in sample_utility.py:
  • If at line 15
  • If at line 18
  • If at line 24
  • While at line 26
  [... more conditionals ...]

Branch coverage details are available in the HTML report.

==================================================
ENHANCED COVERAGE REPORT SUMMARY
==================================================
✓ Test file: llm_generated_test_sample_utility.py
✓ Source module: sample_utility.py
✓ Coverage types: Line + Branch + Function + Conditional
✓ Coverage data: /path/to/coverage_analysis/reports/coverage_sample_utility_20250120_143022.coverage
✓ HTML report: /path/to/coverage_analysis/reports/coverage_sample_utility_20250120_143022_html
✓ Open HTML report: file:///path/to/coverage_analysis/reports/coverage_sample_utility_20250120_143022_html/index.html
==================================================

🎉 Enhanced coverage analysis completed successfully!

Coverage types analyzed:
  ✅ Line Coverage
  ✅ Branch Coverage
  ✅ Function Coverage
  ✅ Conditional Coverage
```

## Dependencies

- Python 3.7+
- pytest
- pytest-cov
- coverage.py

Install dependencies:
```bash
pip install pytest pytest-cov coverage
```

## Integration Notes

This coverage analysis system is designed to be:
- **Independent**: Does not interfere with existing pipeline
- **Focused**: Analyzes only the specific test file being examined
- **Comprehensive**: Provides all major coverage types in one run
- **User-friendly**: Clear output and easy-to-understand reports
