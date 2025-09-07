#!/bin/bash
# Script to set cache-disabling environment variables for the LLM testgen pipeline

echo "🧹 Setting up cache-disabling environment variables..."

# Export environment variables to disable Python caching
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPYCACHEPREFIX=/tmp/disabled_pycache
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1

echo "Environment variables set:"
echo "  PYTHONDONTWRITEBYTECODE=$PYTHONDONTWRITEBYTECODE"
echo "  PYTHONPYCACHEPREFIX=$PYTHONPYCACHEPREFIX" 
echo "  PYTEST_DISABLE_PLUGIN_AUTOLOAD=$PYTEST_DISABLE_PLUGIN_AUTOLOAD"

echo ""
echo "To make these permanent, add the following to your shell profile:"
echo "export PYTHONDONTWRITEBYTECODE=1"
echo "export PYTHONPYCACHEPREFIX=/tmp/disabled_pycache"
echo "export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1"

echo ""
echo "You can now run the pipeline with caching disabled:"
echo "python main_pipeline.py sample_number"
