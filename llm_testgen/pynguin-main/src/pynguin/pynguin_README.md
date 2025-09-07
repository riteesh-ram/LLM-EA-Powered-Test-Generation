# Pynguin: Automated Test Generation Framework

This directory contains the full implementation of Pynguin, a state-of-the-art search-based test generation tool for Python. Pynguin leverages genetic algorithms, static and dynamic analysis, assertion inference, mutation analysis, and optional LLM integration to automatically generate high-quality unit tests for Python modules.

---

## High-Level Architecture

1. **Entry Points**
   - `__main__.py`, `cli.py`, `generator.py`: Command-line interface and orchestration of the test generation process.
   - `configuration.py`: Centralized configuration for all pipeline parameters.

2. **Static Analysis**
   - `analyses/`: Parses source code, builds control-flow graphs, infers types, and identifies coverage goals.
     - `module.py`, `syntaxtree.py`: Module and AST parsing.
     - `controlflow.py`: Control-flow graph construction.
     - `typesystem.py`: Type inference for variables and functions.
     - `seeding.py`: Loads and integrates seed tests (e.g., LLM-generated).

3. **Genetic Algorithm Engine**
   - `ga/`: Implements evolutionary search for test generation.
     - `algorithms/`: Multiple algorithms (DynaMOSA, MOSA, MIO, Random, WholeSuite, LLM-augmented).
     - `chromosome.py`, `testcasechromosome.py`, `testsuitechromosome.py`: Internal representations of test cases and suites.
     - `coveragegoals.py`: Defines line, branch, exception, and method coverage goals.
     - `operators/`: Crossover, mutation, and selection operators (e.g., tournament selection).
     - `postprocess.py`: Minimization and cleanup of generated tests.
     - `searchobserver.py`: Tracks search progress and coverage statistics.
     - `stoppingcondition.py`: Manages search termination criteria.

4. **Assertion Generation**
   - `assertion/`: Infers and inserts assertions into generated tests.
     - `assertiongenerator.py`: Main assertion inference engine.
     - `llmassertiongenerator.py`: Uses LLMs for assertion generation.
     - `mutation_analysis/`: Mutation-based assertion strengthening.

5. **Test Case Representation and Execution**
   - `testcase/`: Internal representation, execution, and export of test cases.
     - `defaulttestcase.py`, `statement.py`: Statement-level modeling.
     - `execution.py`: Safe execution and instrumentation of tests.
     - `export.py`: Converts internal test cases to executable Python code (e.g., pytest format).

6. **Instrumentation and Coverage Measurement**
   - `instrumentation/`: Injects probes into code to measure coverage during test execution.
     - `instrumentation.py`, `tracer.py`: Dynamic tracking of executed lines, branches, and exceptions.

7. **LLM Integration (Optional)**
   - `large_language_model/`: Interfaces with LLMs for test and assertion generation, prompt management, and caching.
     - `llmagent.py`, `llmtestcasehandler.py`: LLM-based enhancements to test generation.

8. **Mutation Analysis**
   - `assertion/mutation_analysis/`: Applies mutation testing to strengthen assertions and evaluate test suite effectiveness.
     - `controller.py`, `mutators.py`, `strategies.py`, `transformer.py`: Mutation operators and analysis strategies.

9. **Reporting and Utilities**
   - `utils/`: Utility functions for AST manipulation, configuration writing, randomness, reporting, and statistics.
     - `report.py`: Generates coverage and mutation analysis reports.
     - `statistics/`: Tracks runtime variables and search statistics.

10. **Slicing and Advanced Analysis**
    - `slicer/`: Dynamic slicing for advanced test case reduction and analysis.

---

## Key Features

- **Multi-Objective Genetic Algorithms:**
  - Supports DynaMOSA, MOSA, MIO, and more for maximizing coverage across multiple goals.
  - Archive-based, Pareto-dominance selection, and dynamic focus on uncovered goals.

- **Seeded Test Generation:**
  - Integrates existing or LLM-generated tests as seeds to guide and accelerate search.

- **Assertion Inference:**
  - Generates meaningful assertions using mutation analysis, heuristics, or LLMs.

- **Mutation Testing:**
  - Evaluates and strengthens test suite effectiveness by introducing code mutations and measuring detection rates.

- **Coverage Measurement:**
  - Tracks line, branch, exception, and method coverage in real time.

- **Minimization and Post-Processing:**
  - Removes redundant tests and statements for lean, maintainable test suites.

- **LLM Integration:**
  - Optional use of large language models for test and assertion generation, merging, and repair.

- **Advanced Language Feature Support:**
  - Handles most Python constructs; open challenges remain for async, generators, and complex decorators.

---

## Typical Workflow

1. **Configure Pynguin** via CLI or `configuration.py`.
2. **Analyze the target module** to identify coverage goals and dependencies.
3. **Seed the initial population** with existing or LLM-generated tests (optional).
4. **Run the genetic algorithm** to evolve and optimize test cases for maximum coverage.
5. **Generate and strengthen assertions** using mutation analysis and/or LLMs.
6. **Minimize and export** the final test suite in pytest format.
7. **Measure coverage and mutation score** to assess test suite quality.
8. **Iterate and improve** using survivor analysis and targeted test generation.

---

## Important Notes
- Pynguin is highly configurable and extensible for research and practical use.
- Supports integration with CI/CD pipelines and other automated workflows.
- Open challenges include handling advanced Python features and generating semantically perfect oracles.
- For best results, combine Pynguin with LLM-based test generation and mutation analysis.

---

## Usage
- Run Pynguin via CLI or integrate as a library in your test generation pipeline.
- Adjust configuration for your coverage goals, algorithm, and assertion strategies.
- Use seed tests and LLM integration for smarter, faster test generation.
- Review coverage and mutation reports to guide further improvements.

---

For further details, refer to the docstrings, comments, and documentation within each module and subdirectory.
