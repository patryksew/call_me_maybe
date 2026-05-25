import json
import random
from collections import OrderedDict

from src.models import FunctionDefinitions
from src.fsm import FSM


def load_definitions():
    with open("data/input/functions_definition.json") as f:
        return json.load(f)


def build_fsm_from_definitions():
    data = load_definitions()
    funcs = FunctionDefinitions.model_validate(data)
    return funcs.to_fsm(), funcs.functions


def generate_value(p_type: str):
    if p_type == "string":
        return random.choice(["Alice", "Bob", "", "hello world", "regex$^."])
    if p_type == "number":
        return random.choice([0, 1, -1, 3.14, 1e6, -2.5e-3])
    if p_type == "boolean":
        return random.choice([True, False])
    if p_type == "array":
        return [random.randint(0, 10) for _ in range(random.randint(0, 3))]
    if p_type == "object":
        return {"k": "v"}
    if p_type == "null":
        return None
    raise ValueError("Unknown type")


def instance_json_for_function(func):
    params = OrderedDict()
    has_array = False
    for k, v in func.parameters.items():
        p_type = v.get("type")
        if p_type == "array":
            has_array = True
        params[k] = generate_value(p_type)

    obj = OrderedDict()
    obj["name"] = func.name
    obj["parameters"] = params
    return json.dumps(obj), has_array
