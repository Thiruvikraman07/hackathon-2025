# Local Repository Support for Pipeline 1 (JD Generator)

## Overview

Pipeline 1 JD Generator now supports **both GitHub repositories and local file system repositories**. The system automatically detects which type of repository you're using and applies the appropriate analysis tools.

## Features

### 1. Automatic Repository Type Detection
- **Local Path**: If the input is a valid directory path, it uses local file system tools
- **GitHub Repo**: If the input matches the format `owner/repo`, it uses GitHub API tools
- Clear error messages for invalid inputs

### 2. Local Repository Tools

Three new tools have been added for local repository analysis:

#### `fetch_local_repo_metadata(repo_path: str)`
- Scans the local directory structure
- Counts files by extension
- Maps extensions to programming languages
- Returns metadata similar to GitHub API format

#### `get_local_repo_file_structure(repo_path: str)`
- Walks through the directory tree
- Filters out non-code directories (node_modules, .git, etc.)
- Returns list of code files, documentation, and config files
- Limits to 500 most relevant files

#### `fetch_local_code_files(repo_path: str, file_paths: List[str])`
- Reads specific files from local filesystem
- Handles encoding errors gracefully
- Enforces 1MB file size limit
- Returns file content with metadata

### 3. Smart File Filtering

Automatically filters out:
- `.git`, `node_modules`, `__pycache__`
- `.venv`, `venv`, `build`, `dist`, `.next`
- Binary files and non-code files

Includes:
- Code files (.py, .js, .ts, .java, .go, etc.)
- Documentation (.md, .txt, .rst)
- Config files (package.json, requirements.txt, etc.)

## Usage

### Example 1: GitHub Repository

```python
from track_a_iron_man.pipeline1_jd_generator import generate_jd

jd, toon = generate_jd(
    company_repo="facebook/react",
    job_title="Senior Frontend Developer",
    salary_range="$120k-$160k",
    additional_requirements=[
        "5+ years React experience",
        "Team leadership skills"
    ],
    verbose=True,
    testing=True  # Enables GitHub data caching
)
```

### Example 2: Local Repository

```python
from track_a_iron_man.pipeline1_jd_generator import generate_jd

jd, toon = generate_jd(
    company_repo="/path/to/your/local/repo",
    job_title="Backend Engineer",
    salary_range="$100k-$140k",
    additional_requirements=[
        "Python expertise",
        "FastAPI experience"
    ],
    verbose=True,
    testing=False  # Testing mode not applicable for local repos
)
```

### Example 3: Relative Path

```python
# You can also use relative paths
jd, toon = generate_jd(
    company_repo="./my_project",
    job_title="Full Stack Developer",
    salary_range="$110k-$150k",
    verbose=True
)
```

## Test Repository

A test repository has been created at `test_local_repo/` with:
- Python FastAPI backend code
- Authentication and user management
- Database models and services
- Test files
- Documentation (README.md)
- Configuration files

### Running the Test

```bash
python track_a_iron_man/test_local_repo_jd.py
```

This will:
1. Analyze the local test repository
2. Generate a complete job description
3. Create a TOON file: `local_test_local_repo_jd.toon`
4. Display comprehensive results

## Output Files

### GitHub Repository
- Filename format: `{owner}_{repo}_jd.toon`
- Example: `facebook_react_jd.toon`

### Local Repository
- Filename format: `local_{repo_name}_jd.toon`
- Example: `local_test_local_repo_jd.toon`

## Key Implementation Details

### Repository Detection Logic

```python
repo_path_obj = Path(company_repo)

if repo_path_obj.exists() and repo_path_obj.is_dir():
    # Use local repository tools
    is_local_repo = True
elif '/' in company_repo and not company_repo.startswith('/'):
    # Use GitHub API tools
    is_local_repo = False
else:
    # Invalid format
    raise ValueError("Invalid repository format")
```

### Agent Configuration

```python
if is_local_repo:
    agent = create_react_agent(
        llm,
        tools=[
            fetch_local_repo_metadata,
            get_local_repo_file_structure,
            fetch_local_code_files
        ],
        response_format=JobDescription
    )
else:
    agent = create_react_agent(
        llm,
        tools=[
            fetch_repo_metadata,
            get_repo_file_structure,
            fetch_code_files
        ],
        response_format=JobDescription
    )
```

## Benefits

1. **Privacy**: Analyze private company repositories without GitHub access
2. **Speed**: No API rate limits or network delays
3. **Flexibility**: Works with any local codebase
4. **Testing**: Easy to test with local sample repositories
5. **Offline**: Can work without internet connection (except for LLM API)

## Limitations

1. **No Git History**: Local analysis doesn't include commit history or stars
2. **No Caching**: Testing mode cache only works for GitHub repos
3. **Manual Path**: You need to provide the correct absolute or relative path

## Error Handling

The system provides clear error messages:
- `"Local repository path '{path}' does not exist or is not a directory"`
- `"Invalid repository format. Use 'owner/repo' for GitHub or provide a valid local path"`
- File-level warnings for unreadable or binary files

## Performance

- **Local repos**: Faster than GitHub (no API calls)
- **Large repos**: Automatically limits to 500 most relevant files
- **File size**: Enforces 1MB limit per file to prevent memory issues

## Future Enhancements

Potential improvements:
1. Support for zip/tar archives
2. Git repository metadata extraction (even for local repos)
3. Configurable file filtering patterns
4. Multi-repository support
5. Incremental analysis for large codebases
