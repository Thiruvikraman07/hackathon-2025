import os

from fastmcp import FastMCP

from .github_client import GitHubClient

# Initialize FastMCP server
mcp = FastMCP("GitHub MCP")

# Initialize GitHub client with token from environment
github_client = GitHubClient(access_token=os.getenv("GITHUB_TOKEN"))


@mcp.tool()
def get_github_profile(username: str) -> dict:
    """Get GitHub user profile information.

    Args:
        username: GitHub username to fetch profile for

    Returns:
        User profile with stats, bio, and other public information
    """
    return github_client.get_profile_info(username)


@mcp.tool()
def list_public_repositories(username: str, language: str | None = None) -> list[dict]:
    """List all public repositories for a GitHub user.

    Args:
        username: GitHub username
        language: Optional language filter (e.g., 'Python', 'JavaScript', 'TypeScript')

    Returns:
        List of public repositories (excluding forks) with metadata
    """
    return github_client.get_public_repositories(username, language)


@mcp.tool()
def sample_repository_files(
    repo_full_name: str, extensions: list[str], max_files: int = 10
) -> list[dict]:
    """Randomly sample files from a GitHub repository by file extensions.

    Args:
        repo_full_name: Full repository name (e.g., 'username/repo-name')
        extensions: List of file extensions to sample (e.g., ['.py', '.js', '.ts'])
        max_files: Maximum number of files to sample (default: 10)

    Returns:
        List of sampled files with path, size, content, and URL
    """
    return github_client.sample_files_by_extension(
        repo_full_name, extensions, max_files
    )


@mcp.tool()
def get_repository_languages(repo_full_name: str) -> dict:
    """Get programming languages used in a repository with byte counts.

    Args:
        repo_full_name: Full repository name (e.g., 'username/repo-name')

    Returns:
        Dictionary mapping language names to byte counts
    """
    return github_client.get_repository_languages(repo_full_name)


@mcp.tool()
def analyze_user_repositories(
    username: str,
    language: str | None = None,
    extensions: list[str] | None = None,
    max_repos: int = 5,
    max_files_per_repo: int = 7,
) -> dict:
    """Complete analysis: get user profile and sample files from their repositories.

    Args:
        username: GitHub username to analyze
        language: Optional language filter for repositories
        extensions: File extensions to sample (e.g., ['.py', '.js']). If None, uses language default
        max_repos: Maximum number of repositories to analyze (default: 5)
        max_files_per_repo: Maximum files to sample per repository (default: 7)

    Returns:
        Complete analysis including profile, repositories, and sampled files
    """
    # Get profile
    profile = github_client.get_profile_info(username)

    # Get repositories
    repos = github_client.get_public_repositories(username, language)

    # Limit repos to analyze
    repos_to_analyze = repos[:max_repos]

    # Default extensions based on language
    if extensions is None:
        language_extensions = {
            "Python": [".py"],
            "JavaScript": [".js", ".jsx"],
            "TypeScript": [".ts", ".tsx"],
            "Java": [".java"],
            "Go": [".go"],
            "Rust": [".rs"],
            "Ruby": [".rb"],
            "PHP": [".php"],
            "C++": [".cpp", ".hpp", ".cc", ".h"],
            "C": [".c", ".h"],
            "C#": [".cs"],
        }
        extensions = language_extensions.get(language, [".py"])

    # Sample files from each repository
    repository_samples = []
    for repo in repos_to_analyze:
        try:
            files = github_client.sample_files_by_extension(
                repo["full_name"], extensions, max_files_per_repo
            )
            repository_samples.append(
                {"repository": repo, "sampled_files": files, "files_count": len(files)}
            )
        except Exception as e:
            repository_samples.append(
                {"repository": repo, "error": str(e), "files_count": 0}
            )

    total_files_sampled = sum(rs["files_count"] for rs in repository_samples)

    return {
        "profile": profile,
        "total_repositories": len(repos),
        "repositories_analyzed": len(repos_to_analyze),
        "total_files_sampled": total_files_sampled,
        "extensions_searched": extensions,
        "repository_samples": repository_samples,
    }
