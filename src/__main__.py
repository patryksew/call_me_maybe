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
        return

    io_manager = IOManager(
        path_functions=args.functions_definition,
        path_input=args.input,
        path_output=args.output
    )

    try:
        definitions = io_manager.get_function_definitions()
    except ValidationError as e:
        print(f"Error parsing function definitions: {e.errors()[0]['msg']}")
        return
    except ValueError as e:
        print(f"Error loading function definitions: {e}")
        return

    try:
        prompts = io_manager.get_input_prompts().prompts
    except ValidationError as e:
        print(f"Error parsing input prompts: {e.errors()[0]['msg']}")
        return
    except ValueError as e:
        print(f"Error loading input prompts: {e}")
        return

    try:
        validator = definitions.to_fsm()
    except ValueError as e:
        print(f"Error creating FSM: {e}")
        return

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
            return

    outputs = OutputResults()

    start_t = time.time()

    for prompt in prompts:
        try:
            answer = robot.get_answer_to_input_prompt(prompt)
        except Exception as e:
            print(f"Error processing prompt: {e}")
            return
        try:
            output = OutputResult.model_validate_json(answer)
            outputs.append(output)
        except ValidationError as e:
            print(f"Error parsing output: {e.errors()[0]['msg']}")
            return

    try:
        io_manager.save_output_results(outputs)
    except Exception as e:
        print(f"Error saving output: {e}")
        return
    printer.print_done_message(time.time() - start_t, str(io_manager.get_output_file_path()))


if __name__ == "__main__":
    try:
        main()
    finally:
        Printer.restore_terminal_settings()
