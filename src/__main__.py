import time

from .io_manager import IOManager
from .models import OutputResults, OutputResult
from .robot import Robot


def main():
    import os
    # we're tricking ROCM that we use a supported GPU
    os.environ["HSA_OVERRIDE_GFX_VERSION"] = "10.3.0"

    i = IOManager()
    definitions = i.get_function_definitions()

    prompts = i.get_input_prompts().prompts
    validator = definitions.to_fsm()
    robot = Robot(definitions, validator)

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

    print(outputs.model_dump_json(indent=4))

    print(f"Total time: {time.time() - start_t:.2f} seconds")

    exit(0)


main()