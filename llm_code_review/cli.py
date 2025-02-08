import requests
import openai
import click
import os
import base64
from dotenv import load_dotenv

load_dotenv()

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

# Set your API keys via environment variables for security
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# GitHub API Headers
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def fetch_pr_files(repo_owner, repo_name, pr_number):
    """Fetch the modified files and their diffs in the pull request"""
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}/files"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def fetch_file_content(repo_owner, repo_name, file_path, branch):
    """Fetch the full content of a file from the repository."""
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}?ref={branch}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    file_data = response.json()
    if 'content' in file_data:
        return base64.b64decode(file_data['content']).decode('utf-8')
    return ""

def review_code(diff, filename, full_code, model):
    """Generate a code review using OpenAI or Ollama based on the chosen model."""
    provider, model_name = model.split(":", 1)
    
    prompt = f"""
    You are a code reviewer. Review the following Git diff from {filename} for potential bugs.
    Use the full file content as context, but focus only on the changes.
    Suggest improvements where necessary. Keep it concise, don't highlight positives, just negatives.
    If there are more than 3 suggestions for a file, pick the top suggestion only, unless there is a critical one.
    Show before and after code snippets where possible. Be encouraging.
    
    Full file content:
    ```python
    {full_code}
    ```
    
    Changes:
    ```diff
    {diff}
    ```
    
    Provide constructive feedback with clear recommendations.
    """
    
    if provider == "openai":
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    
    elif provider == "ollama":
        if not OLLAMA_AVAILABLE:
            raise RuntimeError("Ollama module is not installed. Install it using 'pip install ollama'.")
        response = ollama.chat(model=model_name, messages=[{"role": "user", "content": prompt}])
        return response["message"]["content"]
    
    else:
        raise ValueError("Invalid model provider. Use 'openai' or 'ollama'.")

@click.command()
@click.argument("repo")
@click.argument("pr_number", type=int)
@click.option("--model", required=False, default="openai:gpt-4o-mini")
def cli(repo, pr_number, model):
    """Fetch and review a GitHub PR using OpenAI or Ollama with full file context."""
    if not GITHUB_TOKEN:
        click.echo("Error: Please set GITHUB_TOKEN as an environment variable.")
        return
    
    provider, _ = model.split(":", 1)
    if provider == "openai" and not OPENAI_API_KEY:
        click.echo("Error: Please set OPENAI_API_KEY as an environment variable.")
        return
    
    repo_owner, repo_name = repo.split("/")
    
    # Fetch PR details to get the branch name
    pr_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}"
    pr_response = requests.get(pr_url, headers=HEADERS)
    pr_response.raise_for_status()
    pr_data = pr_response.json()
    branch = pr_data['head']['ref']
    
    files = fetch_pr_files(repo_owner, repo_name, pr_number)
    for file in files:
        filename = file['filename']
        if not filename.endswith(".py"):
            continue
        
        diff = file.get('patch', '')  # GitHub API provides 'patch' containing the diff
        
        if not diff:
            click.echo(f"No changes detected in {filename}")
            continue
        
        # Fetch full file content
        full_code = fetch_file_content(repo_owner, repo_name, filename, branch)
        
        click.echo(f"\nReviewing changes in: {filename}")
        
        # Review diff with selected model
        review = review_code(diff, filename, full_code, model)
        click.echo(f"\nReview for {filename}:{review}\n{'-'*40}")

if __name__ == "__main__":
    cli()
