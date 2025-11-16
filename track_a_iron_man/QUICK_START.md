# Quick Start Guide: Local Repository Support

## TL;DR

Pipeline 1 now accepts **BOTH** GitHub repos and local paths!

```python
# GitHub repo
generate_jd(company_repo="facebook/react", ...)

# Local repo
generate_jd(company_repo="/path/to/repo", ...)
```

System automatically detects which type and handles it correctly.

## Quick Examples

### Example 1: Analyze Local Repository

```python
from track_a_iron_man.pipeline1_jd_generator import generate_jd

jd, toon = generate_jd(
    company_repo="/Users/me/my_project",  # ← Local path
    job_title="Senior Backend Developer",
    salary_range="$140k-$180k",
    additional_requirements=[
        "Python expertise",
        "FastAPI experience"
    ],
    verbose=True
)

print(f"Generated: {jd.job_title}")
print(f"Output: local_my_project_jd.toon")
```

### Example 2: Analyze GitHub Repository

```python
from track_a_iron_man.pipeline1_jd_generator import generate_jd

jd, toon = generate_jd(
    company_repo="fastapi/fastapi",  # ← GitHub repo
    job_title="Senior Backend Developer",
    salary_range="$140k-$180k",
    additional_requirements=[
        "Python expertise",
        "FastAPI experience"
    ],
    verbose=True,
    testing=True  # Cache GitHub data
)

print(f"Generated: {jd.job_title}")
print(f"Output: fastapi_fastapi_jd.toon")
```

## Running Tests

### Test Local Repository
```bash
python track_a_iron_man/test_local_repo_jd.py
```

### Interactive Demo (Both Types)
```bash
python track_a_iron_man/demo_comparison.py
```

## How Detection Works

| Input | Detected As | Tools Used |
|-------|-------------|------------|
| `/Users/me/project` | Local | Local file system tools |
| `./my_project` | Local | Local file system tools |
| `../other_project` | Local | Local file system tools |
| `facebook/react` | GitHub | GitHub API tools |
| `owner/repo` | GitHub | GitHub API tools |

## Key Differences

| Feature | Local Repo | GitHub Repo |
|---------|------------|-------------|
| Privacy | ✅ Private code | ❌ Public only |
| Speed | ✅ Fast | ⚠️ Network dependent |
| Offline | ✅ Yes (except LLM) | ❌ No |
| Rate Limits | ✅ None | ⚠️ GitHub limits |
| Caching | ❌ N/A | ✅ Supported |

## Need Help?

- 📖 Full documentation: `LOCAL_REPO_FEATURE.md`
- 📝 Implementation details: `IMPLEMENTATION_SUMMARY.md`
- 🧪 Run tests: `test_local_repo_jd.py`
- 🎭 See demo: `demo_comparison.py`
