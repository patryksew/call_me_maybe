from functools import singledispatchmethod

from pydantic import BaseModel, Field, RootModel, field_validator


class OutputResult(BaseModel):
    prompt: str = Field()
    name: str = Field()
    parameters: dict = Field()


class OutputResults(RootModel[list[OutputResult]]):
    root: list[OutputResult] = Field(default_factory=list)

    @property
    def results(self):
        return self.root

    @singledispatchmethod
    def append(self):
        ...

    @append.register
    def _(self, result: OutputResult):
        self.root.append(result)

    @append.register
    def _(self, result: str):
        self.root.append(OutputResult.model_validate_json(result))


class FunctionDefinition(BaseModel):
    name: str = Field()
    description: str = Field()
    parameters: dict[str, dict[str, str]] = Field()
    returns: dict = Field()

    @field_validator("parameters", mode="after")
    @staticmethod
    def validate_parameters(parameters: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
        for param_name, param_info in parameters.items():
            if "type" not in param_info:
                raise ValueError(f"Parameter '{param_name}' is missing 'type' field.")
            param_type = param_info["type"]
            if param_type not in {"object", "array", "string", "number", "boolean", "null"}:
                raise ValueError(
                    f"Parameter '{param_name}' has invalid type '{param_type}'. Must be one of 'object', 'array', 'string', 'number', 'boolean', or 'null'.")
        return parameters


class FunctionDefinitions(RootModel[list[FunctionDefinition]]):
    @property
    def functions(self):
        return self.root


class InputPrompt(BaseModel):
    prompt: str = Field()


class InputPrompts(RootModel[list[InputPrompt]]):
    @property
    def prompts(self):
        return self.root
