from math import inf

from .fsm import FSM
from .printer import Printer
from .models import FunctionDefinitions, InputPrompt


class Robot:
    answer_start_marker = "<|im_start|>assistant"

    def __init__(self, function_definitions: FunctionDefinitions, validator: FSM, printer: Printer,
                 model: str):
        """
        Initialize the Robot with function definitions, a validator, a printer, and a model.

        :param function_definitions: Definitions of available functions.
        :param validator: FSM for constrained decoding.
        :param printer: Printer for progress and output.
        :param model: Name of the model to use.
        """
        import llm_sdk
        try:
            self.model = llm_sdk.Small_LLM_Model(model)
        except Exception as e:
            raise ValueError(f"Failed to load model '{model}': {e}")
        self.function_definitions = function_definitions
        self.validator = validator
        self.printer = printer

    def _get_answer_start_index(self, tokens: list[int]) -> int:
        """
        Find the index in the token list where the assistant's answer begins.

        :param tokens: A list of token IDs.
        :return: The index of the first token after the answer start marker.
        :raises ValueError: If the answer start marker is not found in the tokens.
        """
        answer_start_marker_tokens = self.model.encode(self.answer_start_marker)[0].tolist()
        for i in range(len(tokens) - len(answer_start_marker_tokens) + 1):
            if tokens[i:i + len(answer_start_marker_tokens)] == answer_start_marker_tokens:
                return i + len(answer_start_marker_tokens)
        raise ValueError("Answer start marker not found in tokens")

    def _make_prompt(self, input_prompt: InputPrompt) -> str:
        system_prompt = ("You are a helpful assistant that will perform function calling.\n"
                         "Your job is to first understand what functions you can use, and then to "
                         "select a correct one based on prompt. "
                         "Result needs to be a valid JSON, containing fields: "
                         "prompt: str, name: str, and parameters: dict.\n"
                         "Remember to put in parameters correctly. Pay utmost attention to regex.\n"
                         "Allowed functions are:\n" + self.function_definitions.model_dump_json())

        return (f"<|im_start|>system\n{system_prompt}\n<|im_end|>\n"
                f"<|im_start|>user\n{input_prompt}\n<|im_end|>\n"
                f"{self.answer_start_marker}"
                '{\n'
                f'    "prompt": {input_prompt},\n'
                '    "name": "'
                )

    def _ask(self, prompt: str) -> list[int]:
        tokens: list[int] = self.model.encode(prompt)[0].tolist()
        answer_start = self._get_answer_start_index(tokens)

        while True:
            text, did_autocomplete = self.validator.try_autocomplete(
                self.model.decode(tokens[answer_start:]))
            if did_autocomplete:
                tokens[answer_start:] = self.model.encode(text)[0].tolist()
                tokens.pop()
            logits = self.model.get_logits_from_input_ids(tokens)
            while True:
                max_logit = logits.index(max(logits))
                tokens.append(max_logit)
                validation_result = self.validator.validate_text(
                    self.model.decode(tokens[answer_start:]))
                self.printer.print(self.model.decode(tokens[answer_start:]))
                if validation_result == self.validator.ValidationResult.OK:
                    break
                if validation_result == self.validator.ValidationResult.FINISHED:
                    self.printer.set_prompt_finished()
                    return tokens
                logits[max_logit] = -inf
                tokens.pop()

    def _extract_answer(self, tokens: list[int]) -> list[int]:
        answer_start = self._get_answer_start_index(tokens)
        return tokens[answer_start:]

    def get_answer_to_input_prompt(self, input_prompt: InputPrompt) -> str:
        """
        Get the model's answer to a given input prompt.

        :param input_prompt: The input prompt to process.
        :return: The model's answer as a string.
        """
        prompt = self._make_prompt(input_prompt)
        tokens = self._ask(prompt)
        tokens = self._extract_answer(tokens)
        return str(self.model.decode(tokens))
