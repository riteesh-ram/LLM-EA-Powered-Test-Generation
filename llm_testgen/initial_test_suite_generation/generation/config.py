"""
Configuration for LLM Test Generation with Google Gemini 2.5 Pro
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

# Gemini 2.5 Pro Configuration
MODEL_NAME = os.getenv('MODEL_NAME', 'gemini-2.5-pro')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
MAX_INPUT_TOKENS = 1000000    # Gemini 2.5 Pro context window: ~1M tokens
MAX_OUTPUT_TOKENS = int(os.getenv('MAX_OUTPUT_TOKENS', 8192))
TEMPERATURE = float(os.getenv('TEMPERATURE', 0.1))
TOP_P = float(os.getenv('TOP_P', 0.95))
TOP_K = int(os.getenv('TOP_K', 40))

# Output Configuration
TEST_SUITES_DIR = os.getenv('TEST_SUITES_DIR', 'tests/test_suites')

# Repair Configuration
MAX_REPAIR_ATTEMPTS = int(os.getenv('MAX_REPAIR_ATTEMPTS', 5))
OUTPUT_CONFIG = {
    "save_tests": True,
    "output_dir": TEST_SUITES_DIR,
    "include_timestamp": True
}
