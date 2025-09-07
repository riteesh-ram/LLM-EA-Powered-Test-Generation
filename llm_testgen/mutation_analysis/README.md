# Standalone Mutation Analysis System

This system provides comprehensive mutation score analysis for individual test files using the existing `mutants_validation` components. It reuses the proven implementations for mutant generation, testing, and score calculation while maintaining complete independence from the main pipeline.

## Overview

The standalone mutation analysis system leverages the existing modular components:
- **MutantGenerator**: Generates mutants using MutPy from `mutants_validation/mutant_generator.py`
- **MutantTester**: Tests individual mutants against test suites from `mutants_validation/mutant_tester.py`  
- **MutationScoreCalculator**: Calculates scores and generates reports from `mutants_validation/mutation_score_calculator.py`

## Key Features

### 🔄 **Reuses Existing Components**
- Uses proven `MutantGenerator` for reliable mutant generation
- Leverages `MutantTester` for consistent testing methodology
- Utilizes `MutationScoreCalculator` for standardized scoring

### 📁 **Proper File Organization**
- **Mutants Storage**: `mutants_validation/generated_mutants/` (same as pipeline)
- **Results Storage**: `test_results/` with `analysis_` prefix to distinguish from pipeline results
- **Independence**: No interference with existing pipeline operations

### 🎯 **Comprehensive Analysis**
- Multiple mutation types: AOD, AOR, ASR, LCR, ROR, BCR, COD, COI, CRP, SIR
- Detailed CSV reports with individual mutant results
- Summary reports with interpretation and recommendations
- Progress tracking and status updates

## Usage

### Basic Command
```bash
python mutation_analysis/run_mutation_analysis.py <test_file_name>
```

### Examples
```bash
# Analyze LLM-generated test
python mutation_analysis/run_mutation_analysis.py llm_generated_test_sample_number

# Analyze Pynguin-generated test  
python mutation_analysis/run_mutation_analysis.py pynguin_generated_test_sample_utility

# Analyze custom test file
python mutation_analysis/run_mutation_analysis.py my_custom_test_file
```

## File Structure and Integration

### Input Files
- **Test Files**: Located in `tests/test_suites/`
- **Source Files**: Located in `tests/source/`
- **Auto-detection**: Automatically detects source module from test file imports

### Output Files
- **Mutants**: `mutants_validation/generated_mutants/mutant_<module>_*.py`
- **CSV Results**: `test_results/analysis_mutation_test_results_<module>_<timestamp>.csv`
- **Summary**: `test_results/analysis_mutation_summary_<module>_<timestamp>.txt`

### Integration with Existing Pipeline
- **No Conflicts**: Uses `analysis_` prefix to avoid overwriting pipeline results
- **Same Storage**: Mutants stored in same location as pipeline for consistency
- **Independent Operation**: Can run simultaneously with pipeline without interference

## Technical Implementation

### Component Integration
```python
# Uses existing components with proper initialization
generator = MutantGenerator(source_module, logger=None)
tester = MutantTester(source_module, logger=None)  
calculator = MutationScoreCalculator(source_module, logger=None)

# Configures output paths for analysis results
calculator.results_csv_path = test_results_dir / f"analysis_mutation_test_results_{module}_{timestamp}.csv"
calculator.summary_path = test_results_dir / f"analysis_mutation_summary_{module}_{timestamp}.txt"
```

### Working Directory Management
- Runs from `llm_testgen` directory (required by existing components)
- No directory changes needed (components expect this working directory)
- Automatic path resolution for all file operations

## Mutation Score Interpretation

### Score Ranges
- **≥85%**: EXCELLENT - Test suite is highly effective
- **70-84%**: GOOD - Test suite is effective  
- **50-69%**: MODERATE - Test suite needs improvement
- **<50%**: POOR - Test suite needs significant improvement

### Mutant Categories
- **Killed Mutants**: Tests successfully detected the mutation (good)
- **Surviving Mutants**: Tests passed despite mutation (needs more tests)
- **Problematic Mutants**: Syntax errors or test execution issues (excluded from score)

## Output Analysis

### CSV Report Columns
- `file_name`: Mutant file name
- `file_type`: "original" or "mutant"
- `status`: "PASS", "FAIL", "TIMEOUT", "ERROR"
- `num_tests`: Total number of tests executed
- `num_pass`: Number of tests that passed
- `num_fail`: Number of tests that failed
- `execution_time`: Time taken to run tests
- `error_msg`: Any error messages

### Summary Report Content
- Module information and file paths
- Total counts for each mutant category
- Final mutation score percentage
- Timestamp and execution details
- Path to detailed CSV results

## Requirements

### Dependencies
- Python 3.7+
- MutPy environment at `mutants_validation/mutpy_env/`
- pytest for test execution
- Existing test files in `tests/test_suites/`
- Source files in `tests/source/`

### Environment Setup
The system automatically uses the existing MutPy environment and component implementations. No additional setup required beyond the existing pipeline infrastructure.

## Troubleshooting

### Common Issues
1. **Component Import Errors**: Ensure running from `llm_testgen` directory
2. **Path Resolution**: Check that test and source files exist in expected locations
3. **MutPy Environment**: Verify `mutants_validation/mutpy_env/` is properly configured
4. **File Permissions**: Ensure write access to `test_results/` directory

### Debug Information
The system provides detailed logging of:
- Component initialization status
- File path resolution
- Mutant generation progress
- Testing execution status
- Score calculation details

## Best Practices

### For Accurate Results
- Ensure test files have proper imports for source modules
- Use descriptive test file names following existing conventions
- Run from `llm_testgen` directory for proper path resolution

### For Performance
- Consider test execution time when analyzing large test suites
- Monitor disk space usage in `mutants_validation/generated_mutants/`
- Use the progress indicators to track long-running analyses

### For Consistency
- Use the same naming conventions as the main pipeline
- Store results with `analysis_` prefix to maintain separation
- Follow existing file organization patterns
