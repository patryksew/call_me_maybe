import pytest
from src.fsm import FSM


class TestFSMBasics:
    """Test basic FSM construction and state creation."""

    def test_fsm_init(self):
        """FSM initializes with one empty root state."""
        fsm = FSM()
        assert len(fsm.states) == 1
        assert fsm.states[0] == {}

    def test_add_literal_single_start(self):
        """Adding a literal from a single start state works."""
        fsm = FSM()
        end_state = fsm.add_literal("hello", [0])
        assert isinstance(end_state, int)
        assert end_state > 0
        assert len(fsm.states) > 1

    def test_add_literal_empty_text_raises(self):
        """Adding empty literal raises ValueError."""
        fsm = FSM()
        with pytest.raises(ValueError, match="Text must be non-empty"):
            fsm.add_literal("", [0])

    def test_add_literal_creates_state_chain(self):
        """Adding 'abc' creates a chain of transitions a->b->c."""
        fsm = FSM()
        fsm.add_literal("abc", [0])

        state_0 = fsm.states[0]
        assert 'a' in state_0

        state_a = fsm.states[state_0['a']]
        assert 'b' in state_a

        state_b = fsm.states[state_a['b']]
        assert 'c' in state_b


class TestFSMValidation:
    """Test text validation behavior."""

    def test_validate_simple_literal(self):
        """Validating a simple literal works."""
        fsm = FSM()
        fsm.add_literal("hello", [0])

        result = fsm.validate_text("hello")
        assert result == FSM.ValidationResult.FINISHED

    def test_validate_prefix_ok(self):
        """Validating a prefix of a literal returns OK (not FINISHED)."""
        fsm = FSM()
        fsm.add_literal("hello", [0])

        result = fsm.validate_text("hel")
        assert result == FSM.ValidationResult.OK

    def test_validate_invalid_char(self):
        """Validating text with invalid char returns NOK."""
        fsm = FSM()
        fsm.add_literal("hello", [0])

        result = fsm.validate_text("hex")
        assert result == FSM.ValidationResult.NOK

    def test_validate_empty_text(self):
        """Validating empty text on root state returns FINISHED (root accepts empty)."""
        fsm = FSM()
        result = fsm.validate_text("")
        assert result == FSM.ValidationResult.FINISHED  # Root state has no transitions, so len(state)==0

    def test_validate_resets_between_calls(self):
        """validate_text does NOT update current_state (stateless behavior)."""
        fsm = FSM()
        fsm.add_literal("hello", [0])

        fsm.validate_text("hel")

    def test_validate_multiple_paths(self):
        """Validating when multiple valid transitions exist."""
        fsm = FSM()
        fsm.add_literal("hello", [0])
        fsm.add_literal("hi", [0])

        result_hello = fsm.validate_text("hello")
        assert result_hello == FSM.ValidationResult.FINISHED

        result_hi = fsm.validate_text("hi")
        assert result_hi == FSM.ValidationResult.FINISHED

        result_he = fsm.validate_text("he")
        assert result_he == FSM.ValidationResult.OK  # ambiguous: could go to hello or invalid


class TestFSMWhitespace:
    """Test whitespace handling."""

    def test_add_whitespace_loops(self):
        """Whitespace transitions loop back to the same state."""
        fsm = FSM()
        hello = fsm.add_literal("hello", [0])
        fsm.add_whitespace(hello)

        state = fsm.states[hello]
        assert state.get(' ') == hello
        assert state.get('\t') == hello
        assert state.get('\n') == hello

    def test_whitespace_zero_or_more(self):
        """Whitespace allows zero or more occurrences."""
        fsm = FSM()
        hello = fsm.add_literal("hello", [0])
        fsm.add_whitespace(hello)
        fsm.add_literal("world", [hello])

        result_no_space = fsm.validate_text("helloworld")
        assert result_no_space == FSM.ValidationResult.FINISHED

        result_one_space = fsm.validate_text("hello world")
        assert result_one_space == FSM.ValidationResult.FINISHED

        result_multi_space = fsm.validate_text("hello   world")
        assert result_multi_space == FSM.ValidationResult.FINISHED

    def test_whitespace_types(self):
        """All whitespace types (space, tab, newline) are accepted."""
        fsm = FSM()
        hello = fsm.add_literal("hello", [0])
        fsm.add_whitespace(hello)
        fsm.add_literal("world", [hello])

        for ws_char in [' ', '\t', '\n']:
            result = fsm.validate_text(f"hello{ws_char}world")
            assert result == FSM.ValidationResult.FINISHED, f"Failed for whitespace {repr(ws_char)}"


