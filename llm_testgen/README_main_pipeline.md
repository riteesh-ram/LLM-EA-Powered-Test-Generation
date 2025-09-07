# Main Pipeline Execution: End-to-End Automated Test Generation

This README describes the complete workflow and architecture of the main pipeline for automated test generation, integrating static analysis, LLM-based test generation, evolutionary algorithms (Pynguin), test suite merging, repair, and mutation testing. The pipeline is designed for robust, scalable, and high-quality test suite creation for Python modules.

---

## High-Level Pipeline Steps

1. **Configuration & Initialization**
   - User specifies the target module and pipeline parameters (algorithm, coverage goals, population size, etc.).
   - Configuration manager loads and validates all settings for the pipeline.

2. **Static Analysis**
   - The analysis layer parses the source code to extract functions, classes, dependencies, and coverage goals.
   - External dependencies and mocking targets are identified for proper test generation.

3. **Initial Test Generation (LLM)**
   - A Large Language Model (LLM) generates initial test cases, covering basic functionality and edge cases.
   - Tests are normalized for compatibility with evolutionary algorithms.

4. **Seeding and Population Management**
   - Normalized LLM tests are used as seeds for Pynguin's genetic algorithm.
   - Population size is dynamically adjusted based on code complexity.

5. **Evolutionary Test Generation (Pynguin EA)**
   - Pynguin evolves and optimizes test cases using genetic algorithms (e.g., DynaMOSA), maximizing code coverage and discovering edge cases.
   - Assertion generation and minimization are performed for robust, maintainable tests.

6. **Test Suite Merging (LLM+EA)**
   - LLM and Pynguin-generated test suites are intelligently merged, deduplicated, and enhanced using LLM assistance.
   - Automated repair loop fixes failing tests or marks persistent failures with `@pytest.mark.xfail`.

7. **Mutation Testing**
   - Mutant versions of the source code are generated and tested to evaluate the effectiveness of the test suite.
   - Mutation score is calculated, and survived mutants are analyzed for further test improvements.

8. **Reporting & Output**
   - Coverage, mutation score, and survivor analysis reports are generated.
   - The final, merged, and repaired test suite is exported for integration and review.

---

## Key Features
- **Multi-layered test generation:** Combines LLM intuition and EA exploration for broad and deep coverage.
- **Automated repair and minimization:** Ensures robust, maintainable test suites with minimal manual intervention.
- **Mutation analysis:** Quantitatively measures and improves test suite effectiveness.
- **Extensibility:** Modular design allows for easy integration of new analysis, generation, and repair strategies.

---

## Usage
- Configure the pipeline with your target module and desired parameters.
- Run the main pipeline script to execute all steps end-to-end.
- Review generated reports and final test suite for quality assurance.
- Iterate and improve using survivor analysis and targeted test generation.

---

## Important Notes
- The pipeline is designed for real-world code, handling external dependencies and complex scenarios.
- Open challenges remain for advanced language features and perfect oracle generation.
- Regular mutation testing and survivor analysis are recommended for continuous improvement.

---

For further details, refer to the README files in each subdirectory and the docstrings within pipeline modules.
