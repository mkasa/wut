# Standard library
import os
import argparse
import logging
from openai import APIConnectionError, APIError, RateLimitError, AuthenticationError, NotFoundError

# Third party
from rich.console import Console
from rich.markup import escape

# Local
from wut.utils import (
    get_shell,
    get_terminal_context,
    explain,
    get_llm_provider,
    remove_ansi_escape_sequences,
)


def error_message(e: APIError) -> str:
    body = e.body
    if isinstance(body, dict):
        body = body.get("error", body)
        if isinstance(body, dict) and body.get("message"):
            return str(body["message"])
    return e.message


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
    parser.add_argument(
        "-p",
        "--perplexity",
        action="store_true",
        help="Use Perplexity CLI instead of the configured LLM provider.",
    )
    args = parser.parse_args()
    if args.activate_shell:
        print_activate_script(args.activate_shell)
        return
    console = Console()
    debug = lambda text: console.print(f"wut | {text}") if args.debug else None
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
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
            not args.perplexity
            and not os.environ.get("OPENAI_API_KEY", None)
            and not os.environ.get("AZURE_API_KEY", None)
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
            response = explain(terminal_context, args.query, use_perplexity=args.perplexity)
        except RateLimitError as e:
            console.print("[bold red]ERROR: Rate limit exceeded.[/bold red]")
            console.print("    [green]" + escape(error_message(e)) + "[/green]")
            return
        except AuthenticationError as e:
            key_var = "AZURE_API_KEY" if get_llm_provider() == "azure" else "OPENAI_API_KEY"
            console.print("[bold red]ERROR: Authentication error.[/bold red]")
            console.print("    [green]" + escape(error_message(e)) + "[/green]")
            console.print(f"    Your API key appears to be invalid. Please check {key_var}.")
            return
        except NotFoundError as e:
            console.print("[bold red]ERROR: Not found error.[/bold red]")
            console.print("    [green]" + escape(error_message(e)) + "[/green]")
            console.print("    If you are using Azure OpenAI, please ensure that you have set the correct endpoint.")
            return
        except APIConnectionError as e:
            console.print("[bold red]ERROR: Could not connect to the API.[/bold red]")
            console.print("    [green]" + escape(str(e)) + "[/green]")
            console.print("    Please check your network and endpoint settings (OPENAI_BASE_URL / AZURE_ENDPOINT).")
            return
        except APIError as e:
            console.print("[bold red]ERROR: API error.[/bold red]")
            console.print("    [green]" + escape(error_message(e)) + "[/green]")
            return
        except (RuntimeError, ValueError) as e:
            console.print(f"[bold red]ERROR: {escape(str(e))}[/bold red]")
            return

    if isinstance(response, str):
        # Response from glow with ANSI codes - print directly
        print(response, end='')
    else:
        # Rich Markdown object - use console.print
        console.print(response)


