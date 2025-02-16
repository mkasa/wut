# Standard library
import os
import argparse
from openai import RateLimitError, AuthenticationError

# Third party
from rich.console import Console

# Local
from wut.utils import (
    get_shell,
    get_terminal_context,
    explain,
    remove_ansi_escape_sequences,
)


def print_activate_script(shell):
    if shell == "bash":
        print("alias wut='\\wut --prompt=\"$(echo ${PS1@P})\" $@'")  # NOTE: This works only in bash 4.4+
    elif shell == "zsh":
        print("alias wut='\\wut --prompt=\"$(print -P $PS1)\" $@'")
    elif shell == "fish":
        print("ERROR: Sorry. fish is not supported yet.", file=sys.stderr)
    else:
        print(
            "wut only supports bash, zsh, and fish. Please specify one of these shells."
        )


def main():
    parser = argparse.ArgumentParser(
        description="Understand the output of your latest terminal command."
    )
    parser.add_argument(
        "--query",
        type=str,
        required=False,
        default="",
        help="A specific question about what's on your terminal.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print debug information.",
    )
    parser.add_argument(
        "--activate-shell",
        type=str,
        required=False,
        help="Print a shell script to eval in your shell to activate wut.",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        required=False,
        help="The shell prompt string. If not provided, wut will attempt to detect it.",
    )
    args = parser.parse_args()
    if args.activate_shell:
        print_activate_script(args.activate_shell)
        return
    console = Console()
    debug = lambda text: console.print(f"wut | {text}") if args.debug else None
    if args.prompt:
        args.prompt = remove_ansi_escape_sequences(args.prompt)

    with console.status("[bold green]Trying my best..."):
        # Ensure environment is set up correctly
        if not os.environ.get("TMUX") and not os.environ.get("STY"):
            console.print(
                "[bold red]wut must be run inside a tmux or screen session.[/bold red]"
            )
            return
        if (
            not os.environ.get("OPENAI_API_KEY", None)
            and not os.environ.get("ANTHROPIC_API_KEY", None)
            and not os.environ.get("OLLAMA_MODEL", None)
        ):
            console.print(
                "[bold red]Please set your OpenAI or Anthropic API key in your environment variables. Or, alternatively, specify an Ollama model name.[/bold red]"
            )
            return

        # Gather context
        shell = get_shell(args.prompt)
        terminal_context = get_terminal_context(shell)

        debug(f"Retrieved shell information:\n{shell}")
        debug(f"Retrieved terminal context:\n{terminal_context}")
        debug("Sending request to LLM...")

        try:
            # Get response
            response = explain(terminal_context, args.query)
        except RateLimitError as e:
            console.print("[bold red]ERROR: Rate limit exceeded.[/bold red]")
            console.print("    [green]" + e.body["message"] + "[/green]")
            return
        except AuthenticationError as e:
            console.print("[bold red]ERROR: Authentication error.[/bold red]")
            console.print("    [green]" + e.body["message"] + "[/green]")
            return

    console.print(response)