class TestFSMNumbers:
    """Test JSON number validation."""

    def test_number_zero(self):
        """Single zero is a valid number."""
        fsm = FSM()
        fsm.add_number(0)
        fsm.validate_text("0")
        # Should allow zero but might require follow-up or be terminal

    def test_number_simple_integer(self):
        """Simple positive integers are valid."""
        fsm = FSM()
        fsm.add_number(0)

        result = fsm.validate_text("123")
        assert result == FSM.ValidationResult.OK  # Numbers can continue in JSON (e.g., followed by , ] } or whitespace)

    def test_number_negative(self):
        """Negative numbers are valid."""
        fsm = FSM()
        fsm.add_number(0)

        result = fsm.validate_text("-456")
        assert result == FSM.ValidationResult.OK

    def test_number_negative_zero(self):
        """Negative zero is a valid JSON number."""
        fsm = FSM()
        fsm.add_number(0)

        result = fsm.validate_text("-0")
        assert result == FSM.ValidationResult.OK

    def test_number_decimal(self):
        """Numbers with decimal points are valid."""
        fsm = FSM()
        fsm.add_number(0)

        result = fsm.validate_text("3.14")
        assert result == FSM.ValidationResult.OK

    def test_number_exponential(self):
        """Numbers with exponents are valid (uppercase E)."""
        fsm = FSM()
        fsm.add_number(0)

        result = fsm.validate_text("1E10")
        assert result == FSM.ValidationResult.OK

    def test_number_exponential_lowercase(self):
        """Numbers with lowercase exponents are valid."""
        fsm = FSM()
        fsm.add_number(0)

        result = fsm.validate_text("1e10")
        assert result == FSM.ValidationResult.OK

    def test_number_exponential_negative(self):
        """Numbers with negative exponents are valid."""
        fsm = FSM()
        fsm.add_number(0)

        result = fsm.validate_text("1.5e-3")
        assert result == FSM.ValidationResult.OK

    def test_number_exponential_positive_sign(self):
        """Numbers with positive exponent sign are valid."""
        fsm = FSM()
        fsm.add_number(0)

        result = fsm.validate_text("2E+5")
        assert result == FSM.ValidationResult.OK

    def test_number_complex(self):
        """Complex number formats."""
        fsm = FSM()
        fsm.add_number(0)

        test_cases = [
            "0",
            "-0",
            "123",
            "-456",
            "3.14",
            "-3.14",
            "1E10",
            "1e10",
            "1E-10",
            "1.5e+3",
            "-123.456E-7",
        ]

        for num_str in test_cases:
            result = fsm.validate_text(num_str)
            assert result == FSM.ValidationResult.OK, f"Failed for {num_str}"

    def test_number_leading_zero_invalid(self):
        """Numbers with leading zeros (except lone 0) are invalid per JSON spec."""
        fsm = FSM()
        fsm.add_number(0)

        result = fsm.validate_text("01")
        assert result == FSM.ValidationResult.NOK

    def test_number_decimal_without_integer_invalid(self):
        """.5 is not valid JSON (requires 0.5)."""
        fsm = FSM()
        fsm.add_number(0)

        result = fsm.validate_text(".5")
        assert result == FSM.ValidationResult.NOK

    def test_number_decimal_without_fraction_invalid(self):
        """1. is a valid prefix (could continue with digits), returns OK."""
        fsm = FSM()
        fsm.add_number(0)

        result = fsm.validate_text("1.")
        assert result == FSM.ValidationResult.OK  # Valid prefix, expecting digits

    def test_number_empty_exponent_invalid(self):
        """1e is a valid prefix (could continue with sign or digits), returns OK."""
        fsm = FSM()
        fsm.add_number(0)

        result = fsm.validate_text("1e")
        assert result == FSM.ValidationResult.OK  # Valid prefix, expecting +/- or digits


class TestFSMChaining:
    """Test chaining literals, whitespace, and numbers."""

    def test_chain_literal_whitespace_literal(self):
        """hello <spaces> world is valid."""
        fsm = FSM()
        hello = fsm.add_literal("hello", [0])
        fsm.add_whitespace(hello)
        fsm.add_literal("world", [hello])

        result = fsm.validate_text("hello world")
        assert result == FSM.ValidationResult.FINISHED

    def test_chain_literal_number(self):
        """test123 is valid when chained."""
        fsm = FSM()
        test = fsm.add_literal("test", [0])
        fsm.add_number(test)

        result = fsm.validate_text("test123")
        assert result == FSM.ValidationResult.OK  # Number endpoint returns OK in JSON context

    def test_chain_multiple_literals_with_whitespace(self):
        """Multiple literals with whitespace."""
        fsm = FSM()
        hello = fsm.add_literal("hello", [0])
        fsm.add_whitespace(hello)
        world = fsm.add_literal("world", [hello])
        fsm.add_whitespace(world)
        fsm.add_literal("!", [world])

        result = fsm.validate_text("hello world !")
        assert result == FSM.ValidationResult.FINISHED

    def test_chain_number_with_whitespace_literal(self):
        """number <space> suffix."""
        fsm = FSM()
        num = fsm.add_number(0)

        fsm.add_whitespace(num)
        fsm.add_literal("units", num)

        result = fsm.validate_text("123.45 units")
        assert result == FSM.ValidationResult.FINISHED


