# GitHub Analysis Agents

Two intelligent agents for analyzing company repositories and evaluating candidates.

## 🎯 Agent Overview

### Agent 1: Company Repo → Job Description Generator
**File:** `agent1_repo_to_jd.py`

**Purpose:** Analyzes a company repository and generates a complete Job Description for candidate onboarding.

**Input:** Company repository URL (e.g., `tiangolo/fastapi`)

**Output:** Job Description in TOON format with:
- Job title
- Overview
- Technical requirements (languages, frameworks, tools, databases)
- Responsibilities
- Qualifications (must-have, nice-to-have, experience level)
- What candidate will learn

---

### Agent 2: Candidate Project Evaluator
**File:** `agent2_candidate_evaluator.py`

**Purpose:** Evaluates candidate's GitHub projects against a Job Description using smart file selection.

**Two Evaluation Paths:**

#### Path 2.1: GitHub Project Links Provided
When resume contains specific GitHub project URLs:
1. Filter projects by relevance to JD
2. For relevant projects: Analyze 2-3 key files and rate quality

#### Path 2.2: Only GitHub Username
When only GitHub username is available:
1. Get all repositories from GitHub profile
2. Filter repos by title relevance to JD
3. For relevant repos: Analyze 2-3 key files and rate quality

**Output:** Candidate evaluation in TOON format with:
- Overall rating (1-100)
- JD fit score (1-100)
- Project relevance assessments
- Quality ratings for relevant projects
- Hiring recommendation (strong-yes/yes/maybe/no)

---

## 📁 Files

```
src/github/
├── agent1_repo_to_jd.py           # Agent 1: Repo → JD
├── agent2_candidate_evaluator.py  # Agent 2: Candidate Evaluator
├── github_client.py               # GitHub API client
├── test_simple.py                 # Simple working test
├── test_new_agents.py             # Comprehensive test suite
└── README.md                      # This file
```

---

## 🚀 Quick Start

### Test Agent 1 (Repo → JD)

```bash
cd /Users/thiruanand/2025-hackaton/hackathon-2025/track_a_iron_man/src/github

# Run Agent 1 standalone
python agent1_repo_to_jd.py
```

### Test Agent 2 (Candidate Evaluation)

```python
from agent2_candidate_evaluator import evaluate_candidate

# Path 2.1: With project links
result, toon = evaluate_candidate(
    jd_text="Python Developer, Required: Python, FastAPI...",
    project_links=[
        "https://github.com/username/project1",
        "https://github.com/username/project2"
    ]
)

# Path 2.2: Only username
result, toon = evaluate_candidate(
    jd_text="Python Developer, Required: Python, FastAPI...",
    github_username="username"
)
```

### Run Tests

```bash
# Simple test (VERIFIED WORKING)
python test_simple.py

# Individual tests
python test_new_agents.py 1  # Test Agent 1
python test_new_agents.py 2  # Test Agent 2 Path 2.1
python test_new_agents.py 3  # Test Agent 2 Path 2.2
python test_new_agents.py 4  # Test End-to-End

# All tests
python test_new_agents.py
```

---

## 💡 Usage Examples

### Example 1: Generate JD from Company Repo

```python
from agent1_repo_to_jd import generate_jd_from_repo

# Analyze FastAPI repository
jd, toon = generate_jd_from_repo("tiangolo/fastapi", verbose=True)

print(f"Job Title: {jd.job_title}")
print(f"Experience Level: {jd.qualifications.experience_level}")
print(f"Must-Have Skills: {jd.qualifications.must_have_skills}")

# Output saved to: tiangolo_fastapi_jd.toon
```

**Output:**
```
Job Title: Senior Python Backend Developer - FastAPI Core
Experience Level: senior (5+ years)
Must-Have Skills: ['Expert-level Python programming', 'Type hints', ...]
```

### Example 2: Evaluate Candidate (Path 2.1 - Project Links)

```python
from agent2_candidate_evaluator import evaluate_candidate

jd_text = """
Senior Python Developer
Required: Python, FastAPI, REST APIs, pytest
Nice to have: Docker, AWS
"""

# Resume has specific project links
result, toon = evaluate_candidate(
    jd_text=jd_text,
    project_links=[
        "https://github.com/user/api-project",
        "https://github.com/user/web-scraper"
    ],
    verbose=True
)

print(f"Overall Rating: {result.overall_rating}/100")
print(f"JD Fit Score: {result.jd_fit_score}/100")
print(f"Recommendation: {result.recommendation}")
```

### Example 3: Evaluate Candidate (Path 2.2 - Username Only)

```python
from agent2_candidate_evaluator import evaluate_candidate

jd_text = """
Full-Stack Developer
Required: JavaScript, React, Node.js
"""

# Only GitHub username available
result, toon = evaluate_candidate(
    jd_text=jd_text,
    github_username="username",
    verbose=True
)

print(f"Projects Found: {result.total_projects_found}")
print(f"Relevant Projects: {sum(1 for p in result.relevant_projects if p.is_relevant)}")
print(f"Overall Rating: {result.overall_rating}/100")
```

