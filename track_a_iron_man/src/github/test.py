from github_client import GitHubClient

# Initialize GitHub client (no token required - uses public data only)
github_client = GitHubClient()

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

# Get 1-2 random repositories for analysis
print("=" * 60)
print("RANDOM REPOSITORIES FOR ANALYSIS")
print("=" * 60)
random_repos = github_client.get_random_repositories(
    username="baljinnyamday", count=2, min_stars=0  # Select 1-2 random repos
)

print(f"Selected {len(random_repos)} random repositories:\n")
for i, repo in enumerate(random_repos, 1):
    print(f"{i}. {repo['name']}")
    print(f"   Language: {repo['language']}")
    print(f"   Stars: {repo['stars']}")
    print(f"   Description: {repo['description']}")
    print(f"   URL: {repo['url']}")
    print()

# Get 10-15 random code files from those repositories
print("=" * 60)
print("RANDOM FILES FOR CODE QUALITY ANALYSIS")
print("=" * 60)

# Common code file extensions
extensions = [
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".java",
    ".go",
    ".rs",
    ".cpp",
    ".c",
    ".rb",
]

files_by_repo = github_client.get_random_files_from_repos(
    repo_list=random_repos,
    extensions=extensions,
    files_per_repo=15,  # Get 10-15 files per repo
)

# Display the selected code files
total_files = 0
for repo_name, files in files_by_repo.items():
    print(f"\n{repo_name}:")
    print(f"  Found {len(files)} files for analysis:\n")
    total_files += len(files)
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
print(f"SUMMARY: Analyzed {total_files} files from {len(files_by_repo)} repositories")
print("=" * 60)
