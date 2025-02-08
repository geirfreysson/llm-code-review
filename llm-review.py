import requests
import openai
import click
import base64
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

def fetch_pull_request(repo_owner, repo_name, pr_number):
    """Fetch pull request details from GitHub"""
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def fetch_pr_files(repo_owner, repo_name, pr_number):
    """Fetch the modified files in the pull request"""
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}/files"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def fetch_file_content(repo_owner, repo_name, file_path):
    """Fetch the content of a file from the PR"""
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    file_data = response.json()
    return base64.b64decode(file_data["content"]).decode("utf-8")


def review_code_with_openai(diff, filename):
    """Send only the changed code (diff) to OpenAI for a focused review."""
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    prompt = f"""
    You are a code reviewer. Review the following Git diff from {filename} for best practices, efficiency, readability, and potential bugs.
    Focus only on the changes and suggest improvements where necessary.

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
def review_pr(repo, pr_number):
    """Fetch and review a GitHub PR using OpenAI"""
    if not GITHUB_TOKEN or not OPENAI_API_KEY:
        click.echo("Error: Please set GITHUB_TOKEN and OPENAI_API_KEY as environment variables.")
        return
    
    repo_owner, repo_name = repo.split("/")
    
    pr_details = fetch_pull_request(repo_owner, repo_name, pr_number)
    click.echo(f"Reviewing PR #{pr_number}: {pr_details['title']}")

    files = fetch_pr_files(repo_owner, repo_name, pr_number)
    for file in files:
        filename = file['filename']
        click.echo(f"\nFetching file: {filename}")

        # Fetch file content
        file_content = fetch_file_content(repo_owner, repo_name, filename)

        # Review file with OpenAI
        review = review_code_with_openai(file_content, filename)
        click.echo(f"\nReview for {filename}:\n{review}\n{'-'*40}")

if __name__ == "__main__":
    review_pr()
