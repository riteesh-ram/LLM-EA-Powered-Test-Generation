# initial_test_suite_generation/repair Directory

This directory contains modules responsible for managing, validating, and repairing generated test suites in the automated test generation pipeline.

---

## Module Overview

### 1. `test_suite_manager.py`
**Functionality:**
- Handles saving, running, and repairing generated test suites.
- Cleans and writes test code to disk, executes tests, and manages repair attempts for failing tests.

**Key Details:**
- Runs the test suite (typically with pytest) and collects results.
- If tests fail, sends error output back to the LLM for automatic repair, retrying up to a configured number of attempts.
- Prints results in a readable format and ensures only valid tests are retained.
- Can mark persistent failures with `@pytest.mark.xfail` to prevent blocking the suite.

---

## Key Workflow
1. **Save generated test code** using `test_suite_manager.py`.
2. **Run the test suite** and collect results.
3. **Repair failing tests** by sending errors to the LLM and retrying as needed.
4. **Finalize and clean up** the test suite for integration and reporting.

---

## Important Notes
- Automated repair is a key feature, reducing manual intervention.
- Persistent failures are handled gracefully to maintain suite robustness.
- This directory ensures the quality and reliability of generated tests before merging and deployment.

---

## Usage
- Use `test_suite_manager.py` to manage the lifecycle of generated test suites.
- Integrate with LLM and analysis modules for a complete, automated workflow.

---

For further details, refer to the docstrings and comments within each module.
