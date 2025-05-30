# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`wut` is a CLI tool that explains terminal command output using LLMs. It captures terminal history from tmux/screen sessions and sends it to OpenAI, Anthropic Claude, Azure OpenAI, or Ollama for explanation.

## Development Commands

- **Install dependencies**: `uv sync`
- **Run the CLI**: `python -m wut` or `uv run wut`
- **Build package**: `uv build`
- **Install in development mode**: `uv pip install -e .`

## Architecture

### Core Components

- **`wut/wut.py`**: Main entry point with CLI argument parsing and orchestration
- **`wut/utils.py`**: Core functionality including:
  - Terminal context extraction (`get_terminal_context()`)
  - Shell detection and prompt parsing
  - LLM provider routing (OpenAI, Anthropic, Azure, Ollama)
  - Terminal output processing and command parsing
- **`wut/prompts.py`**: System prompts for different LLM interactions

### Key Architecture Patterns

- **Shell Detection**: Multi-method approach using environment variables (`$SHELL`) and process tree traversal
- **Terminal Context**: Parses tmux/screen output into structured commands with prompts and outputs
- **LLM Provider Abstraction**: Single `explain()` function routes to different providers based on environment variables
- **Command Parsing**: Uses shell prompts to separate commands from outputs in terminal history

### Environment Variables

Required (at least one):
- `OPENAI_API_KEY` - For OpenAI/ChatGPT
- `ANTHROPIC_API_KEY` - For Claude
- `AZURE_API_KEY` + `AZURE_ENDPOINT` - For Azure OpenAI
- `OLLAMA_MODEL` - For local Ollama models

Optional configuration:
- `OPENAI_MODEL` (default: "gpt-4o")
- `OPENAI_BASE_URL` - Custom OpenAI endpoint
- `AZURE_MODEL` (default: "gpt-4o")
- `AZURE_API_VERSION` (default: "2024-06-01")

### Terminal Integration

Requires tmux (`$TMUX`) or screen (`$STY`) session. The tool:
1. Captures pane output using `tmux capture-pane` or `screen hardcopy`
2. Parses output using detected shell prompts
3. Truncates to last few commands (max 10000 chars)
4. Sends structured context to LLM

### Dependencies

- **Core**: `anthropic`, `openai`, `ollama`, `psutil`, `rich`, `tiktoken`
- **Python**: Requires >=3.13
- **Package Manager**: Uses `uv` for dependency management