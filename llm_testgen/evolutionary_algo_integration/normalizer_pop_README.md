# normalizer.py Module

This module provides an enhanced normalization pipeline for preparing LLM-generated tests as Pynguin-compatible seed tests. It is a critical component for bridging human-like test generation with evolutionary algorithms, ensuring that seed tests are simple, direct, and compatible with Pynguin's requirements.

---

## Key Features
- **Raw Test Collection:** Scans for raw LLM-generated test files (pattern: `test_*.py`), excluding already normalized seed files.
- **Function Call Extraction:** Identifies calls to target functions, supporting both direct and attribute references.
- **Parametrization Expansion:** Expands parametrized tests into individual seed cases, mapping parameters dynamically.
- **Variable Resolution:** Resolves variable assignments within test functions to extract literal values and supported collections.
- **Type Safety:** Ensures only Pynguin-supported argument types (primitives and collections) are used in seed tests.
- **Seed Test Generation:** Groups each call into a separate `test_seed_<n>()` function for maximum evolvability.
- **Idempotency and Safety:** Updates seed files only if content changes, never overwrites non-seed files, and uses SHA256 hash comparison for safety.
- **Generic Design:** Works with any Python function signature and test structure, supporting auto-discovery of functions.

---

## Workflow
1. **Collect raw LLM-generated test files** from the specified directory.
2. **Extract function calls and resolve arguments** using AST parsing and local variable context.
3. **Expand parametrized tests** into individual seed cases.
4. **Generate a consolidated seed file** with simple, direct test functions compatible with Pynguin.
5. **Write the seed file** only if changes are detected, ensuring safe and efficient updates.

---

## Usage
- Run as a CLI or import as a module.
- Example CLI usage:
  ```bash
  python -m evolutionary_algo_integration.normalizer \
      --tests-dir tests/test_suites \
      --module-name sample_calculator \
      --function-name calculator
  ```
- Result: A single seed file (e.g., `test_sample_calculator_seed.py`) ready for Pynguin seeding.

---

## Important Notes
- Arguments must be variable names bound to supported types; no fixtures or complex expressions in final output.
- One call per generated seed test for simplicity and evolvability.
- Auto-discovery of functions and test targets is supported for flexible integration.

---

For further details, refer to the docstrings and comments within the module.

# simple_population_manager.py Module

This module provides automated population size management for Pynguin, dynamically adjusting the evolutionary algorithm's population based on the complexity of the source module. It ensures efficient and effective test generation by scaling resources to match code difficulty.

---

## Key Features
- **Complexity Analysis:** Uses the Radon library to analyze cyclomatic complexity, Halstead volume, and source lines of code (SLOC) for the target module.
- **Population Size Calculation:** Computes a normalized complexity score and sets the population size between 50 and 200, emphasizing cyclomatic complexity for more challenging code.
- **Configuration Update:** Automatically updates Pynguin's configuration file with the new population size, ensuring the EA is neither underpowered nor wasteful.
- **Fallbacks and Safety:** Provides sensible defaults and error handling for missing files or analysis failures.

---

## Workflow
1. **Analyze the target module's complexity** using Radon metrics.
2. **Compute the optimal population size** based on weighted complexity factors.
3. **Update Pynguin's configuration** with the new population size if needed.
4. **Display analysis results** for transparency and review.

---

## Usage
- Import as a module or run as a script.
- Example usage:
  ```python
  from evolutionary_algo_integration.simple_population_manager import auto_adjust_population_for_module
  auto_adjust_population_for_module('sample_calculator')
  ```
- The population size is automatically set in Pynguin's configuration for subsequent test generation runs.

---

## Important Notes
- Dynamic population adjustment is crucial for balancing search efficiency and coverage quality.
- The module is designed to be extensible for additional complexity metrics or custom scaling strategies.

---

For further details, refer to the docstrings and comments within the module.
