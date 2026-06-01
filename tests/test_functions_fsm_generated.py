import json

from src.models import FunctionDefinitions
from src.fsm import FSM


def load_definitions() -> object:
    """
    Load function definitions from a JSON file.

    :return: Parsed JSON data from the default functions definition file.
    """
    with open("data/input/functions_definition.json") as f:
        return json.load(f)


def build_fsm_from_definitions() -> FSM:
    """
    Build an FSM from the loaded function definitions.

    :return: The constructed FSM object.
    """
    data = load_definitions()
    funcs = FunctionDefinitions.model_validate(data)
    return funcs.to_fsm()


def test_generated_fsm_rejects_unknown_function_name() -> None:
    """Verify that the FSM rejects a function name it doesn't know."""
    fsm = build_fsm_from_definitions()
    txt = '{"name":"fn_unknown","parameters":{}}'
    assert fsm.validate_text(txt).name == FSM.ValidationResult.NOK.name


def test_generated_fsm_rejects_invalid_parameter_type() -> None:
    """Verify that the FSM rejects a parameter value of the wrong type."""
    fsm = build_fsm_from_definitions()
    txt = '{"name":"fn_add_numbers","parameters":{"a":"one","b":2}}'
    assert fsm.validate_text(txt).name == FSM.ValidationResult.NOK.name
