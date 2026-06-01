import time
from pydantic import ValidationError

from .cli import CLIArguments
from .io_manager import IOManager
from .models import OutputResults, OutputResult
from .robot import Robot
from .printer import Printer


def main() -> None:
    """
    Main entry point.
    """
    import os
    # we're tricking ROCM that we use a supported GPU
    os.environ["HSA_OVERRIDE_GFX_VERSION"] = "10.3.0"

    try:
        args = CLIArguments.from_cli()
    except ValidationError as e:
        print(f"Error parsing arguments: {e.errors()[0]['msg']}")
        exit(1)

    io_manager = IOManager(
        path_functions=args.functions_definition,
        path_input=args.input,
        path_output=args.output
    )
    definitions = io_manager.get_function_definitions()

    prompts = io_manager.get_input_prompts().prompts
    validator = definitions.to_fsm()

    model = args.model

    printer = Printer(len(prompts), model)

    try:
        robot = Robot(definitions, validator, printer, model)
    except Exception as e:
        BOLD = "\033[1m"
        LIGHT_GREEN = "\033[92m"
        RESET = "\033[0m"
        model = 'Qwen/Qwen3-0.6B'
        print(
            f"Error initializing the Robot: {e}.\n\n"
            f"{BOLD}{LIGHT_GREEN}Falling back to the default model {model}.{RESET}\n")
        try:
            printer = Printer(len(prompts), model)
            robot = Robot(definitions, validator, printer, model)
        except Exception as e:
            print(f"Failed to load the default model as well: {e}. Exiting.")
            exit(1)

    outputs = OutputResults()

    start_t = time.time()

    for prompt in prompts:
        answer = robot.get_answer_to_input_prompt(prompt)
        try:
            output = OutputResult.model_validate_json(answer)
            outputs.append(output)
        except ValueError as e:
            print(e)
            print(answer)

    io_manager.save_output_results(outputs)
    printer.print_done_message(time.time() - start_t, str(io_manager.get_output_file_path()))

    exit(0)


if __name__ == "__main__":
    try:
        main()
    finally:
        Printer.restore_terminal_settings()
