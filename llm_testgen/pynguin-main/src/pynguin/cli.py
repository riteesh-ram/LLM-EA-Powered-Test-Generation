#  This file is part of Pynguin.
#
#  SPDX-FileCopyrightText: 2019–2025 Pynguin Contributors
#
#  SPDX-License-Identifier: MIT
#
"""Pynguin is an automated unit test generation framework for Python.

This module provides the main entry location for the program execution from the command
line.
"""

from __future__ import annotations

import logging
import os
import sys

from pathlib import Path
from typing import TYPE_CHECKING

import simple_parsing

from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install

import pynguin.configuration as config

from pynguin.__version__ import __version__
from pynguin.generator import run_pynguin
from pynguin.generator import set_configuration
from pynguin.utils.configuration_writer import write_configuration


if TYPE_CHECKING:
    import argparse


def _create_argument_parser() -> argparse.ArgumentParser:
    parser = simple_parsing.ArgumentParser(
        add_option_string_dash_variants=simple_parsing.DashVariant.UNDERSCORE_AND_DASH,
        description="Pynguin is an automatic unit test generation framework for Python",
        fromfile_prefix_chars="@",
    )
    parser.add_argument("--version", action="version", version="%(prog)s " + __version__)
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        dest="verbosity",
        default=0,
        help="verbose output (repeat for increased verbosity)",
    )
    parser.add_argument(
        "--no-rich",
        "--no_rich",
        "--poor",  # hehe
        dest="no_rich",
        action="store_true",
        default=False,
        help="Don't use rich for nicer consoler output.",
    )
    parser.add_argument(
        "--log-file",
        "--log_file",
        help="Path to an optional log file.",
        type=Path,
    )
    


    # Add all config arguments, but we will override project_path, module_name, and output_path in main
    # Remove required flags for these fields by setting them after parsing
    parser.add_arguments(config.Configuration, dest="config")

    return parser


def _expand_arguments_if_necessary(arguments: list[str]) -> list[str]:
    #Expand command-line arguments, if necessary.
    if (
        "--output_variables" not in arguments
        and "--output-variables" not in arguments
        and "--coverage_metrics" not in arguments
        and "--coverage-metrics" not in arguments
    ):
        return arguments
    if "--output_variables" in arguments:
        arguments = _parse_comma_separated_option(arguments, "--output_variables")
    elif "--output-variables" in arguments:
        arguments = _parse_comma_separated_option(arguments, "--output-variables")

    if "--coverage_metrics" in arguments:
        arguments = _parse_comma_separated_option(arguments, "--coverage_metrics")
    elif "--coverage-metrics" in arguments:
        arguments = _parse_comma_separated_option(arguments, "--coverage-metrics")
    return arguments


def _parse_comma_separated_option(arguments: list[str], option: str) -> list[str]:
    index = arguments.index(option)
    if "," not in arguments[index + 1]:
        return arguments
    variables = arguments[index + 1].split(",")
    return arguments[: index + 1] + variables + arguments[index + 2 :]


def _setup_output_path(output_path: str) -> None:
    path = Path(output_path).resolve()
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)


def _setup_logging(
    verbosity: int,
    no_rich: bool,  # noqa: FBT001
    log_file: Path | None,
) -> Console | None:
    level = logging.WARNING
    if log_file is not None:
        level = logging.INFO
    if verbosity == 1:
        level = logging.INFO
    if verbosity >= 2:
        level = logging.DEBUG

    console = None
    handler: logging.Handler
    if no_rich:
        handler = logging.StreamHandler()
    else:
        install()
        console = Console(tab_size=4)
        handler = RichHandler(rich_tracebacks=True, log_time_format="[%X]", console=console)
        handler.setFormatter(logging.Formatter("%(message)s"))

    if log_file is not None:
        handler = logging.FileHandler(log_file)

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s](%(name)s:%(funcName)s:%(lineno)d): %(message)s",
        datefmt="[%X]",
        handlers=[handler],
    )
    return console


# People may wipe their disk, so we give them a heads-up.
_DANGER_ENV = "PYNGUIN_DANGER_AWARE"


