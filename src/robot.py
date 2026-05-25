from math import inf

from .fsm import FSM
from .printer import Printer
from .models import FunctionDefinitions, InputPrompt


class Robot:
    answer_start_marker = "<|im_start|>assistant"

    def __init__(self, function_definitions: FunctionDefinitions, validator: FSM, printer: Printer):
        import llm_sdk
        self.model = llm_sdk.Small_LLM_Model("Qwen/Qwen3-0.6B")
        # self.model = llm_sdk.Small_LLM_Model("openai-community/gpt2")
        # self.model = llm_sdk.Small_LLM_Model("LiquidAI/LFM2.5-1.2B-Instruct")
        # self.model = llm_sdk.Small_LLM_Model("TinyLlama/TinyLlama-1.1B-Chat-v0.4")
        self.function_definitions = function_definitions
        self.validator = validator
        self.printer = printer

    def get_answer_start_index(self, tokens: list[int]):
        answer_start_marker_tokens = self.model.encode(self.answer_start_marker)[0].tolist()
        for i in range(len(tokens) - len(answer_start_marker_tokens) + 1):
            if tokens[i:i + len(answer_start_marker_tokens)] == answer_start_marker_tokens:
                return i + len(answer_start_marker_tokens)
        raise ValueError("Answer start marker not found in tokens")

    def make_prompt(self, input_prompt: InputPrompt) -> str:
        system_prompt = ("You are a helpful assistant that will perform function calling.\n"
                         "Your job is to first understand what functions you can use, and then to select a correct one\n"
                         "based on prompt."
                         "Result needs to be a valid JSON, containing fields: prompt: str, name: str, and parameters: dict.\n"
                         "Remember to put in parameters correctly. Pay utmost attention to regex.\n"
                         "It is really important that you do not think and output only the JSON.\n"
                         "Allowed functions are:\n" + self.function_definitions.model_dump_json())

        return (f"<|im_start|>system\n{system_prompt}\n<|im_end|>\n"
                f"<|im_start|>user\n{input_prompt}\n<|im_end|>\n"
                f"{self.answer_start_marker}"
                '{\n'
                f'    "prompt": {input_prompt},\n'
                '    "name": "'
                )

    def ask(self, prompt: str) -> list[int]:
        tokens = self.model.encode(prompt)[0].tolist()
        answer_start = self.get_answer_start_index(tokens)

        while True:
            text, did_autocomplete = self.validator.try_autocomplete(self.model.decode(tokens[answer_start:]))
            if did_autocomplete:
                tokens[answer_start:] = self.model.encode(text)[0].tolist()
                tokens.pop()
            logits = self.model.get_logits_from_input_ids(tokens)
            while True:
                max_logit = logits.index(max(logits))
                tokens.append(max_logit)
                validation_result = self.validator.validate_text(self.model.decode(tokens[answer_start:]))
                self.printer.print(self.model.decode(tokens[answer_start:]))
                if validation_result == self.validator.ValidationResult.OK:
                    break
                if validation_result == self.validator.ValidationResult.FINISHED:
                    self.printer.set_prompt_finished()
                    return tokens
                logits[max_logit] = -inf
                tokens.pop()

    def extract_answer(self, tokens: list[int]) -> list[int]:
        answer_start = self.get_answer_start_index(tokens)
        return tokens[answer_start:]

    def get_answer_to_input_prompt(self, input_prompt: InputPrompt):
        prompt = self.make_prompt(input_prompt)
        tokens = self.ask(prompt)
        tokens = self.extract_answer(tokens)
        return self.model.decode(tokens)
