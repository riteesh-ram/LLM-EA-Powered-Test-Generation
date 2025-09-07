# LLM-EA Powered Test Generation: Setup & Run Instructions


## 1. Main Environment: `myvenv`

- **Python Required:** 3.13+
- **Purpose:** LLM integration, test generation, merging, and repair

**Steps:**

1. **Navigate:**  
   Go to the project root, then into `llm_testgen/`
   ```bash
   cd llm_testgen
   ```

2. **Create virtual environment:**  
   ```bash
   python3.13 -m venv myvenv
   ```

3. **Activate environment:**  
   ```bash
   source myvenv/bin/activate
   ```

4. **Upgrade pip:**  
   ```bash
   pip install --upgrade pip
   ```

5. **Install dependencies:**  
   ```bash
   pip install -r requirements.txt
   ```

6. **Verify installation:**  
   ```bash
   python --version  # Should show Python 3.13.x
   ```


## 2. Pynguin Environment: `my_pynguin_venv`

- **Python Required:** 3.10
- **Purpose:** Evolutionary algorithm test generation with Pynguin

**Steps:**

1. **Navigate:**  
   Move to the Pynguin directory:
   ```bash
   cd pynguin-main
   ```

2. **Create virtual environment:**  
   ```bash
   python3.10 -m venv my_pynguin_venv
   ```

3. **Activate environment:**  
   ```bash
   source my_pynguin_venv/bin/activate
   ```

4. **Upgrade pip:**  
   ```bash
   pip install --upgrade pip
   ```

5. **Install dependencies:**  
   ```bash
   pip install -r docs/requirements.txt
   ```

6. **Install Pynguin in editable mode:**  
   ```bash
   pip install -e .
   ```

7. **Verify installation:**  
   ```bash
   python --version           # Should show Python 3.10.x
   export PYNGUIN_DANGER_AWARE=1   # Run before pynguin command
   pynguin --version
   ```

---

## 3. Mutation Testing Environment: `mutpy_env`

- **Python Required:** 3.10
- **Purpose:** Mutation testing with MutPy

**Note:** Deactivate any currently active environment before proceeding.

**Steps:**

1. **Navigate:**  
   Go to the mutants validation directory:
   ```bash
   cd ../mutants_validation
   ```

2. **Create virtual environment:**  
   ```bash
   python3.10 -m venv mutpy_env
   ```

3. **Activate environment:**  
   ```bash
   source mutpy_env/bin/activate
   ```

4. **Upgrade pip:**  
   ```bash
   pip install --upgrade pip
   ```

5. **Install dependencies:**  
   ```bash
   pip install -r requirements.txt
   ```

6. **Verify installation:**  
   ```bash
   python --version    # Should show Python 3.10.x
   mut.py --version    # Should show MutPy version
   ```


## How to Run the Tool

- **Purpose:** Execute the automated test generation pipeline.
- **Required Environment:** `myvenv` (Main Environment)

**Steps:**

1. **Navigate to project root:**
   ```bash
   cd ..   # If not already there
   ```

2. **Activate main environment:**
   ```bash
   source myvenv/bin/activate
   ```

3. **Run the main script:**
   ```bash
   python main_pipeline.py <module-to-test>
   ```
   Replace `<module-to-test>` with the actual Python module or file to process.


## Important Note: Gemini 2.5 Flash Model Usage

This project uses the Gemini 2.5 Flash model, which has limitations under its free usage tier:

- **Token Limit:** 250,000 tokens per Google account.
- **If exceeded:** The Gemini model will stop generating output; pipeline steps relying on the LLM will fail.


## Resolving Token Limit Issues

1. **Create a new API key:**  
   Register for the Gemini API with a different Google account.

2. **Navigate to the project's `llm_testgen` root folder.**

3. **Open the `.env` file.**

4. **Update API key:**  
   Add your new API key in the file:
   ```
   GEMINI_API_KEY=<your-new-api-key>
   ```