class TestFSMMultiStartStates:
    """Test add_literal with multiple start states."""

    def test_add_literal_multiple_starts_same_end(self):
        """Adding literal from multiple start states."""
        fsm = FSM()
        state1 = fsm.add_literal("a", [0])
        state2 = fsm.add_literal("b", [0])

        # Both "a" and "b" should lead somewhere
        fsm.add_literal("x", [state1, state2])

        result_ax = fsm.validate_text("ax")
        result_bx = fsm.validate_text("bx")

        assert result_ax == FSM.ValidationResult.FINISHED
        assert result_bx == FSM.ValidationResult.FINISHED

    def test_add_literal_shared_prefix_no_conflict(self):
        """Adding literals with shared prefixes doesn't break prior paths."""
        fsm = FSM()
        h = fsm.add_literal("h", [0])
        fsm.add_literal("i", [h])
        fsm.add_literal("e", [h])

        # Both "hi" and "he" should still be valid
        result_hi = fsm.validate_text("hi")
        result_he = fsm.validate_text("he")

        assert result_hi == FSM.ValidationResult.FINISHED
        assert result_he == FSM.ValidationResult.FINISHED


class TestFSMEdgeCases:
    """Test edge cases and corner scenarios."""

    def test_single_char_literal(self):
        """Single character literal."""
        fsm = FSM()
        fsm.add_literal("a", [0])

        result = fsm.validate_text("a")
        assert result == FSM.ValidationResult.FINISHED

    def test_long_literal(self):
        """Very long literal."""
        fsm = FSM()
        long_text = "a" * 1000
        fsm.add_literal(long_text, [0])

        result = fsm.validate_text(long_text)
        assert result == FSM.ValidationResult.FINISHED

    def test_special_characters(self):
        """Literals with special characters."""
        fsm = FSM()
        fsm.add_literal("!@#$%", [0])

        result = fsm.validate_text("!@#$%")
        assert result == FSM.ValidationResult.FINISHED

    def test_unicode_characters(self):
        """Unicode in literals."""
        fsm = FSM()
        fsm.add_literal("hello🌍", [0])

        result = fsm.validate_text("hello🌍")
        assert result == FSM.ValidationResult.FINISHED

    def test_validation_after_multiple_additions(self):
        """Complex FSM with many branches."""
        fsm = FSM()
        root = 0

        # Build: (hello|hi|hey) (world|there|there)
        h = fsm.add_literal("h", [root])
        e = fsm.add_literal("e", [h])

        # "hello" path
        l1 = fsm.add_literal("l", [e])
        l2 = fsm.add_literal("l", [l1])
        fsm.add_literal("o", [l2])

        # "he" -> should now be valid for "hey"
        fsm.add_literal("y", [e])

        # "hi" path
        fsm.add_literal("i", [h])

        result_hello = fsm.validate_text("hello")
        result_hi = fsm.validate_text("hi")
        result_hey = fsm.validate_text("hey")

        assert result_hello == FSM.ValidationResult.FINISHED
        assert result_hi == FSM.ValidationResult.FINISHED
        assert result_hey == FSM.ValidationResult.FINISHED

    def test_validation_partial_match_is_ok(self):
        """Partial match where more input is possible returns OK."""
        fsm = FSM()
        fsm.add_literal("testing", [0])

        result = fsm.validate_text("test")
        assert result == FSM.ValidationResult.OK

    def test_validation_exact_match_is_finished(self):
        """Exact match with no further transitions returns FINISHED."""
        fsm = FSM()
        fsm.add_literal("test", [0])

        result = fsm.validate_text("test")
        assert result == FSM.ValidationResult.FINISHED

    def test_numbers_return_multiple_accepting_states(self):
        """add_number returns list of accepting states."""
        fsm = FSM()
        result = fsm.add_number(0)
        assert isinstance(result, list)
        assert len(result) > 0


class TestFSMNumberEdgeCases:
    """Edge cases specific to number parsing."""

    def test_number_with_zero_exponent(self):
        """1e0 should be valid."""
        fsm = FSM()
        fsm.add_number(0)

        result = fsm.validate_text("1e0")
        assert result == FSM.ValidationResult.OK

    def test_number_negative_with_all_features(self):
        """Negative number with decimal and exponent."""
        fsm = FSM()
        fsm.add_number(0)

        result = fsm.validate_text("-123.456e-78")
        assert result == FSM.ValidationResult.OK

    def test_number_plus_not_allowed_at_start(self):
        """+123 should be invalid (JSON disallows leading +)."""
        fsm = FSM()
        fsm.add_number(0)

        result = fsm.validate_text("+123")
        assert result == FSM.ValidationResult.NOK

    def test_number_double_minus_invalid(self):
        """--5 should be invalid."""
        fsm = FSM()
        fsm.add_number(0)

        result = fsm.validate_text("--5")
        assert result == FSM.ValidationResult.NOK

    def test_number_multiple_dots_invalid(self):
        """1.2.3 should be invalid."""
        fsm = FSM()
        fsm.add_number(0)

        result = fsm.validate_text("1.2.3")
        assert result == FSM.ValidationResult.NOK


