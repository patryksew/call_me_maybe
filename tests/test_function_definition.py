"""pytest tests/test_function_definition.py -v
Example tests for FunctionDefinition and FunctionDefinitions models.

This test module demonstrates:
- Parsing and loading FunctionDefinition from JSON
- Validation of FunctionDefinition data
- Serialization to JSON format
- Working with FunctionDefinitions collections
"""

import json
import pytest
from pydantic import ValidationError

from src.models import FunctionDefinition, FunctionDefinitions


class TestFunctionDefinitionParsing:
    """Tests for parsing FunctionDefinition from JSON data."""

    def test_parse_simple_function_definition(self):
        """Example: Parse a simple function definition from dict."""
        data = {
            "name": "fn_add",
            "description": "Add two numbers",
            "parameters": {
                "a": {"type": "number"},
                "b": {"type": "number"}
            },
            "returns": {"type": "number"}
        }

        func_def = FunctionDefinition(**data)

        assert func_def.name == "fn_add"
        assert func_def.description == "Add two numbers"
        assert func_def.parameters == {"a": {"type": "number"}, "b": {"type": "number"}}
        assert func_def.returns == {"type": "number"}

    def test_parse_function_definition_from_json_string(self):
        """Example: Parse FunctionDefinition from JSON string using model_validate_json."""
        json_str = '''
        {
            "name": "fn_greet",
            "description": "Generate a greeting message",
            "parameters": {
                "name": {"type": "string"}
            },
            "returns": {"type": "string"}
        }
        '''

        func_def = FunctionDefinition.model_validate_json(json_str)

        assert func_def.name == "fn_greet"
        assert func_def.parameters == {"name": {"type": "string"}}

    def test_parse_function_with_multiple_parameters(self):
        """Example: Parse function with multiple different parameter types."""
        data = {
            "name": "fn_process",
            "description": "Process user data",
            "parameters": {
                "user_id": {"type": "number"},
                "email": {"type": "string"},
                "active": {"type": "boolean"},
                "tags": {"type": "array"}
            },
            "returns": {"type": "object"}
        }

        func_def = FunctionDefinition(**data)

        assert len(func_def.parameters) == 4
        assert func_def.parameters["user_id"]["type"] == "number"
        assert func_def.parameters["email"]["type"] == "string"
        assert func_def.parameters["active"]["type"] == "boolean"
        assert func_def.parameters["tags"]["type"] == "array"

    def test_parse_function_with_weird_whitespaces(self):
        """Example: Parse function definition with extra whitespaces in JSON."""
        json_str = '''
        {         "name":
         
         
         "fn_whitespace",         
            "description":         
            
                 "Function with weird whitespaces",
            "parameters":
             
                {
                "param1":   
                 
                  {"type":
                    
                     
                      
                      "string"},
                
                  
                "param2": {"type": "number"}
    },  
            "returns": {"type": 
             
              
               
               "boolean"}
        }
        '''

        func_def = FunctionDefinition.model_validate_json(json_str)

        assert func_def.name == "fn_whitespace"
        assert func_def.description == "Function with weird whitespaces"
        assert func_def.parameters["param1"]["type"] == "string"
        assert func_def.parameters["param2"]["type"] == "number"
        assert func_def.returns["type"] == "boolean"


class TestFunctionDefinitionValidation:
    """Tests for validation of FunctionDefinition data."""

    def test_validate_required_fields(self):
        """Example: Validation fails when required fields are missing."""
        incomplete_data = {
            "name": "fn_test",
            "description": "Test function"
            # Missing 'parameters' and 'returns'
        }

        with pytest.raises(ValidationError):
            FunctionDefinition(**incomplete_data)

    def test_validate_parameters_shape(self):
        """Example: Nested parameter shape is preserved."""
        data = {
            "name": "fn_test",
            "description": "Test",
            "parameters": {
                "param1": {"type": "string", "description": "ignored"},
                "param2": {"type": "number"}
            },
            "returns": {"type": "boolean"}
        }

        func_def = FunctionDefinition(**data)

        assert func_def.parameters == {
            "param1": {"type": "string", "description": "ignored"},
            "param2": {"type": "number"}
        }

    def test_validate_flat_parameters_rejected(self):
        """Example: Flat parameters are invalid with the nested schema."""
        data = {
            "name": "fn_test",
            "description": "Test",
            "parameters": {"param1": "string"},
            "returns": {"type": "boolean"}
        }

        with pytest.raises(ValidationError):
            FunctionDefinition(**data)

    def test_validate_empty_parameters(self):
        """Example: Function with no parameters is valid."""
        data = {
            "name": "fn_no_params",
            "description": "Function with no parameters",
            "parameters": {},
            "returns": {"type": "null"}
        }

        func_def = FunctionDefinition(**data)

        assert func_def.parameters == {}


