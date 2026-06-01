import argparse
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator


class CLIArguments(BaseModel):
    """Validated CLI arguments for the function calling program."""

    functions_definition: Path = Field(
        default=Path("data/input/functions_definition.json"),
        description="Path to function definitions JSON file"
    )
    input: Path = Field(
        default=Path("data/input/function_calling_tests.json"),
        description="Path to input prompts JSON file"
    )
    output: Path = Field(
        default=Path("data/output/function_calling_results.json"),
        description="Path to output results JSON file"
    )
    model: str = Field(
        default="Qwen/Qwen3-0.6B",
        description="Model name to use"
    )

    @field_validator("functions_definition", "input", mode="before")
    @classmethod
    def validate_input_paths(cls, v: str) -> Path:
        """
        Validate that input paths exist.

        :param v: The path string to validate.
        :return: A Path object if the path exists.
        :raises ValueError: If the input file is not found.
        """
        path = Path(v) if not isinstance(v, Path) else v
        if not path.exists():
            raise ValueError(f"Input file not found: {path}")
        return path

    @field_validator("output", mode="before")
    @classmethod
    def validate_output_path(cls, v: str) -> Path:
        """
        Convert output path to Path object.

        The path doesn't need to exist yet.

        :param v: The path string to convert.
        :return: A Path object for the output file.
        """
        return Path(v) if not isinstance(v, Path) else v

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> Any:
        """
        Validate that model name is not empty.

        :param v: The model name string to validate.
        :return: The stripped model name string.
        :raises ValueError: If the model name is empty or contains only whitespace.
        """
        if not v or not v.strip():
            raise ValueError("Model name cannot be empty")
        return v.strip()

    @classmethod
    def from_cli(cls) -> "CLIArguments":
        """
        Parse and validate command-line arguments from sys.argv.

        :return: A validated CLIArguments object.
        """
        parser = argparse.ArgumentParser(
            description="Function calling with LLM",
            prog="python -m src"
        )
        parser.add_argument(
            "--functions_definition",
            type=str,
            default="data/input/functions_definition.json",
            help="Path to function definitions JSON file "
                 "(default: data/input/functions_definition.json)"
        )
        parser.add_argument(
            "--input",
            type=str,
            default="data/input/function_calling_tests.json",
            help="Path to input prompts JSON file (default: data/input/function_calling_tests.json)"
        )
        parser.add_argument(
            "--output",
            type=str,
            default="data/output/function_calling_results.json",
            help="Path to output results JSON file "
                 "(default: data/output/function_calling_results.json)"
        )
        parser.add_argument(
            "--model",
            type=str,
            default="Qwen/Qwen3-0.6B",
            help="Model name to use (default: Qwen/Qwen3-0.6B)"
        )
        args = parser.parse_args()

        # Validate and convert to CLIArguments
        return cls(
            functions_definition=args.functions_definition,
            input=args.input,
            output=args.output,
            model=args.model
        )
