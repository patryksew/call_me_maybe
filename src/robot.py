from src.models import FunctionDefinitions, InputPrompt


class Robot:
    def __init__(self, function_definitions: FunctionDefinitions):
        import llm_sdk
        self.model = llm_sdk.Small_LLM_Model()
        self.function_definitions = function_definitions

    def make_prompt(self, input_prompt: InputPrompt) -> str:
        system_prompt = ("You are a helpful assistant that will perform function calling.\n"
                         "Your job is to first understand what functions you can use, and then to select a correct one\n"
                         "based on prompt."
                         "Do not think.\n"
                         "Result needs to be a valid JSON, containing fields: prompt: str, name: str, and parameters: dict.\n"
                         "Remember to put in parameters correctly. Pay utmost attention to regex.\n"
                         "It is really important that you do not think and output only the JSON.\n"
                         "Allowed functions are:\n" + self.function_definitions.model_dump_json())

        return (f"<|im_start|>system\n{system_prompt}\n<|im_end|>\n"
                f"<|im_start|>user\n{input_prompt}\n<|im_end|>\n"
                f"<|im_start|>assistant\n"
                f"<think>\n\n</think>\n"
                )

    def ask(self, prompt: str) -> list[int]:
        im_end = self.model.encode("<|im_end|>")[0].tolist()[0]
        tokens = self.model.encode(prompt)[0].tolist()

        while True:
            logits = self.model.get_logits_from_input_ids(tokens)
            max_logit = logits.index(max(logits))
            tokens.append(max_logit)
            if max_logit == im_end:
                break

        return tokens

    def extract_answer(self, tokens: list[int]) -> list[int]:
        """This function returns the part of the answer that sits between end of thinking and <|im_end|>"""
        think_end = self.model.encode("</think>")[0].tolist()[0]
        im_end = self.model.encode("<|im_end|>")[0].tolist()[0]

        think_end_index = tokens.index(think_end)
        im_end_index = tokens.index(im_end, think_end_index)

        return tokens[think_end_index + 1: im_end_index]

    def get_answer_to_input_prompt(self, input_prompt: InputPrompt):
        prompt = self.make_prompt(input_prompt)
        tokens = self.ask(prompt)
        tokens = self.extract_answer(tokens)
        return self.model.decode(tokens)
