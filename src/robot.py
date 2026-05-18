from math import inf

from .fsm import FSM
from .models import FunctionDefinitions, InputPrompt


class Robot:
    def __init__(self, function_definitions: FunctionDefinitions, validator: FSM):
        import llm_sdk
        self.model = llm_sdk.Small_LLM_Model()
        self.function_definitions = function_definitions
        self.validator = validator

    def make_prompt(self, input_prompt: InputPrompt) -> str:
        system_prompt = ("You are a helpful assistant that will perform function calling.\n"
                         "Your job is to first understand what functions you can use, and then to select a correct one\n"
                         "based on prompt."
                         "Result needs to be a valid JSON, containing fields: name: str, and parameters: dict.\n"
                         "Remember to put in parameters correctly. Pay utmost attention to regex.\n"
                         "It is really important that you do not think and output only the JSON.\n"
                         "Allowed functions are:\n" + self.function_definitions.model_dump_json())

        return (f"<|im_start|>system\n{system_prompt}\n<|im_end|>\n"
                f"<|im_start|>user\n{input_prompt}\n<|im_end|>\n"
                f"<|im_start|>assistant\n"
                f"<think>\n\n</think>\n"
                )

    def ask(self, prompt: str) -> list[int]:
        tokens = self.model.encode(prompt)[0].tolist()
        end_think_index = tokens.index(self.model.encode("</think>")[0].tolist()[0])

        while True:
            logits = self.model.get_logits_from_input_ids(tokens)
            while True:
                max_logit = logits.index(max(logits))
                tokens.append(max_logit)
                validation_result = self.validator.validate_text(self.model.decode(tokens[end_think_index+2:]))
                if validation_result == self.validator.ValidationResult.OK:
                    break
                if validation_result == self.validator.ValidationResult.FINISHED:
                    return tokens
                logits[max_logit] = -inf
                tokens.pop()

    def extract_answer(self, tokens: list[int]) -> list[int]:
        """This function returns the part of the answer that sits between end of thinking and <|im_end|>"""
        think_end = self.model.encode("</think>")[0].tolist()[0]

        think_end_index = tokens.index(think_end)

        return tokens[think_end_index + 2:]

    def get_answer_to_input_prompt(self, input_prompt: InputPrompt):
        prompt = self.make_prompt(input_prompt)
        tokens = self.ask(prompt)
        tokens = self.extract_answer(tokens)
        return self.model.decode(tokens)
