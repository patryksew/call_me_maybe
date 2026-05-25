import json
from src.models import FunctionDefinitions
from src.fsm import FSM


def load_definitions():
    with open("data/input/functions_definition.json") as f:
        return json.load(f)


def build_fsm_from_definitions():
    data = load_definitions()
    funcs = FunctionDefinitions.model_validate(data)
    return funcs.to_fsm()


def test_generated_fsm_rejects_unknown_function_name():
    fsm = build_fsm_from_definitions()
    txt = '{"name":"fn_unknown","parameters":{}}'
    assert fsm.validate_text(txt).name == FSM.ValidationResult.NOK.name


def test_generated_fsm_rejects_invalid_parameter_type():
    fsm = build_fsm_from_definitions()
    txt = '{"name":"fn_add_numbers","parameters":{"a":"one","b":2}}'
    assert fsm.validate_text(txt).name == FSM.ValidationResult.NOK.name




