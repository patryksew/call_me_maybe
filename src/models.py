import json

from pydantic import BaseModel, Field, RootModel, field_validator

from .fsm import FSM


class OutputResult(BaseModel):
    """Represents a single function calling result."""
    prompt: str = Field(default="")
    name: str = Field()
    parameters: dict = Field()


class OutputResults(RootModel[list[OutputResult]]):
    """A collection of OutputResult objects."""
    root: list[OutputResult] = Field(default_factory=list)

    @property
    def results(self) -> list[OutputResult]:
        """Return the list of output results."""
        return self.root

    # @append.register
    def append(self, result: OutputResult) -> None:
        """Append an OutputResult object to the collection."""
        self.root.append(result)


class FunctionDefinition(BaseModel):
    """Definition of a function that can be called by the LLM."""
    name: str = Field()
    description: str = Field()
    parameters: dict[str, dict[str, str]] = Field()
    returns: dict = Field()

    @field_validator("parameters", mode="after")
    @staticmethod
    def validate_parameters(parameters: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
        """
        Validate the parameter definitions.

        Ensures that each parameter has a 'type' field and that the type is one of the
        supported JSON types.

        :param parameters: A dictionary of parameter definitions.
        :return: The validated parameters dictionary.
        :raises ValueError: If a parameter is missing a type or has an invalid type.
        """
        for param_name, param_info in parameters.items():
            if "type" not in param_info:
                raise ValueError(f"Parameter '{param_name}' is missing 'type' field.")
            param_type = param_info["type"]
            if param_type not in {"object", "array", "string", "number", "boolean", "null", "int",
                                  "integer"}:
                raise ValueError(
                    f"Parameter '{param_name}' has invalid type '{param_type}'."
                    f"Must be one of 'object', 'array', 'string', 'number', "
                    f"'boolean', 'int', 'integer', or 'null'.")
        return parameters

    def attach_to_fsm(self, fsm: FSM, index: int) -> int:
        """
        Attach the function definition to the FSM.

        Starts from the given index and returns the index of the final state.

        :param fsm: The FSM to attach to.
        :param index: The starting state index.
        :return: The index of the final state.
        :raises ValueError: If an unsupported parameter type is encountered.
        """

        # "name": "name",
        state = fsm.add_literal(f'"name": "{self.name}",\n    ', index)

        # "parameters": {
        state_a = [fsm.add_literal('"parameters": {', state)]

        # actual parameters
        if self.parameters:
            first = True
            for key, val in self.parameters.items():
                if not first:
                    state = fsm.add_literal(f',\n        "{key}": ', state_a)
                else:
                    state = fsm.add_literal(f'\n        "{key}": ', state_a)

                p_type = val['type']
                if p_type == "string":
                    state_a = [fsm.add_string(state)]
                elif p_type == "number":
                    state_a = fsm.add_number(state)
                elif p_type in ["int", "integer"]:
                    state_a = fsm.add_integer(state)
                elif p_type == "boolean":
                    state_a = fsm.add_boolean(state)
                elif p_type == "array":
                    # print("Array is not supported yet")
                    ...
                else:
                    raise ValueError("Unsupported parameter type: " + p_type)

                first = False

        state = fsm.add_literal('\n    }\n', state_a)

        return state


class FunctionDefinitions(RootModel[list[FunctionDefinition]]):
    """A collection of FunctionDefinition objects."""

    @property
    def functions(self) -> list[FunctionDefinition]:
        """Return the list of function definitions."""
        return self.root

    def to_fsm(self) -> FSM:
        """
        Convert the function definitions to an FSM.

        The FSM can be used for constrained decoding to ensure the LLM output
        matches the defined function schemas.

        :return: An FSM object.
        :raises ValueError: If an error occurs during FSM construction.
        """
        fsm = FSM()

        # "prompt":
        root_state = fsm.add_literal('{\n    "prompt": ', 0)
        # actual prompt
        root_state = fsm.add_string(root_state)
        # indent before "name"
        root_state = fsm.add_literal(',\n    ', root_state)

        try:
            terminal_states = [fun.attach_to_fsm(fsm, root_state) for fun in self.functions]
        except ValueError as e:
            raise ValueError("Failed to attach function definitions to FSM") from e

        fsm.add_literal('}', terminal_states)

        return fsm


class InputPrompt(BaseModel):
    """Represents a single input prompt for the LLM."""
    prompt: str = Field()

    def __str__(self) -> str:
        """Return the prompt as a JSON-encoded string."""
        return json.dumps(self.prompt)


class InputPrompts(RootModel[list[InputPrompt]]):
    """A collection of InputPrompt objects."""

    @property
    def prompts(self) -> list[InputPrompt]:
        """Return the list of input prompts."""
        return self.root