### Example 4: End-to-End Workflow

```python
from agent1_repo_to_jd import generate_jd_from_repo
from agent2_candidate_evaluator import evaluate_candidate

# Step 1: Company analyzes their repo to create JD
jd, _ = generate_jd_from_repo("company/repo")

# Step 2: Convert JD to text
jd_text = f"""
{jd.job_title}
Required: {', '.join(jd.qualifications.must_have_skills)}
Experience: {jd.qualifications.experience_level}
"""

# Step 3: Evaluate candidate against JD
result, _ = evaluate_candidate(
    jd_text=jd_text,
    github_username="candidate"
)

# Step 4: Make hiring decision
if result.recommendation in ["strong-yes", "yes"]:
    print(f"✅ Recommend hiring! Score: {result.jd_fit_score}/100")
else:
    print(f"❌ Not a good fit. Score: {result.jd_fit_score}/100")
```

---

## 🔑 Key Features

### Agent 1 Features:
- ✅ Analyzes repository structure and code
- ✅ Extracts tech stack automatically
- ✅ Generates realistic job responsibilities
- ✅ Determines appropriate experience level
- ✅ Output in TOON format (token-efficient)

### Agent 2 Features:
- ✅ **Smart File Selection** - Only analyzes 2-3 most relevant files per project
- ✅ **Two Evaluation Paths** - Handles both project links and username-only
- ✅ **Relevance Filtering** - Filters projects by title and content relevance
- ✅ **Quality Assessment** - Rates code quality, technical depth, best practices
- ✅ **JD Fit Scoring** - Calculates how well candidate matches requirements
- ✅ Output in TOON format (token-efficient)

---

## 📊 Output Format

### Agent 1 Output (JD)
```toon
job_title: Senior Python Backend Developer
company_repo: tiangolo/fastapi
overview: Looking for a developer to work on FastAPI...
technical_requirements:
  primary_languages[1]: Python
  frameworks_libraries[4]: FastAPI,Pydantic,Starlette,pytest
  ...
qualifications:
  experience_level: senior
  minimum_years: 5
  must_have_skills[7]: Expert Python,Type hints,REST APIs,...
```

### Agent 2 Output (Evaluation)
```toon
candidate_github_username: username
evaluation_path: path_2.2
overall_rating: 85
jd_fit_score: 90
recommendation: yes
relevant_projects[2]:
  0:
    project_name: api-project
    is_relevant: true
    relevance_score: 9
quality_assessments[1]:
  0:
    overall_score: 88
    code_quality_score: 9
    ...
```

---

## ✅ Verified Tests

The following test has been **verified working**:

```bash
python test_simple.py
```

**Test Results:**
- ✅ Agent 1: Generates JD from `tiangolo/fastapi`
- ✅ Agent 2: Evaluates candidate `tiangolo` against generated JD
- ✅ Path 2.2: Successfully filters repos and rates quality
- ✅ Output: Proper TOON format files created

---

## 📝 Notes

1. **Token Efficiency**: All outputs use TOON format for 30-60% token reduction
2. **Smart Analysis**: Agent 2 only analyzes 2-3 key files per project (not all files)
3. **Real-time Evaluation**: Agents fetch live data from GitHub
4. **Flexible Input**: Agent 2 works with both project links and username only
5. **Practical Output**: Generates actionable hiring recommendations

---

## 🐛 Troubleshooting

### Import Error
```bash
ModuleNotFoundError: No module named 'react_agent'
```
**Fix:** Check that paths are correct (should be `../../../core`)

### GitHub Rate Limit
```bash
Failed to fetch repositories: API rate limit exceeded
```
**Fix:** Add GitHub token to `.env` file (optional, increases rate limit)

### No Projects Found
```bash
total_projects_found: 0
```
**Fix:** Verify GitHub username is correct and has public repositories

---

## 🎯 Integration with Resume Agent

These agents are designed to work with the resume extraction agent:

```python
# 1. Extract resume
from resume_agent import analyze_resume_with_toon
resume_data, _ = analyze_resume_with_toon("candidate_resume.pdf")

# 2. Generate JD from company repo
from agent1_repo_to_jd import generate_jd_from_repo
jd, _ = generate_jd_from_repo("company/repo")

# 3. Evaluate candidate
from agent2_candidate_evaluator import evaluate_candidate

# Check if resume has GitHub projects
if resume_data.projects and any(p.github_link for p in resume_data.projects):
    # Path 2.1: Use project links
    project_links = [p.github_link for p in resume_data.projects if p.github_link]
    result, _ = evaluate_candidate(jd_text, project_links=project_links)
else:
    # Path 2.2: Use GitHub username from contact
    result, _ = evaluate_candidate(jd_text, github_username=resume_data.contact.github)
```

---

## 📚 Dependencies

- `langchain` - LLM orchestration
- `langgraph` - Agent creation
- `PyGithub` - GitHub API
- `pydantic` - Data validation
- `toon` - Token-efficient encoding

---

**Created:** November 2025
**Status:** ✅ Tested and Working
**Test File:** `test_simple.py`
