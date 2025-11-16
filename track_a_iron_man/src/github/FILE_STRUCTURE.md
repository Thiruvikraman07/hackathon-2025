# 📁 Clean File Structure

## Current Files (7 total)

```
track_a_iron_man/src/github/
│
├── 🤖 AGENTS (Core Functionality)
│   ├── agent1_repo_to_jd.py           # Agent 1: Company Repo → JD Generator
│   ├── agent2_candidate_evaluator.py  # Agent 2: Candidate Evaluator (Paths 2.1 & 2.2)
│   └── github_client.py               # GitHub API Client (dependency)
│
├── 🧪 TESTS
│   └── test_simple.py                 # Verified working test (run this!)
│
└── 📚 DOCUMENTATION
    ├── README.md                      # Full documentation
    ├── SUMMARY.md                     # Complete overview
    ├── QUICKSTART.md                  # Quick reference
    └── FILE_STRUCTURE.md              # This file
```

---

## File Descriptions

### Core Agents

#### `agent1_repo_to_jd.py` (8.6K)
**Purpose:** Generate Job Description from company repository

**Usage:**
```python
from agent1_repo_to_jd import generate_jd_from_repo
jd, toon = generate_jd_from_repo("company/repo")
```

**Output:** `company_repo_jd.toon`

---

#### `agent2_candidate_evaluator.py` (13K)
**Purpose:** Evaluate candidate's GitHub projects against JD

**Two Paths:**
- Path 2.1: With project links
- Path 2.2: With username only

**Usage:**
```python
from agent2_candidate_evaluator import evaluate_candidate

# Path 2.1
result, toon = evaluate_candidate(jd_text, project_links=[...])

# Path 2.2
result, toon = evaluate_candidate(jd_text, github_username="user")
```

**Output:** `username_evaluation.toon`

---

#### `github_client.py` (11K)
**Purpose:** GitHub API wrapper (dependency for both agents)

**Features:**
- Fetch repository metadata
- Get user repositories
- Sample code files efficiently
- Get repository structure

---

### Tests

#### `test_simple.py` (1.1K)
**Purpose:** Simple, verified working test

**What it tests:**
- ✅ Agent 1: Generate JD from `tiangolo/fastapi`
- ✅ Agent 2 Path 2.2: Evaluate `tiangolo` against JD

**Run:**
```bash
python test_simple.py
```

---

### Documentation

#### `README.md` (9.4K)
Complete documentation with:
- Agent overview
- Usage examples
- Features
- Integration guide

#### `SUMMARY.md` (6.5K)
Quick overview with:
- What was built
- Test results
- File descriptions
- Integration workflow

#### `QUICKSTART.md` (3.2K)
Quick reference with:
- Run test command
- Usage examples
- File locations

---

## Removed Files (Cleanup)

The following old/duplicate files were removed:

❌ `candidate_github_evaluator.py` - Replaced by `agent2_candidate_evaluator.py`
❌ `company_repo_analyzer.py` - Replaced by `agent1_repo_to_jd.py`
❌ `test_agents.py` - Replaced by `test_simple.py`
❌ `test_new_agents.py` - More complex than needed
❌ `test.py` - Old test file
❌ `quick_test.py` - Replaced by `test_simple.py`
❌ `server.py` - Not used in current workflow
❌ `*.toon` - Generated output files (can be recreated)
❌ `__pycache__/` - Python cache directory

---

## File Size Summary

```
agent1_repo_to_jd.py           8.6K
agent2_candidate_evaluator.py   13K
github_client.py                 11K
test_simple.py                  1.1K
README.md                       9.4K
SUMMARY.md                      6.5K
QUICKSTART.md                   3.2K
FILE_STRUCTURE.md              (this file)
--------------------------------
Total: ~52K of clean, working code
```

---

## Quick Start

```bash
# Navigate to directory
cd /Users/thiruanand/2025-hackaton/hackathon-2025/track_a_iron_man/src/github

# Run test
python test_simple.py

# Use agents
python -c "from agent1_repo_to_jd import generate_jd_from_repo; generate_jd_from_repo('repo')"
```

---

## Dependencies

All agents require:
- `langchain` - LLM orchestration
- `langgraph` - Agent framework
- `PyGithub` - GitHub API
- `pydantic` - Data validation
- `toon` - Token encoding (from parent directory)

---

**Last Cleaned:** November 15, 2025
**Status:** ✅ Clean & Tested
**Total Files:** 7 essential files only