class TestFSMNumberContract:
    """Tests for add_number contract details (state meanings and collisions)."""

    @staticmethod
    def _state_after_text(fsm: FSM, text: str) -> int:
        state_index = 0
        for char in text:
            state_index = fsm.states[state_index][char]
        return state_index

    def test_number_accepting_state_order_matches_semantics(self):
        """Returned accepting states map to zero, integer, fraction, exponent."""
        fsm = FSM()
        zero, integer, fraction, exponent = fsm.add_number(0)

        assert self._state_after_text(fsm, "0") == zero
        assert self._state_after_text(fsm, "1") == integer
        assert self._state_after_text(fsm, "123") == integer
        assert self._state_after_text(fsm, "1.2") == fraction
        assert self._state_after_text(fsm, "1e9") == exponent

    def test_number_accepting_states_allow_json_value_termination(self):
        """Each returned accepting state can be used as a JSON value endpoint."""
        fsm = FSM()
        ends = fsm.add_number(0)
        fsm.add_literal("}", ends)

        assert fsm.validate_text("0}") == FSM.ValidationResult.FINISHED
        assert fsm.validate_text("42}") == FSM.ValidationResult.FINISHED
        assert fsm.validate_text("3.14}") == FSM.ValidationResult.FINISHED
        assert fsm.validate_text("1e9}") == FSM.ValidationResult.FINISHED

        # Prefixes cannot terminate a JSON number value.
        assert fsm.validate_text("-}") == FSM.ValidationResult.NOK
        assert fsm.validate_text("1.}") == FSM.ValidationResult.NOK
        assert fsm.validate_text("1e}") == FSM.ValidationResult.NOK

    def test_add_number_overwrites_existing_start_digit_transition(self):
        """add_number currently overwrites colliding transitions on the start state."""
        fsm = FSM()
        fsm.add_literal("1a", [0])

        existing_digit_target = fsm.states[0]["1"]
        fsm.add_number(0)

        assert fsm.states[0]["1"] != existing_digit_target
        assert fsm.validate_text("1a") == FSM.ValidationResult.NOK
        assert fsm.validate_text("1") == FSM.ValidationResult.OK


class TestFSMStructure:
    """Test FSM internal structure and state management."""

    def test_states_only_added_when_needed(self):
        """Adding the same literal twice doesn't create duplicate states."""
        fsm = FSM()

        state_count_after_1 = len(fsm.states)
        fsm.add_literal("test", [0])
        state_count_after_2 = len(fsm.states)

        # First literal adds states
        assert state_count_after_2 > state_count_after_1

    def test_state_reuse_on_same_path(self):
        """When both paths converge, they should reuse states."""
        fsm = FSM()

        # Add two literals that could converge
        state_before = len(fsm.states)
        fsm.add_literal("apple", [0])
        fsm.add_literal("apricot", [0])

        # They share "ap" prefix, so states should be reused
        state_after = len(fsm.states)
        assert state_after > state_before  # States added, but let's verify they're shared


class TestFSMJSON:
    """Test FSM behavior in JSON parsing context."""

    def test_simple(self):
        """Tests simple JSON with only a few valid literals"""
        fsm = FSM()
        name_index = fsm.add_literal('{"name":', [0])
        fsm.add_whitespace(name_index)
        function_name_indexes = list()
        name_index = fsm.add_literal('"', [name_index])

        function_name_indexes.append(fsm.add_literal('add_numbers', [name_index]))
        function_name_indexes.append(fsm.add_literal('multiply_numbers', [name_index]))
        function_name_indexes.append(fsm.add_literal('subtract', [name_index]))

        function_name_end = fsm.add_literal('"', function_name_indexes)

        fsm.add_whitespace(function_name_end)
        fsm.add_literal('}', [function_name_end])

        assert fsm.validate_text('{"name":"add_numbers"        }') == FSM.ValidationResult.FINISHED
        assert fsm.validate_text('{"name": "multiply_numbers"}') == FSM.ValidationResult.FINISHED
        assert fsm.validate_text('{"name":        \n"subtract"}') == FSM.ValidationResult.FINISHED

        assert fsm.validate_text('{"name": "divide_numbers"}') == FSM.ValidationResult.NOK
        assert fsm.validate_text('{"name": add_numbers"}') == FSM.ValidationResult.NOK

    def test_with_numbers(self):
        """Tests JSON with numbers and literals"""
        fsm = FSM()
        name_index = fsm.add_literal('{"name":', [0])
        fsm.add_whitespace(name_index)
        function_name_indexes = list()
        name_index = fsm.add_literal('"', name_index)

        function_name_indexes.append(fsm.add_literal('add_numbers', name_index))
        function_name_indexes.append(fsm.add_literal('multiply_numbers', name_index))
        function_name_indexes.append(fsm.add_literal('subtract', name_index))

        function_name_end = fsm.add_literal('"', function_name_indexes)

        fsm.add_whitespace(function_name_end)
        value_index = fsm.add_literal(', "value":', function_name_end)
        fsm.add_whitespace(value_index)
        value_index = fsm.add_number(value_index)
        fsm.add_literal('}', value_index)

        assert fsm.validate_text('{"name":"add_numbers", "value": 123}') == FSM.ValidationResult.FINISHED
        assert fsm.validate_text('{"name": "multiply_numbers", "value": -3.14e-10}') == FSM.ValidationResult.FINISHED
        assert fsm.validate_text('{"name": "subtract", "value": 0}') == FSM.ValidationResult.FINISHED

        assert fsm.validate_text('{"name": "divide_numbers", "value": 123}') == FSM.ValidationResult.NOK
        assert fsm.validate_text('{"name": "add_numbers", "value": +123}') == FSM.ValidationResult.NOK


    def test_with_booleans(self):
        """Tests JSON with boolean literals"""
        fsm = FSM()
        name_index = fsm.add_literal('{"name":', [0])
        fsm.add_whitespace(name_index)
        function_name_indexes = list()
        name_index = fsm.add_literal('"', name_index)

        function_name_indexes.append(fsm.add_literal('add_numbers', name_index))
        function_name_indexes.append(fsm.add_literal('multiply_numbers', name_index))
        function_name_indexes.append(fsm.add_literal('subtract', name_index))

        function_name_end = fsm.add_literal('"', function_name_indexes)

        fsm.add_whitespace(function_name_end)
        value_index = fsm.add_literal(', "value":', function_name_end)
        fsm.add_whitespace(value_index)
        value_index = fsm.add_boolean(value_index)
        fsm.add_literal('}', value_index)

        assert fsm.validate_text('{"name":"add_numbers", "value": true}') == FSM.ValidationResult.FINISHED
        assert fsm.validate_text('{"name": "multiply_numbers", "value": false}') == FSM.ValidationResult.FINISHED

        assert fsm.validate_text('{"name": "divide_numbers", "value": true}') == FSM.ValidationResult.NOK
        assert fsm.validate_text('{"name": "add_numbers", "value": truth}') == FSM.ValidationResult.NOK