def main(argv: list[str] | None = None) -> int:
    """Entry point for the CLI of the Pynguin automatic unit test generation framework."""
    if _DANGER_ENV not in os.environ:
        print(  # noqa: T201
            f"""Environment variable '{_DANGER_ENV}' not set.
Aborting to avoid harming your system.
Please refer to the documentation
(https://pynguin.readthedocs.io/en/latest/user/quickstart.html)
to see why this happens and what you must do to prevent it."""
        )
        return -1

    if argv is None:
        argv = sys.argv
    # Don't auto-add --help since we set our own defaults
    # if len(argv) <= 1:
    #     argv.append("--help")
    argv = _expand_arguments_if_necessary(argv[1:])

    argument_parser = _create_argument_parser()
    
    # Add dummy values for required arguments to avoid CLI errors
    # These will be overridden with our custom paths
    if "--project-path" not in argv and "--project_path" not in argv:
        argv.extend(["--project-path", "."])
    if "--module-name" not in argv and "--module_name" not in argv:
        argv.extend(["--module-name", "dummy"])
    if "--output-path" not in argv and "--output_path" not in argv:
        argv.extend(["--output-path", "."])
    
    parsed = argument_parser.parse_args(argv)

    # Set paths as per user requirements
    # 1. module path: source code under llm_testgen/tests/source
    # 2. output path: test suite path under llm_testgen/tests/test_suites
    # 3. project path: current pynguin directory

    current_dir = Path.cwd()
    llmtestgen_path = None
    for path in [current_dir] + list(current_dir.parents):
        potential = path / "llm_testgen"
        if potential.exists():
            llmtestgen_path = potential
            break

    if llmtestgen_path is None:
        print("Error: Could not find llm_testgen directory")
        return -1

    source_dir = llmtestgen_path / "tests" / "source"
    test_suites_dir = llmtestgen_path / "tests" / "test_suites"
    # Project path should be the current pynguin directory
    pynguin_project_dir = current_dir

    if not source_dir.exists():
        print(f"Error: Source directory not found: {source_dir}")
        return -1
    
    if not test_suites_dir.exists():
        test_suites_dir.mkdir(parents=True, exist_ok=True)

    py_files = list(source_dir.glob("*.py"))
    if not py_files:
        print(f"Error: No Python files found in {source_dir}")
        return -1

    parsed.config.project_path = str(pynguin_project_dir)
    
    # Respect the module name passed via --module-name argument
    # Find the corresponding source file for the requested module
    requested_module = parsed.config.module_name
    source_file = source_dir / f"{requested_module}.py"
    
    if not source_file.exists():
        print(f"Error: Requested module {requested_module}.py not found in {source_dir}")
        print(f"Available modules: {[f.stem for f in py_files]}")
        return -1
    
    # Create pynguin_tests directory for output
    pynguin_tests_dir = test_suites_dir / "pynguin_tests"
    pynguin_tests_dir.mkdir(parents=True, exist_ok=True)
    parsed.config.test_case_output.output_path = str(pynguin_tests_dir)
    
    # Copy the requested source file to project directory so Pynguin can import it
    import shutil
    target_file = pynguin_project_dir / source_file.name
    shutil.copy2(source_file, target_file)
    
    # Configure seeding from existing test files in test_suites directory (ONLY directly in test_suites, not in subfolders)
    existing_test_files = [f for f in test_suites_dir.glob("llm_generated_test_*.py") if f.is_file()]
    # Run normalization to ensure a *_seed.py file exists reflecting latest raw tests
    try:
        sys.path.insert(0, str(llmtestgen_path))
        from evolutionary_algo_integration.normalizer import (
            generate_seed_file,  # type: ignore
        )
        from evolutionary_algo_integration.normalizer import ExtractionConfig  # type: ignore

        # Heuristic: assume function under test shares module name unless specified differently.
        # We inspect the source file for 'def ' patterns to pick first top-level function if present.
        source_text = source_file.read_text(encoding="utf-8")
        func_name = None
        for line in source_text.splitlines():
            line_strip = line.strip()
            if line_strip.startswith("def ") and line_strip[4:].split("(")[0]:
                func_name = line_strip[4:].split("(")[0]
                break
        if func_name is None:
            func_name = py_files[0].stem  # fallback
        seed_path = generate_seed_file(
            ExtractionConfig(
                module_name=py_files[0].stem,
                function_name=func_name,
                tests_dir=test_suites_dir,
            )
        )
        if seed_path.exists():
            print(f"   -> Normalized seed file generated: {seed_path.name}")
            if seed_path not in existing_test_files:
                existing_test_files.append(seed_path)
    except Exception as norm_exc:  # pragma: no cover
        print(f"[Normalization Warning] Could not generate seed file: {norm_exc}")
    print(f"=== SEEDING CONFIGURATION ===")
    print(f"Scanning for seed test files in: {test_suites_dir}")
    print(f"Looking for files matching pattern: llm_generated_test_*.py")
    
    if existing_test_files:
        print(f"Found {len(existing_test_files)} seed test file(s):")
        for i, seed_file in enumerate(existing_test_files, 1):
            print(f"  {i}. {seed_file.name}")
            # Count test functions/methods in each file
            try:
                with open(seed_file, 'r') as f:
                    content = f.read()
                    import ast
                    tree = ast.parse(content)
                    test_funcs = []
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                            test_funcs.append(node.name)
                        elif isinstance(node, ast.ClassDef):
                            for class_node in node.body:
                                if isinstance(class_node, ast.FunctionDef) and class_node.name.startswith('test_'):
                                    test_funcs.append(f"{node.name}.{class_node.name}")
                    print(f"     -> Contains {len(test_funcs)} test functions/methods")
                    if test_funcs:
                        print(f"     -> Test functions: {test_funcs}")
            except Exception as e:
                print(f"     -> Could not parse file: {e}")
        
        # Enable seeding
        parsed.config.seeding.initial_population_seeding = True
        parsed.config.seeding.initial_population_data = str(test_suites_dir)
        
        # Set seeding probability to use seeds more frequently
        parsed.config.seeding.seeded_testcases_reuse_probability = 1.0
        
        print(f"\nSEEDING ENABLED:")
        print(f"   - initial_population_seeding: {parsed.config.seeding.initial_population_seeding}")
        print(f"   - initial_population_data: {parsed.config.seeding.initial_population_data}")
        print(f"   - seeded_testcases_reuse_probability: {parsed.config.seeding.seeded_testcases_reuse_probability}")
    else:
        print("No existing test files found for seeding")
        parsed.config.seeding.initial_population_seeding = False
    
    print(f"\n=== MODULE CONFIGURATION ===")
    print(f"Source module: {parsed.config.module_name} from {source_dir}")
    print(f"Source file copied to: {target_file}")
    print(f"Test output directory: {parsed.config.test_case_output.output_path}")
    print(f"Project path: {pynguin_project_dir}")
    print(f"================================\n")

    # === DYNAMIC POPULATION SIZE ADJUSTMENT ===
    print(f"=== DYNAMIC POPULATION SIZING ===")
    try:
        # Import the simple population manager
        sys.path.insert(0, str(llmtestgen_path / "evolutionary_algo_integration"))
        from simple_population_manager import auto_adjust_population_for_module
        
        # Auto-adjust population size based on source code complexity
        computed_population = auto_adjust_population_for_module(parsed.config.module_name)
        print(f"Population size dynamically set to: {computed_population}")
        
    except Exception as e:
        print(f"Population auto-adjustment failed: {e}")
        print(f"   Using default population size from configuration")
    print(f"===================================\n")

    _setup_output_path(test_suites_dir)

    console = _setup_logging(
        verbosity=parsed.verbosity,
        no_rich=parsed.no_rich,
        log_file=parsed.log_file,
    )

    set_configuration(parsed.config)
    write_configuration()
    if console is not None:
        with console.status("Running Pynguin..."):
            return run_pynguin().value
    else:
        return run_pynguin().value


if __name__ == "__main__":
    import multiprocess as mp

    mp.set_start_method("spawn")

    sys.exit(main(sys.argv))
