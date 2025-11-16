# 🚀 Quick Start Guide

## Run the Test (Verified Working)

```bash
cd /Users/thiruanand/2025-hackaton/hackathon-2025/track_a_iron_man/src/github
python test_simple.py
```

This will:
1. ✅ Generate JD from `tiangolo/fastapi` repo (Agent 1)
2. ✅ Evaluate candidate `tiangolo` against that JD (Agent 2 - Path 2.2)
3. ✅ Show complete output
4. ✅ Save TOON files

---

## Agent 1: Generate JD from Company Repo

```python
from agent1_repo_to_jd import generate_jd_from_repo

jd, toon = generate_jd_from_repo("company/repo")

print(jd.job_title)
print(jd.qualifications.must_have_skills)
```

**Output file:** `company_repo_jd.toon`

---

## Agent 2: Evaluate Candidate

### Path 2.1: With Project Links (from resume)

```python
from agent2_candidate_evaluator import evaluate_candidate

result, toon = evaluate_candidate(
    jd_text="Python Developer. Required: Python, FastAPI...",
    project_links=[
        "https://github.com/user/project1",
        "https://github.com/user/project2"
    ]
)

print(f"Rating: {result.overall_rating}/100")
print(f"Recommendation: {result.recommendation}")
```

### Path 2.2: With GitHub Username Only

```python
from agent2_candidate_evaluator import evaluate_candidate

result, toon = evaluate_candidate(
    jd_text="Python Developer. Required: Python, FastAPI...",
    github_username="username"
)

print(f"Rating: {result.overall_rating}/100")
print(f"Recommendation: {result.recommendation}")
```

**Output file:** `username_evaluation.toon`

---

## End-to-End Example

```python
from agent1_repo_to_jd import generate_jd_from_repo
from agent2_candidate_evaluator import evaluate_candidate

# 1. Company generates JD
jd, _ = generate_jd_from_repo("tiangolo/fastapi")

# 2. Create JD text
jd_text = f"{jd.job_title}\n"
jd_text += f"Required: {', '.join(jd.qualifications.must_have_skills)}"

# 3. Evaluate candidate
result, _ = evaluate_candidate(
    jd_text=jd_text,
    github_username="candidate_username"
)

# 4. Decision
if result.jd_fit_score >= 70:
    print(f"✅ Good fit! Score: {result.jd_fit_score}/100")
else:
    print(f"❌ Not a good fit. Score: {result.jd_fit_score}/100")
```

---

## File Locations

```
/Users/thiruanand/2025-hackaton/hackathon-2025/track_a_iron_man/src/github/
├── agent1_repo_to_jd.py              👈 Agent 1
├── agent2_candidate_evaluator.py     👈 Agent 2
├── test_simple.py                    👈 RUN THIS FIRST
└── README.md                         👈 Full docs
```

---

## What Each Agent Does

### Agent 1: Company Repo → JD
**Input:** Company GitHub repo
**Process:** Analyzes code, extracts tech stack
**Output:** Complete Job Description (TOON format)

### Agent 2: Candidate → Evaluation
**Input:** JD + (GitHub projects OR username)
**Process:**
- Path 2.1: Filter project links → Rate relevant ones
- Path 2.2: Get all repos → Filter by title → Rate relevant ones

**Output:** Evaluation with rating & recommendation (TOON format)

---

## Need Help?

1. Read: `README.md` - Full documentation
2. Read: `SUMMARY.md` - Complete overview
3. Run: `python test_simple.py` - See it work
4. Check: TOON output files generated

---

**Status:** ✅ Tested & Working
**Last Updated:** November 2025