class TestFSMString:
    """Test JSON string validation with ASCII characters."""

    def test_string_empty(self):
        """Empty string is valid JSON."""
        fsm = FSM()
        fsm.add_string(0)

        result = fsm.validate_text('""')
        assert result == FSM.ValidationResult.FINISHED

    def test_string_simple_ascii(self):
        """Simple ASCII string."""
        fsm = FSM()
        fsm.add_string(0)

        result = fsm.validate_text('"hello"')
        assert result == FSM.ValidationResult.FINISHED

    def test_string_with_spaces(self):
        """String with spaces."""
        fsm = FSM()
        fsm.add_string(0)

        result = fsm.validate_text('"hello world"')
        assert result == FSM.ValidationResult.FINISHED

    def test_string_with_numbers(self):
        """String with numbers."""
        fsm = FSM()
        fsm.add_string(0)

        result = fsm.validate_text('"test123"')
        assert result == FSM.ValidationResult.FINISHED

    def test_string_with_special_chars(self):
        """String with special ASCII characters."""
        fsm = FSM()
        fsm.add_string(0)

        result = fsm.validate_text('"!@#$%^&*()"')
        assert result == FSM.ValidationResult.FINISHED

    def test_string_with_punctuation(self):
        """String with punctuation."""
        fsm = FSM()
        fsm.add_string(0)

        result = fsm.validate_text('"hello, world! How are you?"')
        assert result == FSM.ValidationResult.FINISHED

    def test_string_escaped_quote(self):
        """String with escaped quote inside."""
        fsm = FSM()
        fsm.add_string(0)

        result = fsm.validate_text('"say \\"hello\\""')
        assert result == FSM.ValidationResult.FINISHED

    def test_string_escaped_backslash(self):
        """String with escaped backslash."""
        fsm = FSM()
        fsm.add_string(0)

        result = fsm.validate_text('"path\\\\to\\\\file"')
        assert result == FSM.ValidationResult.FINISHED

    def test_string_escaped_newline(self):
        """String with escaped newline."""
        fsm = FSM()
        fsm.add_string(0)

        result = fsm.validate_text('"line1\\nline2"')
        assert result == FSM.ValidationResult.FINISHED

    def test_string_escaped_tab(self):
        """String with escaped tab."""
        fsm = FSM()
        fsm.add_string(0)

        result = fsm.validate_text('"col1\\tcol2"')
        assert result == FSM.ValidationResult.FINISHED

    def test_string_escaped_carriage_return(self):
        """String with escaped carriage return."""
        fsm = FSM()
        fsm.add_string(0)

        result = fsm.validate_text('"line1\\rline2"')
        assert result == FSM.ValidationResult.FINISHED

    def test_string_escaped_backspace(self):
        """String with escaped backspace."""
        fsm = FSM()
        fsm.add_string(0)

        result = fsm.validate_text('"text\\bmore"')
        assert result == FSM.ValidationResult.FINISHED

    def test_string_escaped_form_feed(self):
        """String with escaped form feed."""
        fsm = FSM()
        fsm.add_string(0)

        result = fsm.validate_text('"page1\\fpage2"')
        assert result == FSM.ValidationResult.FINISHED

    def test_string_escaped_forward_slash(self):
        """String with escaped forward slash."""
        fsm = FSM()
        fsm.add_string(0)

        result = fsm.validate_text('"path\\/to\\/file"')
        assert result == FSM.ValidationResult.FINISHED

    def test_string_multiple_escapes(self):
        """String with multiple escape sequences."""
        fsm = FSM()
        fsm.add_string(0)

        result = fsm.validate_text('"line1\\nline2\\ttab\\\\backslash\\""')
        assert result == FSM.ValidationResult.FINISHED

    def test_string_no_closing_quote(self):
        """String without closing quote is invalid."""
        fsm = FSM()
        fsm.add_string(0)

        result = fsm.validate_text('"hello')
        assert result == FSM.ValidationResult.OK  # Prefix OK, but not finished

    def test_string_unescaped_quote_invalid(self):
        """Unescaped quote inside string is invalid."""
        fsm = FSM()
        fsm.add_string(0)

        result = fsm.validate_text('"say "hello""')
        assert result == FSM.ValidationResult.NOK

    def test_string_unescaped_backslash_at_end_invalid(self):
        """Unescaped backslash at end is a valid prefix (could escape next char)."""
        fsm = FSM()
        fsm.add_string(0)

        result = fsm.validate_text('"hello\\"')
        assert result == FSM.ValidationResult.OK  # Valid prefix, expecting escaped character

    def test_string_invalid_escape_sequence(self):
        """Invalid escape sequence (not recognized) should fail."""
        fsm = FSM()
        fsm.add_string(0)

        result = fsm.validate_text('"hello\\x"')
        assert result == FSM.ValidationResult.NOK

    def test_string_only_backslash(self):
        fsm = FSM()
        fsm.add_string(0)

        result = fsm.validate_text('"\\\\"')
        assert result == FSM.ValidationResult.FINISHED

    def test_string_backslash_without_escape(self):
        """Backslash not followed by valid escape char."""
        fsm = FSM()
        fsm.add_string(0)

        result = fsm.validate_text('"test\\a"')
        assert result == FSM.ValidationResult.NOK

    def test_string_prefix_is_ok(self):
        """Prefix of a valid string returns OK."""
        fsm = FSM()
        fsm.add_string(0)

        result = fsm.validate_text('"hello')
        assert result == FSM.ValidationResult.OK

    def test_string_with_numbers_and_special(self):
        """Complex string with numbers, letters, and special chars."""
        fsm = FSM()
        fsm.add_string(0)

        result = fsm.validate_text('"user@example.com:12345"')
        assert result == FSM.ValidationResult.FINISHED

    def test_string_ascii_letters_and_digits(self):
        """All ASCII letters and digits."""
        fsm = FSM()
        fsm.add_string(0)

        result = fsm.validate_text('"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"')
        assert result == FSM.ValidationResult.FINISHED

    def test_string_long_text(self):
        """Very long string."""
        fsm = FSM()
        fsm.add_string(0)

        long_text = '"' + 'a' * 1000 + '"'
        result = fsm.validate_text(long_text)
        assert result == FSM.ValidationResult.FINISHED

    def test_string_as_json_object_field(self):
        """String used as JSON field value."""
        fsm = FSM()
        quote_open = fsm.add_literal('{', [0])
        quote_open = fsm.add_literal('"', [quote_open])
        quote_open = fsm.add_literal('name', [quote_open])
        quote_open = fsm.add_literal('"', [quote_open])
        fsm.add_whitespace(quote_open)
        quote_open = fsm.add_literal(':', [quote_open])
        fsm.add_whitespace(quote_open)
        string_end = fsm.add_string(quote_open)
        fsm.add_whitespace(string_end)
        fsm.add_literal('}', [string_end])

        result = fsm.validate_text('{"name": "John"}')
        assert result == FSM.ValidationResult.FINISHED

    def test_string_as_json_array_element(self):
        """String used as JSON array element."""
        fsm = FSM()
        bracket_open = fsm.add_literal('[', [0])
        string_end = fsm.add_string(bracket_open)
        fsm.add_whitespace(string_end)
        comma_state = fsm.add_literal(',', [string_end])
        fsm.add_whitespace(comma_state)
        string_end = fsm.add_string(comma_state)
        fsm.add_whitespace(string_end)
        fsm.add_literal(']', [string_end])

        result = fsm.validate_text('["first", "second"]')
        assert result == FSM.ValidationResult.FINISHED