class TestFunctionDefinitionSerialization:
    """Tests for serialization of FunctionDefinition to JSON."""

    def test_serialize_to_json(self):
        """Example: Serialize FunctionDefinition to JSON string."""
        func_def = FunctionDefinition(
            name="fn_compute",
            description="Compute something",
            parameters={"x": {"type": "number"}, "y": {"type": "number"}},
            returns={"type": "number"}
        )

        json_str = func_def.model_dump_json()
        data = json.loads(json_str)

        assert data["name"] == "fn_compute"
        assert data["parameters"]["x"] == {"type": "number"}
        assert data["parameters"]["y"] == {"type": "number"}

    def test_serialize_and_deserialize_roundtrip(self):
        """Example: Serialize to JSON and deserialize back to verify consistency."""
        original = FunctionDefinition(
            name="fn_roundtrip",
            description="Test roundtrip",
            parameters={"input": {"type": "string"}},
            returns={"type": "string"}
        )

        json_str = original.model_dump_json()
        restored = FunctionDefinition.model_validate_json(json_str)

        assert restored.name == original.name
        assert restored.description == original.description
        assert restored.parameters == original.parameters
        assert restored.returns == original.returns

    def test_serialize_to_dict(self):
        """Example: Serialize FunctionDefinition to dictionary."""
        func_def = FunctionDefinition(
            name="fn_dict_test",
            description="Test dict serialization",
            parameters={"a": {"type": "number"}},
            returns={"type": "number"}
        )

        data = func_def.model_dump()

        assert isinstance(data, dict)
        assert data["name"] == "fn_dict_test"
        assert data["parameters"] == {"a": {"type": "number"}}


class TestFunctionDefinitionsParsing:
    """Tests for parsing FunctionDefinitions collection."""

    def test_parse_function_definitions_list(self):
        """Example: Parse a list of FunctionDefinitions from JSON array."""
        json_str = '''
        [
            {
                "name": "fn_add",
                "description": "Add numbers",
                "parameters": {"a": {"type": "number"}, "b": {"type": "number"}},
                "returns": {"type": "number"}
            },
            {
                "name": "fn_greet",
                "description": "Greet user",
                "parameters": {"name": {"type": "string"}},
                "returns": {"type": "string"}
            }
        ]
        '''

        func_defs = FunctionDefinitions.model_validate_json(json_str)

        assert len(func_defs.functions) == 2
        assert func_defs.functions[0].name == "fn_add"
        assert func_defs.functions[1].name == "fn_greet"

    def test_parse_empty_function_definitions(self):
        """Example: Parse empty list of FunctionDefinitions."""
        json_str = '[]'

        func_defs = FunctionDefinitions.model_validate_json(json_str)

        assert len(func_defs.functions) == 0

    def test_access_functions_property(self):
        """Example: Access functions via the property."""
        data = [
            {
                "name": "fn_test",
                "description": "Test",
                "parameters": {},
                "returns": {"type": "null"}
            }
        ]

        func_defs = FunctionDefinitions.model_validate(data)

        assert func_defs.functions[0].name == "fn_test"


class TestFunctionDefinitionsValidation:
    """Tests for validation of FunctionDefinitions collection."""

    def test_validate_all_items_in_collection(self):
        """Example: All items in collection must be valid FunctionDefinitions."""
        invalid_data = [
            {
                "name": "fn_valid",
                "description": "Valid function",
                "parameters": {},
                "returns": {"type": "null"}
            },
            {
                "name": "fn_invalid",
                "description": "Invalid - missing returns"
                # Missing required 'returns' field
            }
        ]

        with pytest.raises(ValidationError):
            FunctionDefinitions.model_validate(invalid_data)

    def test_validate_flat_parameters_in_collection_rejected(self):
        """Example: Collection validation fails for flat parameter shapes."""
        invalid_data = [
            {
                "name": "fn_invalid",
                "description": "Invalid params",
                "parameters": {"x": "number"},
                "returns": {"type": "number"}
            }
        ]

        with pytest.raises(ValidationError):
            FunctionDefinitions.model_validate(invalid_data)


class TestFunctionDefinitionsSerialization:
    """Tests for serialization of FunctionDefinitions collection."""

    def test_serialize_collection_to_json(self):
        """Example: Serialize FunctionDefinitions collection to JSON."""
        func_defs = FunctionDefinitions.model_validate([
            {
                "name": "fn_one",
                "description": "First function",
                "parameters": {"x": {"type": "number"}},
                "returns": {"type": "number"}
            },
            {
                "name": "fn_two",
                "description": "Second function",
                "parameters": {},
                "returns": {"type": "string"}
            }
        ])

        json_str = func_defs.model_dump_json()
        data = json.loads(json_str)

        assert len(data) == 2
        assert data[0]["name"] == "fn_one"
        assert data[1]["name"] == "fn_two"

    def test_serialize_and_deserialize_collection_roundtrip(self):
        """Example: Roundtrip serialization of FunctionDefinitions collection."""
        original_funcs = [
            {
                "name": "fn_test1",
                "description": "Test 1",
                "parameters": {"p1": {"type": "string"}},
                "returns": {"type": "string"}
            },
            {
                "name": "fn_test2",
                "description": "Test 2",
                "parameters": {"p2": {"type": "number"}},
                "returns": {"type": "number"}
            }
        ]

        original = FunctionDefinitions.model_validate(original_funcs)
        json_str = original.model_dump_json()
        restored = FunctionDefinitions.model_validate_json(json_str)

        assert len(restored.functions) == len(original.functions)
        assert restored.functions[0].name == original.functions[0].name
        assert restored.functions[1].parameters == original.functions[1].parameters
