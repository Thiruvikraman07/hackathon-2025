import random
from typing import Any

import requests
from github import Github, GithubException


class GitHubClient:
    """Client for fetching GitHub public repositories and sampling code files.

    Uses only public data - no authentication required.
    Minimizes API calls by fetching file contents directly from raw.githubusercontent.com.
    """

    def __init__(self):
        """Initialize GitHub client for public repositories only."""
        self.github = Github()  # No authentication - public access only

    def get_profile_info(self, username: str) -> dict[str, Any]:
        """Get GitHub user profile information."""
        try:
            user = self.github.get_user(username)
            return {
                "username": user.login,
                "name": user.name,
                "bio": user.bio,
                "location": user.location,
                "email": user.email,
                "public_repos": user.public_repos,
                "followers": user.followers,
                "following": user.following,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                "company": user.company,
                "blog": user.blog,
                "avatar_url": user.avatar_url,
            }
        except GithubException as e:
            raise ValueError(f"Failed to fetch user profile: {e}")

    def get_public_repositories(
        self, username: str, language: str | None = None
    ) -> list[dict[str, Any]]:
        """Get all public repositories for a user, optionally filtered by language."""
        try:
            user = self.github.get_user(username)
            repos = user.get_repos()

            public_repos = []
            for repo in repos:
                if repo.fork:
                    continue

                # Filter by language if specified
                if language and repo.language != language:
                    continue

                public_repos.append(
                    {
                        "name": repo.name,
                        "full_name": repo.full_name,
                        "description": repo.description,
                        "stars": repo.stargazers_count,
                        "forks": repo.forks_count,
                        "language": repo.language,
                        "size": repo.size,
                        "updated_at": (
                            repo.updated_at.isoformat() if repo.updated_at else None
                        ),
                        "url": repo.html_url,
                        "default_branch": repo.default_branch,
                    }
                )

            return public_repos
        except GithubException as e:
            raise ValueError(f"Failed to fetch repositories: {e}")

    def sample_files_by_extension(
        self, repo_full_name: str, extensions: list[str], max_files: int = 10
    ) -> list[dict[str, Any]]:
        """Randomly sample files from a repository by file extensions.

        Args:
            repo_full_name: Full repository name (e.g., 'username/repo')
            extensions: List of file extensions to sample (e.g., ['.py', '.js', '.ts'])
            max_files: Maximum number of files to sample

        Returns:
            List of sampled files with path, size, and content
        """
        try:
            repo = self.github.get_repo(repo_full_name)
            matching_files = []

            def traverse_contents(contents):
                for content in contents:
                    if content.type == "dir":
                        try:
                            traverse_contents(repo.get_contents(content.path))
                        except GithubException:
                            continue
                    else:
                        # Check if file matches any of the extensions
                        if any(content.name.endswith(ext) for ext in extensions):
                            matching_files.append(content)

            try:
                contents = repo.get_contents("")
                traverse_contents(contents)
            except GithubException:
                return []

            # Randomly sample files
            sample_size = min(max_files, len(matching_files))
            if sample_size == 0:
                return []

            sampled = random.sample(matching_files, sample_size)

            result = []
            for file in sampled:
                try:
                    content = file.decoded_content.decode("utf-8")
                    result.append(
                        {
                            "path": file.path,
                            "size": file.size,
                            "content": content,
                            "sha": file.sha,
                            "url": file.html_url,
                        }
                    )
                except Exception:
                    # Skip files that can't be decoded (binary files, etc.)
                    continue

            return result
        except GithubException as e:
            raise ValueError(f"Failed to sample files: {e}")

    def get_repository_languages(self, repo_full_name: str) -> dict[str, int]:
        """Get languages used in a repository with byte counts."""
        try:
            repo = self.github.get_repo(repo_full_name)
            return repo.get_languages()
        except GithubException as e:
            raise ValueError(f"Failed to fetch repository languages: {e}")

    def sample_files_efficiently(
        self,
        repo_full_name: str,
        extensions: list[str],
        max_files: int = 10,
        max_file_size: int = 1_000_000,  # 1MB max per file
    ) -> list[dict[str, Any]]:
        """Efficiently sample files using git tree API and raw content fetching.

        This method uses only 1-2 API calls instead of recursively traversing directories,
        making it much more efficient and less likely to hit rate limits.

        Args:
            repo_full_name: Full repository name (e.g., 'username/repo')
            extensions: List of file extensions to sample (e.g., ['.py', '.js', '.ts'])
            max_files: Maximum number of files to sample
            max_file_size: Maximum file size in bytes to fetch (default: 1MB)

        Returns:
            List of sampled files with path, size, and content
        """
        try:
            repo = self.github.get_repo(repo_full_name)
            default_branch = repo.default_branch

            # Get the entire tree in one API call (recursive)
            tree = repo.get_git_tree(default_branch, recursive=True)

            # Filter files by extension and size
            matching_files = []
            for item in tree.tree:
                if item.type == "blob":  # It's a file
                    # Check if file matches any extension
                    if any(item.path.endswith(ext) for ext in extensions):
                        # Check size constraint
                        if item.size and item.size <= max_file_size:
                            matching_files.append(
                                {
                                    "path": item.path,
                                    "size": item.size,
                                    "sha": item.sha,
                                }
                            )

            if not matching_files:
                return []

            # Randomly sample files
            sample_size = min(max_files, len(matching_files))
            sampled = random.sample(matching_files, sample_size)

            # Fetch raw content directly from githubusercontent.com (no API rate limit)
            result = []
            for file_info in sampled:
                try:
                    # Construct raw content URL
                    raw_url = f"https://raw.githubusercontent.com/{repo_full_name}/{default_branch}/{file_info['path']}"

                    response = requests.get(raw_url, timeout=10)
                    if response.status_code == 200:
                        try:
                            content = response.text
                            result.append(
                                {
                                    "path": file_info["path"],
                                    "size": file_info["size"],
                                    "content": content,
                                    "sha": file_info["sha"],
                                    "url": f"https://github.com/{repo_full_name}/blob/{default_branch}/{file_info['path']}",
                                }
                            )
                        except UnicodeDecodeError:
                            # Skip binary files
                            continue
                except requests.RequestException:
                    # Skip files that fail to fetch
                    continue

            return result
        except GithubException as e:
            raise ValueError(f"Failed to sample files: {e}")

    def get_random_repositories(
        self,
        username: str,
        count: int = 2,
        language: str | None = None,
        min_stars: int = 0,
    ) -> list[dict[str, Any]]:
        """Get random repositories from a user's public repositories.

        Args:
            username: GitHub username
            count: Number of random repositories to select (default: 2)
            language: Optional language filter
            min_stars: Minimum number of stars required (default: 0)

        Returns:
            List of randomly selected repositories
        """
        repos = self.get_public_repositories(username, language)

        # Filter by minimum stars if specified
        if min_stars > 0:
            repos = [repo for repo in repos if repo["stars"] >= min_stars]

        if not repos:
            return []

        # Select random repositories
        sample_size = min(count, len(repos))
        return random.sample(repos, sample_size)

    def get_random_files_from_repos(
        self,
        repo_list: list[dict[str, Any]],
        extensions: list[str],
        files_per_repo: int = 5,
    ) -> dict[str, list[dict[str, Any]]]:
        """Get random files from multiple repositories for code quality analysis.

        Uses efficient fetching to avoid rate limits.

        Args:
            repo_list: List of repository dictionaries (from get_random_repositories)
            extensions: List of file extensions to sample (e.g., ['.py', '.js', '.ts'])
            files_per_repo: Number of files to sample from each repository (default: 5)

        Returns:
            Dictionary mapping repository full_name to list of sampled files
        """
        results = {}

        for repo in repo_list:
            repo_full_name = repo["full_name"]
            try:
                # Use efficient method to avoid rate limits
                files = self.sample_files_efficiently(
                    repo_full_name, extensions, max_files=files_per_repo
                )
                if files:
                    results[repo_full_name] = files
            except ValueError as e:
                # Log error but continue with other repos
                print(f"Warning: Could not sample files from {repo_full_name}: {e}")
                continue

        return results

    def get_file_structure(self, repo_full_name: str) -> list[dict[str, Any]]:
        """Get complete file/directory structure of repository.

        Args:
            repo_full_name: Full repository name (e.g., 'username/repo')

        Returns:
            List of file/directory items with path, type, and size
        """
        try:
            repo = self.github.get_repo(repo_full_name)
            default_branch = repo.default_branch

            # Get the entire tree in one API call (recursive)
            tree = repo.get_git_tree(default_branch, recursive=True)

            structure = []
            for item in tree.tree:
                structure.append({
                    "path": item.path,
                    "type": item.type,  # "blob" (file) or "tree" (directory)
                    "size": item.size if item.size else 0,
                })

            return structure
        except GithubException as e:
            raise ValueError(f"Failed to get file structure: {e}")

    def fetch_specific_files(
        self,
        repo_full_name: str,
        file_paths: list[str],
        max_file_size: int = 1_000_000,  # 1MB max per file
    ) -> list[dict[str, Any]]:
        """Fetch specific files by their paths.

        Args:
            repo_full_name: Full repository name (e.g., 'username/repo')
            file_paths: List of file paths to fetch
            max_file_size: Maximum file size in bytes to fetch (default: 1MB)

        Returns:
            List of files with path, content, and size
        """
        try:
            repo = self.github.get_repo(repo_full_name)
            default_branch = repo.default_branch

            files = []
            for path in file_paths:
                try:
                    # Construct raw content URL
                    raw_url = f"https://raw.githubusercontent.com/{repo_full_name}/{default_branch}/{path}"

                    response = requests.get(raw_url, timeout=10)
                    if response.status_code == 200:
                        # Check file size
                        content_length = len(response.content)
                        if content_length > max_file_size:
                            print(f"Warning: Skipping {path} - file too large ({content_length} bytes)")
                            continue

                        try:
                            content = response.text
                            files.append({
                                "path": path,
                                "content": content,
                                "size": content_length,
                                "url": f"https://github.com/{repo_full_name}/blob/{default_branch}/{path}",
                            })
                        except UnicodeDecodeError:
                            # Skip binary files
                            print(f"Warning: Skipping {path} - binary file")
                            continue
                    else:
                        print(f"Warning: Could not fetch {path} - HTTP {response.status_code}")
                except requests.RequestException as e:
                    print(f"Warning: Failed to fetch {path}: {e}")
                    continue

            return files
        except GithubException as e:
            raise ValueError(f"Failed to fetch files: {e}")
