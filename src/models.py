from functools import singledispatchmethod

from pydantic import BaseModel, Field, RootModel, field_validator

from fsm import FSM


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

    def attach_to_fsm(self, fsm: FSM, index: int) -> int:
        """Attaches the function definition to the FSM, starting from the given index. Returns the index of the final state."""

        # "name": "name",
        state = fsm.add_literal('"name":', index)
        fsm.add_whitespace(state)
        state = fsm.add_literal(f'"{self.name}",', state)
        fsm.add_whitespace(state)

        # "parameters": {
        state = fsm.add_literal('"parameters":', state)
        fsm.add_whitespace(state)
        state = fsm.add_literal('{', state)

        # actual parameters
        if self.parameters:
            first = True
            for key, val in self.parameters.items():
                if not first:
                    state = fsm.add_literal(',', state)
                fsm.add_whitespace(state)
                state = fsm.add_literal(f'"{key}":', state)
                fsm.add_whitespace(state)

                p_type = val['type']
                if p_type == "string":
                    state = fsm.add_string(state)
                elif p_type == "number":
                    state = fsm.add_number(state)
                elif p_type == "boolean":
                    state = fsm.add_boolean(state)
                elif p_type == "array":
                    # print("Array is not supported yet")
                    ...
                else:
                    raise ValueError("Unsupported parameter type: " + p_type)

                first = False

        fsm.add_whitespace(state)
        state = fsm.add_literal('}', state)
        fsm.add_whitespace(state)

        return state


class FunctionDefinitions(RootModel[list[FunctionDefinition]]):
    @property
    def functions(self):
        return self.root

    def to_fsm(self) -> FSM:
        """Converts the function definition to an FSM that can be used in constrained decoding. Does not contain the prompt."""
        fsm = FSM()

        root_state = fsm.add_literal('{', 0)
        fsm.add_whitespace(root_state)

        terminal_states = [fun.attach_to_fsm(fsm, root_state) for fun in self.functions]

        fsm.add_literal('}', terminal_states)

        return fsm


class InputPrompt(BaseModel):
    prompt: str = Field()


class InputPrompts(RootModel[list[InputPrompt]]):
    @property
    def prompts(self):
        return self.root
