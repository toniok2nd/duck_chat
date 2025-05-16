import argparse
import asyncio
import readline
import sys
import os
import tomllib
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.emoji import Emoji
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from .api import DuckChat
from .exceptions import DuckChatException
from .models import ModelType


HELP_MSG = (
    "- [red]/help         [/red]Display the help message\n"
    "- [red]/singleline   [/red]Enable singleline mode, validate is done by <enter>\n"
    "- [red]/multiline    [/red]Enable multiline mode, validate is done by EOF <Ctrl+D>\n"
    "- [red]/quit         [/red]Quit\n"
    "- [red]/save_history [/red]Save conversation history\n"
    "- [red]/load_history [/red]Load conversation history\n"
)

COMMANDS = {
    "help",
    "singleline",
    "multiline",
    "quit",
    "save_history",
    "load_history"
}
#def setCompletion(_list: list[str]):


def completer(text: str, state: int) -> str | None:
    origline = readline.get_line_buffer()
    words = origline.split()
    if not origline.startswith("/"):
        return None
    if len(words) < 2 and words[0][1:] not in COMMANDS:
        options = [cmd for cmd in COMMANDS if cmd.startswith(text)]
        if state < len(options):
            return options[state]
    return None


class CLI:
    def __init__(self) -> None:
        readline.parse_and_bind("tab: complete")
        readline.set_completer(completer)
        self.INPUT_MODE = "singleline"
        self.COUNT = 1
        self.console = Console()

    async def run(self) -> None:
        """Base loop program"""
        model = self.read_model_from_conf()
        self.console.print(f"Using [u b red blink]{model.value}[/u b red blink]")
        async with DuckChat(model) as chat:
            self.console.print("Type /help to display the help",style='blue')
            await chat.get_vqd()

            while True:
                peanuts_emoji = Emoji('peanuts')
                self.console.print(Panel(f">>> {peanuts_emoji} input {self.COUNT}:", style="white on blue"))

                user_input = self.get_user_input()

                # user input is command
                if user_input.startswith("/"):
                    await self.command_parsing(user_input.split(), chat)
                    continue

                # empty user input
                if not user_input:
                    dead = Emoji('prohibited')
                    self.console.print(f"{dead} Empty input",style="red")
                    continue

                # process request
                brain_emoji = Emoji('brain')
                self.console.print(Panel(f"<<< {brain_emoji} Response {self.COUNT}:", style="white on green"))
                try:
                    self.answer_print(await chat.ask_question(user_input))
                except DuckChatException as e:
                    print(f"Error occurred: {str(e)}")
                else:
                    self.COUNT += 1

    def get_user_input(self) -> str:
        if self.INPUT_MODE == "singleline":
            try:
                user_input = input()
            except EOFError:
                return ""
        else:
            contents = []
            while True:
                try:
                    line = input()
                except EOFError:
                    break
                contents.append(line)
            user_input = "".join(contents)
        return user_input.strip()

    def switch_input_mode(self, mode: str) -> None:
        if mode == "singleline":
            self.INPUT_MODE = "singleline"
            print("Switched to singleline mode, validate is done by <enter>")
        else:
            self.INPUT_MODE = "multiline"
            print("Switched to multiline mode, validate is done by EOF <Ctrl+D>")

    def hello(self):
        print('hello', style='red')


    async def command_parsing(self, args: list[str], chat: DuckChat) -> None:
        """Recognize command"""
        self.console.print(Panel(f">>> Command mode Response {self.COUNT}:",style='white on red'))
        match args[0][1:]:
            case "singleline":
                self.switch_input_mode("singleline")
            case "multiline":
                self.switch_input_mode("multiline")
            case "save_history":
                await chat.save_history()
            case "load_history":
                await chat.load_history(self.select_history_file())
            case "quit":
                print("Quit")
                sys.exit(0)
            case "help":
                self.console.print(HELP_MSG)
            case _:
                self.console.print("Command not found",style="red")
                print("Type \033[1;4m/help\033[0m to display the help")

    def answer_print(self, query: str) -> None:
        if "`" in query:  # block of code
            self.console.print(Markdown(query))
        else:
            print(query)

    def read_model_from_conf(self) -> ModelType:
        filepath = Path.home() / ".config" / "hey" / "conf.toml"
        if filepath.exists():
            with open(filepath, "rb") as f:
                conf = tomllib.load(f)
                model_name = conf["model"]
            if model_name in (x.name for x in ModelType):
                if model_name == "GPT3":
                    print("\033[1;1m GPT3 is deprecated! Use GPT4o\033[0m")
                return ModelType[model_name]
        return ModelType.Claude


    def select_history_file(self) -> str:
        home_folder = os.path.expanduser('~')
        folder_path=os.path.join(home_folder, '.config','duck_chat')
        files = os.listdir(folder_path)
        tab_files = {str(i):item for i, item in enumerate(files,start=1)}
        
        table = Table(show_header=True, header_style="bold bmagenta")
        table.add_column("N°")
        table.add_column("filename")
        for k,v in tab_files.items():
            table.add_row(k,v)
        # Print the table
        self.console.print(table)

        self.console.print()
        ret = Prompt.ask(prompt=f"Select a file between 1-{len(files)}",
                         choices=[str(i) for i in range(1,len(files)+1)])
        return tab_files[ret]



def safe_entry_point() -> None:
    parser = argparse.ArgumentParser(description="A simple CLI tool.")
    parser.add_argument("--generate", action="store_true", help="Generate new models")
    args = parser.parse_args()
    if args.generate:
        from .models.generate_models import main as generator

        generator()
    else:
        asyncio.run(CLI().run())
