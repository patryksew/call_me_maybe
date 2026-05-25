import string
from enum import Enum, auto


class DivergingLiteralError(ValueError):
    """Raised when a literal is added that does not lead to exactly one final state."""


class FSM:
    """Finite State Machine for constrained decoding."""

    class ValidationResult(Enum):
        OK = auto()
        NOK = auto()
        FINISHED = auto()

    def __init__(self):
        self.states: list[dict[str, int]] = [{}]

    def __new_state(self) -> int:
        """Creates an empty state

        Returns the index of the new state."""
        self.states.append({})
        return len(self.states) - 1

    def add_literal(self, text: str, start: list[int] | int) -> int:
        """Adds a literal string to the FSM, starting from the given states.
        The literal must lead to exactly one final state."""
        if len(text) == 0:
            raise ValueError("Text must be non-empty")

        if isinstance(start, int):
            start = [start]

        current_states = set(start)
        for char in text:
            next_states: set[int] = set()
            shared_new_state_index: int | None = None

            for state_index in current_states:
                state = self.states[state_index]
                next_state_index = state.get(char)

                if next_state_index is None:
                    if shared_new_state_index is None:
                        shared_new_state_index = self.__new_state()
                    next_state_index = shared_new_state_index
                    state[char] = next_state_index

                next_states.add(next_state_index)

            current_states = next_states

        if len(current_states) != 1:
            raise DivergingLiteralError("Literal must lead to exactly one final state")

        return current_states.pop()

    def add_whitespace(self, start: list[int] | int) -> None:
        """Adds zero or more whitespaces (space, tab, newline). Use add_literal if you need at least one whitespace."""

        if isinstance(start, int):
            start = [start]

        for state_index in start:
            state = self.states[state_index]
            state[' '] = state_index
            state['\t'] = state_index
            state['\n'] = state_index

    def add_number(self, start: int) -> list[int]:
        """Adds JSON valid number

        Returns the list of indexes containing the last valid characters."""

        DIGITS = "0123456789"
        NON_ZERO_DIGITS = "123456789"

        def new_state() -> int:
            return self.__new_state()

        def link(src: int, chars: str, dst: int) -> None:
            for char in chars:
                self.states[src][char] = dst

        minus = new_state()
        zero = new_state()
        int_digits = new_state()
        dot = new_state()
        fraction = new_state()
        exp = new_state()
        exp_sign = new_state()
        exp_digits = new_state()

        link(start, "-", minus)

        link(start, "0", zero)
        link(minus, "0", zero)
        link(start, NON_ZERO_DIGITS, int_digits)
        link(minus, NON_ZERO_DIGITS, int_digits)
        link(int_digits, DIGITS, int_digits)

        link(zero, ".", dot)
        link(int_digits, ".", dot)
        link(dot, DIGITS, fraction)
        link(fraction, DIGITS, fraction)

        for state in (zero, int_digits, fraction):
            link(state, "eE", exp)

        link(exp, "+-", exp_sign)

        link(exp, DIGITS, exp_digits)
        link(exp_sign, DIGITS, exp_digits)
        link(exp_digits, DIGITS, exp_digits)

        return [zero, int_digits, fraction, exp_digits]

    def add_boolean(self, start: int) -> list[int]:
        """Adds the literals "true" and false" to the FSM, starting from the given state."""
        true_state = self.add_literal("true", start)
        false_state = self.add_literal("false", start)
        return [true_state, false_state]

    def add_string(self, start: int) -> int:
        valid_chars = "".join(
            char for char in string.printable
            if char not in {'"', '\\', '\t', '\n', '\r', '\x0b', '\x0c'}
        )
        backslash = '\\'
        quotation_mark = '"'
        valid_escaped_chars = '"\\/bfnrt'

        def link(src: int, chars: str, dst: int) -> None:
            for char in chars:
                self.states[src][char] = dst

        str_begin_state = self.__new_state()
        normal_char_state = self.__new_state()
        backslash_state = self.__new_state()
        escaped_char_state = self.__new_state()
        str_end_state = self.__new_state()

        link(start, quotation_mark, str_begin_state)
        link(str_begin_state, valid_chars, normal_char_state)
        link(str_begin_state, quotation_mark, str_end_state)
        link(normal_char_state, valid_chars, normal_char_state)
        link(normal_char_state, quotation_mark, str_end_state)
        link(normal_char_state, backslash, backslash_state)
        link(str_begin_state, backslash, backslash_state)
        link(backslash_state, valid_escaped_chars, escaped_char_state)
        link(escaped_char_state, valid_chars, normal_char_state)
        link(escaped_char_state, quotation_mark, str_end_state)

        return str_end_state

    def validate_text(self, text: str) -> ValidationResult:
        state = self.states[0]

        for char in text:
            next_state = state.get(char)
            if next_state is None:
                return FSM.ValidationResult.NOK
            state = self.states[next_state]

        if len(state) == 0:
            return FSM.ValidationResult.FINISHED
        return FSM.ValidationResult.OK

    def try_autocomplete(self, text: str) -> tuple[str, bool]:
        """Tries to autocomplete the given text to a valid string according to the FSM, as long when there is a single valid path.
        Returns the autocompleted text and a boolean indicating whether any autocompletion was done."""
        state = self.states[0]
        result = text
        did_something = False

        for char in text:
            next_state = state.get(char)
            if next_state is None:
                return result, did_something
            state = self.states[next_state]

        while len(state) == 1:
            did_something = True
            char, next_state_index = next(iter(state.items()))
            result += char
            state = self.states[next_state_index]

        return result, did_something
