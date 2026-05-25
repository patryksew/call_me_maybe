import time

from .io_manager import IOManager
from .models import OutputResults, OutputResult
from .robot import Robot
from .printer import Printer


def main():
    import os
    # we're tricking ROCM that we use a supported GPU
    os.environ["HSA_OVERRIDE_GFX_VERSION"] = "10.3.0"

    i = IOManager()
    definitions = i.get_function_definitions()

    prompts = i.get_input_prompts().prompts
    validator = definitions.to_fsm()

    printer = Printer(len(prompts))
    robot = Robot(definitions, validator, printer)

    outputs = OutputResults()

    start_t = time.time()

    for prompt in prompts:
        answer = robot.get_answer_to_input_prompt(prompt)
        try:
            output = OutputResult.model_validate_json(answer)
            output.add_prompt(prompt.prompt)
            outputs.append(output)
        except ValueError as e:
            print(e)
            print(answer)

    i.save_output_results(outputs)

    print(f"Total time: {time.time() - start_t:.2f} seconds")

    exit(0)


if __name__ == "__main__":
    try:
        main()
    finally:
        Printer.restore_terminal_settings()
