# initial_test_suite_generation/analysis Directory

This directory contains the core modules responsible for static analysis and prompt construction in the automated test generation pipeline. Each module plays a specific role in understanding the target source code and preparing high-quality prompts for LLM-based test generation.

---

## Module Overview

### 1. `module_parser.py`
**Functionality:**
- Parses the target Python module to extract its overall structure.
- Identifies classes, functions, methods, and their locations.
- Provides a foundation for further analysis by other extractors.

**Key Details:**
- Uses AST (Abstract Syntax Tree) parsing for robust code analysis.
- Handles nested classes and functions.

---

### 2. `function_extractor.py`
**Functionality:**
- Extracts all top-level and nested functions from the source module.
- Captures function names, arguments, default values, and docstrings.

**Key Details:**
- Supports detection of decorated functions and static/class methods.
- Provides detailed function signatures for prompt construction.

---

### 3. `class_extractor.py`
**Functionality:**
- Identifies all classes in the module and extracts their methods.
- Captures class names, method signatures, and docstrings.

**Key Details:**
- Handles inheritance and method overrides.
- Distinguishes between instance, static, and class methods.

---

### 4. `import_extractor.py`
**Functionality:**
- Detects all import statements and external dependencies in the source code.
- Records imported modules, functions, and objects.

**Key Details:**
- Flags dependencies that may require mocking or special handling in tests.
- Useful for identifying third-party libraries and system calls.

---

### 5. `monkeypatch_extractor.py`
**Functionality:**
- Analyzes code to identify areas that may require mocking or monkeypatching during testing.
- Searches for patterns indicating external resource usage (e.g., network, file I/O, environment variables).

**Key Details:**
- Uses AST and pattern matching to find calls to known external libraries (e.g., `requests`, `os`, `open`).
- Flags functions and methods that interact with external systems for targeted test generation.

---

### 6. `prompt_formatter.py`
**Functionality:**
- Aggregates all extracted information (functions, classes, imports, monkeypatch targets) into a structured prompt.
- Formats the prompt according to ASTER or custom templates for LLM consumption.

**Key Details:**
- Ensures prompts are clear, complete, and context-rich to maximize LLM output quality.
- Handles edge cases and special formatting for complex modules.

---

### 7. `test_pipeline.py`
**Functionality:**
- Orchestrates the entire analysis and prompt construction process.
- Coordinates calls to all extractors and the prompt formatter.
- Manages the workflow from source analysis to prompt generation.

**Key Details:**
- Entry point for static analysis in the test generation pipeline.
- Can be extended to support additional analysis steps or custom workflows.

---

## Key Workflow
1. **Parse the module** using `module_parser.py`.
2. **Extract functions** with `function_extractor.py`.
3. **Extract classes and methods** with `class_extractor.py`.
4. **Detect imports and dependencies** with `import_extractor.py`.
5. **Identify monkeypatch/mocking targets** with `monkeypatch_extractor.py`.
6. **Format the prompt** using `prompt_formatter.py`.
7. **Run the pipeline** via `test_pipeline.py` to produce a high-quality prompt for LLM test generation.

---

## Important Notes
- All modules use AST parsing for accuracy and robustness.
- The analysis is designed to be extensible for new code patterns and testing needs.
- Proper prompt construction is critical for effective LLM-based test generation.
- Monkeypatch extraction is especially important for real-world code with external dependencies.

---

## Usage
- Integrate this directory as the first step in your automated test generation workflow.
- Use `test_pipeline.py` as the main entry point to analyze a source module and generate a prompt for LLMs.
- Extend or customize extractors as needed for your specific codebase or testing requirements.

---

For further details, refer to the docstrings and comments within each module.
