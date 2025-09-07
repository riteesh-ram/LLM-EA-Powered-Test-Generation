#Setup and Run Instructions
##1. Creating myvenv (Main Environment):
Required Python Version: 3.13+
Purpose: LLM integration, test generation, merging, and repair
Navigate to the project root -> llm_testgen
Cmd to create virtual environment with Python 3.13+ -> python3.13 -m venv myvenv
Cmd to activate environment -> source myvenv/bin/activate
Cmd to upgrade pip: pip install --upgrade pip
Cmd to install dependencies: pip install -r requirements.txt
Verify installation: python --version # Should show Python 3.13.x
##2. Creating my_pynguin_venv (Pynguin Environment):
Required Python Version: 3.10
Purpose: Evolutionary algorithm test generation with Pynguin
Navigate to Pynguin directory -> llm_testgen/pynguin-main
Cmd to create virtual environment with Python 3.10 -> python3.10 -m venv
my_pynguin_venv
Cmd to activate environment -> source my_pynguin_venv/bin/activate
Cmd to upgrade pip: pip install --upgrade pip
Cmd to install dependencies: pip install -r docs/requirements.txt
Cmd to install Pynguin in editable mode: pip install -e .
Verify installation:
• python --version # Should show Python 3.10.x
• export PYNGUIN_DANGER_AWARE=1 # Run before pynguin command
• pynguin --version # Should show Pynguin version
##3. Creating mutpy_env (Mutation Testing Environment):
Required Python Version: 3.10
Purpose: Mutation testing with MutPy
vii
Note: Deactivate any current environment before proceeding.
Navigate to mutants validation directory -> cd ../mutants_validation
Cmd to create virtual environment with Python 3.10 -> python3.10 -m venv
mutpy_env
Cmd to activate environment -> source mutpy_env/bin/activate
Cmd to upgrade pip -> pip install --upgrade pip
Cmd to install dependencies -> pip install -r requirements.txt
Verify installation:
• python --version # Should show Python 3.10.x
• mut.py --version # Should show MutPy version

#How to Run the Tool:
Purpose: To execute the main automated test generation pipeline.
Required Environment: myvenv (Main Environment)
Navigate to the project root directory -> cd .. (if not already there)
Cmd to activate environment -> source myvenv/bin/activate
Cmd to run the main script -> python main_pipeline.py <module-to-test>
Note: Replace <module-to-test> with the actual name of the Python module or file
you wish to process.

#Important Note
This project utilizes the Gemini 2.5 Flash model, which is subject to the limitations of its free
usage tier.
• Token Limit: Each Google account is allotted a quota of 250,000 tokens.
• Consequence of Exceeding the Limit: If this token limit is exceeded, the Gemini
model will stop generating output. As a result, any pipeline steps that rely on the LLM
will fail.

#How to Resolve a Token Limit Issue?
1. Create a new API key by registering for the Gemini API with a different Google
account.
2. Navigate to the project's llm_testgen root folder.
3. Open the .env file.
4. Add your new API key to the file by setting the GEMINI_API_KEY .