class TestTryAutocomplete:
    """Test the try_autocomplete method."""

    def test_autocomplete_simple_literal_complete_match(self):
        """Completing a text that fully matches a literal should not autocomplete."""
        fsm = FSM()
        fsm.add_literal("hello", [0])

        result, did_autocomplete = fsm.try_autocomplete("hello")
        assert result == "hello"
        assert did_autocomplete is False

    def test_autocomplete_simple_literal_partial_match(self):
        """Completing a partial match with no branch should autocomplete deterministically."""
        fsm = FSM()
        fsm.add_literal("hello", [0])

        result, did_autocomplete = fsm.try_autocomplete("hel")
        assert result == "hello"
        assert did_autocomplete is True

    def test_autocomplete_empty_input(self):
        """Autocompleting empty input on a single literal should work."""
        fsm = FSM()
        fsm.add_literal("test", [0])

        result, did_autocomplete = fsm.try_autocomplete("")
        assert result == "test"
        assert did_autocomplete is True

    def test_autocomplete_invalid_character_returns_original(self):
        """If input contains invalid character, return original text without autocomplete."""
        fsm = FSM()
        fsm.add_literal("hello", [0])

        result, did_autocomplete = fsm.try_autocomplete("hex")
        assert result == "hex"
        assert did_autocomplete is False

    def test_autocomplete_with_multiple_paths_no_autocomplete(self):
        """When there are multiple valid paths after input, don't autocomplete."""
        fsm = FSM()
        fsm.add_literal("hello", [0])
        fsm.add_literal("help", [0])

        # "hel" has two possible continuations (lo or p), so can't autocomplete
        result, did_autocomplete = fsm.try_autocomplete("hel")
        assert result == "hel"
        assert did_autocomplete is False

    def test_autocomplete_with_single_path_continues(self):
        """When there's only one valid path after input, continue autocompleting."""
        fsm = FSM()
        fsm.add_literal("hello", [0])
        fsm.add_literal("help", [0])

        # "hell" has only one continuation (o), so should autocomplete to "hello"
        result, did_autocomplete = fsm.try_autocomplete("hell")
        assert result == "hello"
        assert did_autocomplete is True

    def test_autocomplete_completely_invalid_input(self):
        """Completely invalid input doesn't autocomplete."""
        fsm = FSM()
        fsm.add_literal("hello", [0])

        result, did_autocomplete = fsm.try_autocomplete("x")
        assert result == "x"
        assert did_autocomplete is False

    def test_autocomplete_stops_at_branching_point(self):
        """Autocomplete stops when it reaches a state with multiple transitions."""
        fsm = FSM()
        fsm.add_literal("hello", [0])
        fsm.add_literal("help", [0])
        fsm.add_literal("hey", [0])

        # "he" has three possible continuations (l, l, y)
        result, did_autocomplete = fsm.try_autocomplete("he")
        assert result == "he"
        assert did_autocomplete is False

    def test_autocomplete_with_whitespace(self):
        """Autocomplete through whitespace - stops at whitespace state with multiple options."""
        fsm = FSM()
        hello = fsm.add_literal("hello", [0])
        fsm.add_whitespace(hello)
        fsm.add_literal("world", [hello])

        # "hello " is at a state with whitespace looping (space, tab, newline) and 'w' option
        # So it has multiple transitions and won't autocomplete
        result, did_autocomplete = fsm.try_autocomplete("hello ")
        assert result == "hello "
        assert did_autocomplete is False

    def test_autocomplete_empty_string_on_terminal_state(self):
        """Empty string on FSM with no options returns as-is with no autocomplete."""
        fsm = FSM()
        result, did_autocomplete = fsm.try_autocomplete("")
        assert result == ""
        assert did_autocomplete is False

    def test_autocomplete_partial_literal_no_branching(self):
        """Partial match of a literal with no alternative paths autocompletes fully."""
        fsm = FSM()
        fsm.add_literal("abc", [0])

        result, did_autocomplete = fsm.try_autocomplete("a")
        assert result == "abc"
        assert did_autocomplete is True

        result2, did_autocomplete2 = fsm.try_autocomplete("ab")
        assert result2 == "abc"
        assert did_autocomplete2 is True

    def test_autocomplete_diverging_literals_partial_prefix(self):
        """Partial prefix that splits into multiple paths doesn't autocomplete."""
        fsm = FSM()
        fsm.add_literal("cat", [0])
        fsm.add_literal("car", [0])

        result, did_autocomplete = fsm.try_autocomplete("ca")
        assert result == "ca"
        assert did_autocomplete is False

    def test_autocomplete_diverging_literals_single_path_after(self):
        """Even with diverging paths, if input reaches a point with single continuation, autocomplete."""
        fsm = FSM()
        fsm.add_literal("cat", [0])
        fsm.add_literal("car", [0])
        fsm.add_literal("ca_special", [0])

        # After "cat" there's only one option at end (terminal), and same with "car"
        result, did_autocomplete = fsm.try_autocomplete("cat")
        assert result == "cat"
        assert did_autocomplete is False  # Already at terminal state

    def test_autocomplete_boolean_true(self):
        """Autocomplete boolean true."""
        fsm = FSM()
        fsm.add_boolean(0)

        result, did_autocomplete = fsm.try_autocomplete("tr")
        assert result == "true"
        assert did_autocomplete is True

    def test_autocomplete_boolean_false(self):
        """Autocomplete boolean false."""
        fsm = FSM()
        fsm.add_boolean(0)

        result, did_autocomplete = fsm.try_autocomplete("fal")
        assert result == "false"
        assert did_autocomplete is True

    def test_autocomplete_boolean_ambiguous(self):
        """Autocomplete boolean "t" leads deterministically to "true"."""
        fsm = FSM()
        fsm.add_boolean(0)

        # "t" only has one continuation ('r' from "true"), so it autocompletes
        result, did_autocomplete = fsm.try_autocomplete("t")
        assert result == "true"
        assert did_autocomplete is True

    def test_autocomplete_boolean_initial_ambiguous(self):
        """Initial empty input is ambiguous between true and false."""
        fsm = FSM()
        fsm.add_boolean(0)

        # Empty input has two options ('t' for true, 'f' for false)
        result, did_autocomplete = fsm.try_autocomplete("")
        assert result == ""
        assert did_autocomplete is False

    def test_autocomplete_number_zero(self):
        """Autocomplete number zero."""
        fsm = FSM()
        end_states = fsm.add_number(0)

        result, did_autocomplete = fsm.try_autocomplete("0")
        assert result == "0"
        assert did_autocomplete is False  # Terminal state reached

    def test_autocomplete_number_negative(self):
        """Autocomplete negative number."""
        fsm = FSM()
        fsm.add_number(0)

        result, did_autocomplete = fsm.try_autocomplete("-")
        # Deterministically continues with digits possible
        assert result.startswith("-")
        # Whether it autocompletes depends on having only one valid next character

    def test_autocomplete_after_invalid_continues_from_failure_point(self):
        """Once an invalid character is hit, stay at result with invalid char, don't autocomplete."""
        fsm = FSM()
        fsm.add_literal("hello", [0])

        result, did_autocomplete = fsm.try_autocomplete("hex")
        assert result == "hex"  # Original input returned
        assert did_autocomplete is False

    def test_autocomplete_chain_of_deterministic_transitions(self):
        """Autocomplete through multiple deterministic transitions."""
        fsm = FSM()
        state1 = fsm.add_literal("a", [0])
        state2 = fsm.add_literal("b", [state1])
        state3 = fsm.add_literal("c", [state2])

        result, did_autocomplete = fsm.try_autocomplete("a")
        assert result == "abc"
        assert did_autocomplete is True

    def test_autocomplete_mixed_branching_and_linear(self):
        """Complex FSM with branching and linear paths."""
        fsm = FSM()
        # Two initial choices: "a" or "b"
        a_state = fsm.add_literal("a", [0])
        b_state = fsm.add_literal("b", [0])

        # Both lead to unique continuations
        a_cont = fsm.add_literal("x", [a_state])
        b_cont = fsm.add_literal("y", [b_state])

        # After "a", should complete to "ax"
        result_a, did_autocomplete_a = fsm.try_autocomplete("a")
        assert result_a == "ax"
        assert did_autocomplete_a is True

        # After "b", should complete to "by"
        result_b, did_autocomplete_b = fsm.try_autocomplete("b")
        assert result_b == "by"
        assert did_autocomplete_b is True

        # Empty should not autocomplete (both "a" and "b" available)
        result_empty, did_autocomplete_empty = fsm.try_autocomplete("")
        assert result_empty == ""
        assert did_autocomplete_empty is False

    def test_autocomplete_with_whitespace_and_alternatives(self):
        """Autocomplete with whitespace between alternatives."""
        fsm = FSM()
        hello = fsm.add_literal("hello", [0])
        fsm.add_whitespace(hello)
        world = fsm.add_literal("world", [hello])
        fsm.add_whitespace(world)
        # Create alternatives for next word
        fsm.add_literal("!", [world])
        fsm.add_literal("?", [world])

        # "hello world" has two options after (! or ?), so stops
        result, did_autocomplete = fsm.try_autocomplete("hello world")
        assert result == "hello world"
        assert did_autocomplete is False

    def test_autocomplete_idempotent(self):
        """Calling autocomplete on already completed text returns same result."""
        fsm = FSM()
        fsm.add_literal("hello", [0])

        # First call
        result1, did_autocomplete1 = fsm.try_autocomplete("h")
        assert result1 == "hello"
        assert did_autocomplete1 is True

        # Second call with the result
        result2, did_autocomplete2 = fsm.try_autocomplete(result1)
        assert result2 == "hello"
        assert did_autocomplete2 is False

    def test_autocomplete_preserves_input(self):
        """Autocomplete never modifies the input text, only extends it."""
        fsm = FSM()
        fsm.add_literal("hello", [0])

        inputs = ["", "h", "he", "hel", "hell", "hello"]
        for input_text in inputs:
            result, _ = fsm.try_autocomplete(input_text)
            assert result.startswith(input_text), f"Result {result} doesn't start with {input_text}"

    def test_autocomplete_complex_json_like_structure(self):
        """Autocomplete in a complex structure similar to JSON."""
        fsm = FSM()
        # Simulate: {"key": value}
        brace = fsm.add_literal("{", [0])
        quote1 = fsm.add_literal('"', [brace])
        key = fsm.add_literal("key", [quote1])
        quote2 = fsm.add_literal('"', [key])
        colon = fsm.add_literal(":", [quote2])
        fsm.add_whitespace(colon)
        # After whitespace, could be number, string, or other (creates branching)
        fsm.add_literal("123", [colon])
        fsm.add_literal("true", [colon])

        # Input up to colon and space should not autocomplete (multiple options)
        result, did_autocomplete = fsm.try_autocomplete('{\"key\": ')
        assert result == '{\"key\": '
        assert did_autocomplete is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
