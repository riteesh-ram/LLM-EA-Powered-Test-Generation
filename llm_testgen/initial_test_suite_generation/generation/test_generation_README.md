# initial_test_suite_generation/generation Directory

This directory contains modules responsible for prompt configuration, LLM interaction, and test generation orchestration in the automated test generation pipeline.

---

## Module Overview

### 1. `config.py`
**Functionality:**
- Stores configuration constants and parameters for the test generation process.
- Defines settings such as test suite directory, maximum repair attempts, and LLM prompt templates.

**Key Details:**
- Centralizes configuration for easy adjustment and experimentation.
- Used by other modules to maintain consistency across the pipeline.

---

### 2. `simple_llm.py`
**Functionality:**
- Provides the interface for interacting with the Large Language Model (LLM).
- Sends formatted prompts to the LLM and receives generated test code as output.

**Key Details:**
- Handles communication with external LLM APIs or local models.
- Manages prompt formatting, error handling, and response parsing.
- Can be extended to support different LLM providers or advanced prompt strategies.

---

## Key Workflow
1. **Configure test generation** using `config.py`.
2. **Format and send prompts** to the LLM via `simple_llm.py`.
3. **Receive and process generated test code** for further normalization and repair.

---

## Important Notes
- Configuration is centralized for reproducibility and ease of tuning.
- LLM interaction is abstracted for flexibility and future upgrades.
- This directory is the bridge between static analysis and test suite management.

---

## Usage
- Use `config.py` to adjust pipeline parameters and prompt templates.
- Use `simple_llm.py` to generate tests from prompts created by the analysis layer.
- Integrate with normalization and repair modules for a complete workflow.

---

For further details, refer to the docstrings and comments within each module.
