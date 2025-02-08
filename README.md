# LLM Code Review

## Overview

`llm-code-review` is a command-line tool for automated code reviews of GitHub pull requests using OpenAI's GPT models or local models via Ollama. It fetches modified files, extracts diffs, retrieves full file contents for context, and generates concise, constructive code reviews.

## Features
- Supports OpenAI API (`gpt-4o-mini`, etc.)
- Supports local models via Ollama
- Fetches diffs from GitHub pull requests
- Retrieves full file contents for context
- Provides AI-generated feedback with before/after code snippets
- Filters reviews to focus only on Python files

## Installation

Install the package from PyPI:
```sh
pip install llm-code-review
```

## Prerequisites
Before using the tool, you must set up the required API keys as environment variables:

- **GitHub Token**: To authenticate API requests, create a GitHub personal access token (with `repo` scope for private repositories) and set it as an environment variable.
- **OpenAI API Key**: Obtain an API key from OpenAI and set it as an environment variable.

### Setting Up Environment Variables
Add the following lines to your shell profile (e.g., `~/.bashrc`, `~/.zshrc`):

```sh
export GITHUB_TOKEN="your_github_token"
export OPENAI_API_KEY="your_openai_api_key"
```

Then, reload your shell profile:

```sh
source ~/.bashrc  # or source ~/.zshrc
```

Alternatively, you can store them in a `.env` file and use `python-dotenv` to load them.

## Usage

### Basic Command

To review a GitHub pull request:
```sh
llm-code-review owner/repository PR_NUMBER
```

Example:
```sh
llm-code-review octocat/hello-world 42
```

### Using a Specific Model

#### OpenAI
```sh
llm-code-review octocat/hello-world 42 --model openai:gpt-4o-mini
```

#### Ollama (local model)
```sh
llm-code-review octocat/Hello-World 42 --model ollama:deepseek-r1:8b
```
This command fetches the pull request #42 from the `octocat/Hello-World` repository, retrieves modified Python files, and reviews the changes using OpenAI.

## How It Works
1. Fetches pull request details from GitHub.
2. Retrieves the full content of modified Python files.
3. Sends the diff and full file content to OpenAI for review.
4. Displays feedback, focusing on potential improvements and critical issues.

## Notes
- Only Python (`.py`) files are reviewed.
- The review focuses on changes in the PR while using the full file context.
- If a file has more than three issues, only the most important one is highlighted unless critical issues are found.

## License
MIT License

## Contributions
Feel free to open issues or submit pull requests!

