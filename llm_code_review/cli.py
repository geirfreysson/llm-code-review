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

# Set API keys via environment variables for security
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# GitHub API Headers (only if authentication is needed)
AUTH_HEADERS = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"} if GITHUB_TOKEN else {}

def is_repo_public(repo_owner, repo_name):
    """Check if a repository is public."""
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    response = requests.get(url)  # Unauthenticated request
    if response.status_code == 200:
        return True  # Public repo
    elif response.status_code == 404:
        click.echo(f"Error: Repository {repo_owner}/{repo_name} not found.")
    else:
        click.echo(f"Error: Unable to determine repository visibility (Status: {response.status_code}, Response: {response.text}).")
    return False

def fetch_pr_files(repo_owner, repo_name, pr_number, public_repo):
    """Fetch the modified files and their diffs in the pull request."""
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}/files"
    headers = {} if public_repo else AUTH_HEADERS
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        click.echo(f"Error fetching PR files (Status: {response.status_code}, Response: {response.text}).")
        return []
    return response.json()

def fetch_file_content(repo_owner, repo_name, file_path, branch, public_repo):
    """Fetch the full content of a file from the repository."""
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}?ref={branch}"
    headers = {} if public_repo else AUTH_HEADERS
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        click.echo(f"Error fetching file {file_path} (Status: {response.status_code}, Response: {response.text}).")
        return ""
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
    
    try:
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
    except Exception as e:
        click.echo(f"Error during code review: {e}")
        return ""

@click.command()
@click.argument("repo")
@click.argument("pr_number", type=int)
@click.option("--model", required=False, default="openai:gpt-4o-mini")
def cli(repo, pr_number, model):
    """Fetch and review a GitHub PR using OpenAI or Ollama with full file context."""
    repo_owner, repo_name = repo.split("/")
    public_repo = is_repo_public(repo_owner, repo_name)
    
    if not public_repo and not GITHUB_TOKEN:
        click.echo("Error: Private repository detected. Please set GITHUB_TOKEN as an environment variable.")
        return
    
    provider, _ = model.split(":", 1)
    if provider == "openai" and not OPENAI_API_KEY:
        click.echo("Error: Please set OPENAI_API_KEY as an environment variable.")
        return
    
    # Fetch PR details to get the branch name
    pr_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}"
    headers = {} if public_repo else AUTH_HEADERS
    pr_response = requests.get(pr_url, headers=headers)
    if pr_response.status_code != 200:
        click.echo(f"Error fetching PR details (Status: {pr_response.status_code}, Response: {pr_response.text}).")
        return
    pr_data = pr_response.json()
    branch = pr_data['head']['ref']
    
    files = fetch_pr_files(repo_owner, repo_name, pr_number, public_repo)
    if not files:
        click.echo("No files retrieved from the PR. Check repository and PR number.")
        return
    for file in files:
        filename = file['filename']
        if not filename.endswith(".py"):
            continue
        
        diff = file.get('patch', '')
        
        if not diff:
            click.echo(f"No changes detected in {filename}")
            continue
        
        full_code = fetch_file_content(repo_owner, repo_name, filename, branch, public_repo)
        click.echo(f"\nReviewing changes in: {filename}")
        review = review_code(diff, filename, full_code, model)
        click.echo(f"\nReview for {filename}:{review}\n{'-'*40}")

if __name__ == "__main__":
    cli()
