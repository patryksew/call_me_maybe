from pathlib import Path

from pydantic import BaseModel, Field

from .models import FunctionDefinitions, InputPrompts, OutputResults

DATA_PATH = Path(__file__).resolve().parents[1] / "data"
INPUT_PATH = DATA_PATH / "input"
OUTPUT_PATH = DATA_PATH / "output"


class IOManager(BaseModel):
    path_functions: Path = Field(default=INPUT_PATH / "functions_definition.json")
    path_input: Path = Field(default=INPUT_PATH / "function_calling_tests.json")
    path_output: Path = Field(default=OUTPUT_PATH / "function_calling_results.json")

    def get_function_definitions(self) -> FunctionDefinitions:
        with open(self.path_functions) as f:
            definitions = f.read()
            return FunctionDefinitions.model_validate_json(definitions)

    def get_input_prompts(self):
        with open(self.path_input) as f:
            prompts = f.read()
            return InputPrompts.model_validate_json(prompts)

    def save_output_results(self, results: OutputResults):
        with open(self.path_output, "w") as f:
            f.write(results.model_dump_json(indent=4))
