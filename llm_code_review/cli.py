import requests
import openai
import click
import os
from dotenv import load_dotenv

load_dotenv()

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
        import base64
        return base64.b64decode(file_data['content']).decode('utf-8')
    return ""

def review_code_with_openai(diff, filename, full_code):
    """Send the full file content along with the changed code (diff) to OpenAI for review."""
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    prompt = f"""
    You are a code reviewer. Review the following Git diff from {filename} for potential bugs.
    Use the full file content as context, but focus only on the changes.
    Suggest improvements where necessary. Keep it concise, don't highlight positives, just negatives.
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

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content

@click.command()
@click.argument("repo")
@click.argument("pr_number", type=int)
def cli(repo, pr_number):
    """Fetch and review a GitHub PR using OpenAI with full file context"""
    if not GITHUB_TOKEN or not OPENAI_API_KEY:
        click.echo("Error: Please set GITHUB_TOKEN and OPENAI_API_KEY as environment variables.")
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
        
        # Review diff with OpenAI using full file context
        review = review_code_with_openai(diff, filename, full_code)
        click.echo(f"\nReview for {filename}:{review}\n{'-'*40}")

if __name__ == "__main__":
    cli()
