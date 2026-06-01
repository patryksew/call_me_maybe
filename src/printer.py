class Printer:
    """Handles terminal output and progress reporting."""
    def __init__(self, total_prompts: int, model_name: str) -> None:
        """
        Initialize the Printer with the total number of prompts and the model name.

        :param total_prompts: Total number of prompts to process.
        :param model_name: Name of the LLM being used.
        """
        self._total_prompts = total_prompts
        self._model_name = model_name
        self._processed = 0

        # \033[?25l -> Hide cursor
        print("\033[?25l", end="")
        self._clear_screen()

    def print(self, content: str) -> None:
        """
        Print the current content along with a progress bar.

        :param content: The content to display.
        """
        self._clear_screen()

        progress_bar = self._generate_progress_bar()
        print(f"Processing using {self._model_name}\n"
              f"Progress: {self._processed + 1} / {self._total_prompts}\n"
              f"{progress_bar}\n")
        print(content)

    def print_done_message(self, time: float, output_file: str) -> None:
        """
        Print a completion message with processing time and output location.

        :param time: Time taken to process all prompts.
        :param output_file: Path to the saved results.
        """
        self._clear_screen()
        print(f"Done!\n"
              f"Processed {self._total_prompts} prompts in {time:.2f} s.\n"
              f"Saved results to {output_file}")

    def _generate_progress_bar(self, bar_length: int = 40) -> str:
        """Generate a progress bar string."""
        percent = self._processed / self._total_prompts
        filled = int(bar_length * percent)
        bar = "█" * filled + "░" * (bar_length - filled)
        percentage = int(percent * 100)
        return f"[{bar}] {percentage}%"

    def set_prompt_finished(self) -> None:
        """Increment the count of processed prompts."""
        self._processed += 1

    @staticmethod
    def _clear_screen() -> None:
        """Clear the terminal screen."""
        # \033[H -> Move cursor to Home position (0,0)
        # \033[2J -> Clear the screen
        print("\033[H\033[2J", end="")

    @staticmethod
    def restore_terminal_settings() -> None:
        """Restore terminal settings, such as showing the cursor."""
        # \033[?25h -> Show cursor
        print("\033[?25h", end="")
