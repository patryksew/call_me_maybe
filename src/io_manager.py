from pathlib import Path

from pydantic import BaseModel, Field

from .models import FunctionDefinitions, InputPrompts, OutputResults

DATA_PATH = Path(__file__).resolve().parents[1] / "data"
INPUT_PATH = DATA_PATH / "input"
OUTPUT_PATH = DATA_PATH / "output"


class IOManager(BaseModel):
    """Manages input/output operations for function definitions and prompts."""
    path_functions: Path = Field()
    path_input: Path = Field()
    path_output: Path = Field()

    def get_function_definitions(self) -> FunctionDefinitions:
        """
        Load and return function definitions from the specified path.

        :return: A FunctionDefinitions object.
        """
        with open(self.path_functions) as f:
            definitions = f.read()
            return FunctionDefinitions.model_validate_json(definitions)

    def get_input_prompts(self) -> InputPrompts:
        """
        Load and return input prompts from the specified path.

        :return: An InputPrompts object.
        """
        with open(self.path_input) as f:
            prompts = f.read()
            return InputPrompts.model_validate_json(prompts)

    def save_output_results(self, results: OutputResults) -> None:
        """
        Save output results to the specified path.

        :param results: The OutputResults object to save.
        """
        self.path_output.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path_output, "w") as f:
            f.write(results.model_dump_json(indent=4))

    def get_output_file_path(self) -> Path:
        """
        Return the path where output results are saved.

        :return: The Path to the output file.
        """
        return self.path_output
