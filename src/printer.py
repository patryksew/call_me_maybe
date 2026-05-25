class Printer:
    def __init__(self, total_prompts: int):
        self._total_prompts = total_prompts
        self._processed = 0

        # \033[?25l -> Hide cursor and \033[2J -> Clear the screen
        print("\033[?25l\033[2J", end="")

    def print(self, text: str):
        # ...
        # \033[H -> Move cursor to Home position (0,0)
        print("\033[H\033[2J", end="")

        print(text)
        print(f"\n\n{self._processed} / {self._total_prompts}")

    def set_prompt_finished(self):
        self._processed += 1

    @staticmethod
    def restore_terminal_settings():
        # \033[?25h -> Show cursor
        print("\033[?25h", end="")
