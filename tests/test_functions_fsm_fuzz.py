import json
import random
from collections import OrderedDict
from typing import Any

from src.models import FunctionDefinitions, FunctionDefinition
from src.fsm import FSM


def load_definitions() -> Any:
    """
    Load function definitions from a JSON file.

    :return: Parsed JSON data from the default functions definition file.
    """
    with open("data/input/functions_definition.json") as f:
        return json.load(f)


def build_fsm_from_definitions() -> tuple[FSM, list[FunctionDefinition]]:
    """
    Build an FSM from the loaded function definitions.

    :return: A tuple containing the constructed FSM and a list of
             FunctionDefinition objects.
    """
    data = load_definitions()
    funcs = FunctionDefinitions.model_validate(data)
    return funcs.to_fsm(), funcs.functions


def generate_value(p_type: str) -> Any:
    """
    Generate a random value based on the parameter type.

    :param p_type: The type of parameter to generate a value for.
    :return: A random value of the specified type.
    """
    if p_type == "string":
        return random.choice(["Alice", "Bob", "", "hello world", "regex$^."])
    if p_type == "number":
        # Numbers must be floats with decimal point, no exponent
        return random.choice([0.0, 1.0, -1.0, 3.14, 99.99, -2.5])
    if p_type in ["integer", "int"]:
        # Integers must be whole numbers without decimal point, no exponent
        return random.choice([0, 1, -1, 42, 100, -999])
    if p_type == "boolean":
        return random.choice([True, False])
    if p_type == "array":
        return [random.randint(0, 10) for _ in range(random.randint(0, 3))]
    if p_type == "object":
        return {"k": "v"}
    if p_type == "null":
        return None
    raise ValueError("Unknown type")


def instance_json_for_function(func: FunctionDefinition) -> tuple[str, bool]:
    """
    Generate a JSON string instance for a given function definition.

    :param func: The FunctionDefinition to generate JSON for.
    :return: A tuple containing the JSON string and a boolean indicating
             if it contains an array.
    """
    params: dict[str, Any] = OrderedDict()
    has_array = False
    for k, v in func.parameters.items():
        p_type = v.get("type")
        if p_type == "array":
            has_array = True
        if p_type is not None:
            params[k] = generate_value(p_type)

    obj: dict[str, Any] = OrderedDict()
    obj["name"] = func.name
    obj["parameters"] = params
    return json.dumps(obj), has_array
