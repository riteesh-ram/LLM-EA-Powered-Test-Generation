#Pipeline configuration for LLM test generation.

from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Union

@dataclass
class PipelineConfig:
    """Configuration for the test generation pipeline."""
    
    # Core configuration
    module_name: str
    function_name: Optional[str] = None  # Deprecated, use function_names
    function_names: Optional[List[str]] = None  # New: support multiple functions
    
    # Directories
    source_dir: Path = Path("tests/source")
    tests_dir: Path = Path("tests/test_suites")
    
    # Evolution parameters
    generations: int = 10
    population_size: int = 20
    mutation_rate: float = 0.1
    crossover_rate: float = 0.8
    
    # LLM configuration
    model_name: str = "gpt-3.5-turbo"
    max_tokens: int = 2000
    temperature: float = 0.7
    
    # Test generation parameters
    max_tests_per_function: int = 10
    include_edge_cases: bool = True
    include_parametrized: bool = True
    
    def __post_init__(self):
        """Post-initialization processing."""
        # Handle function names compatibility
        if self.function_names is None:
            if self.function_name is not None:
                self.function_names = [self.function_name]
            else:
                # Auto-detect function name if not provided
                self.function_names = [self.module_name]
        
        # Ensure backward compatibility
        if self.function_name is None and self.function_names:
            self.function_name = self.function_names[0]
        
        # Ensure directories exist
        self.source_dir.mkdir(parents=True, exist_ok=True)
        self.tests_dir.mkdir(parents=True, exist_ok=True)
        
        # Convert string paths to Path objects
        if isinstance(self.source_dir, str):
            self.source_dir = Path(self.source_dir)
        if isinstance(self.tests_dir, str):
            self.tests_dir = Path(self.tests_dir)
    
    @property
    def source_file(self) -> Path:
        """Get the source file path."""
        return self.source_dir / f"{self.module_name}.py"
    
    @property
    def test_file_pattern(self) -> str:
        """Get the test file pattern."""
        return f"llm_generated_test_{self.module_name}.py"
    
    @property
    def seed_file_pattern(self) -> str:
        """Get the seed file pattern."""
        return f"llm_generated_test_{self.module_name}_seed.py"
    
    def __str__(self) -> str:
        """String representation of configuration."""
        functions_str = ", ".join(self.function_names) if self.function_names else "None"
        return (f"PipelineConfig(module={self.module_name}, "
                f"functions=[{functions_str}], "
                f"source_dir={self.source_dir}, "
                f"tests_dir={self.tests_dir})")
