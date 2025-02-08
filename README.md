# LLM Code Review

## Overview
`llm-code-review` is a Python CLI tool that fetches and reviews GitHub pull requests using OpenAI's language model. It downloads modified files from a specified PR, retrieves their full content, and leverages OpenAI to provide focused, constructive code reviews.

## Installation
You can install `llm-code-review` from PyPI using pip:

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
Once installed and set up, you can run the tool using the following command:

```sh
llm-code-review <repo_owner/repo_name> <pr_number>
```

### Example:
```sh
llm-code-review octocat/Hello-World 42
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
Feel free to contribute by submitting issues or pull requests!

## Author
[Your Name]

