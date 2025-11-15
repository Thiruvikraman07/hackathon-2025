import os

from .github_client import GitHubClient

# Initialize GitHub client
# Token is optional for public repos - uncomment the line below to use without token
# github_client = GitHubClient()  # No token - 60 requests/hour
github_client = GitHubClient()  # With token - 5000 requests/hour

# Show rate limit info
print("=" * 60)
print("API RATE LIMIT INFO")
print("=" * 60)
rate_info = github_client.get_rate_limit_info()
print(f"Using authentication: {rate_info['using_auth']}")
print(f"Rate limit: {rate_info['limit']} requests/hour")
print(f"Remaining: {rate_info['remaining']} requests")
print(f"Resets at: {rate_info['reset_time']}")
print()

# Get profile info
print("=" * 60)
print("PROFILE INFORMATION")
print("=" * 60)
result = github_client.get_profile_info("baljinnyamday")
print(f"Username: {result['username']}")
print(f"Name: {result['name']}")
print(f"Bio: {result['bio']}")
print(f"Location: {result['location']}")
print(f"Public Repos: {result['public_repos']}")
print(f"Followers: {result['followers']}")
print(f"Following: {result['following']}")
print()

# Get random repositories for analysis
print("=" * 60)
print("RANDOM REPOSITORIES FOR ANALYSIS")
print("=" * 60)
random_repos = github_client.get_random_repositories(
    username="baljinnyamday", count=2, min_stars=0  # Select 2 random repos
)

print(f"Selected {len(random_repos)} random repositories:\n")
for i, repo in enumerate(random_repos, 1):
    print(f"{i}. {repo['name']}")
    print(f"   Language: {repo['language']}")
    print(f"   Stars: {repo['stars']}")
    print(f"   Description: {repo['description']}")
    print(f"   URL: {repo['url']}")
    print()

# Get random files from those repositories
print("=" * 60)
print("RANDOM FILES FOR CODE QUALITY ANALYSIS")
print("=" * 60)

# Determine extensions based on the main languages
extensions = [".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs"]

files_by_repo = github_client.get_random_files_from_repos(
    repo_list=random_repos,
    extensions=extensions,
    files_per_repo=5,  # Get 5 files per repo
)

for repo_name, files in files_by_repo.items():
    print(f"\n{repo_name}:")
    print(f"  Found {len(files)} files for analysis:\n")
    for file in files:
        print(f"  📄 {file['path']}")
        print(f"     Size: {file['size']} bytes")
        print(f"     Lines: {len(file['content'].splitlines())}")
        print(f"     URL: {file['url']}")
        print(f"\n{'=' * 60}")
        print(f"CODE CONTENT:")
        print(f"{'=' * 60}")
        print(file["content"])
        print(f"{'=' * 60}\n")

print("=" * 60)
print(
    f"SUMMARY: Analyzed {sum(len(files) for files in files_by_repo.values())} files from {len(files_by_repo)} repositories"
)
print("=" * 60)
