# Quick Start Guide - Combined Pipeline

## TL;DR

```python
from combined_pipeline import combined_pipeline

# Run end-to-end evaluation
jd, jd_toon, eval, eval_toon = combined_pipeline(
    company_repo="fastapi/fastapi",
    job_title="Senior Backend Developer",
    resume_pdf_path="resume.pdf",
    testing=True  # Enable caching
)

# Check result
print(f"Fit: {eval.final_decision.is_fit}")
print(f"Score: {eval.final_decision.overall_score}/100")
```

## What It Does

1. **Generates a Job Description** from a company's GitHub repository
2. **Evaluates a candidate** against that JD using their resume + GitHub
3. **Makes a fit/no-fit decision** with detailed reasoning
4. **Outputs TOON format** files for integration

## Setup (One Time)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create `.env` file:**
   ```
   HOLISTIC_AI_TEAM_ID=your_team_id
   HOLISTIC_AI_API_TOKEN=your_api_token
   GITHUB_TOKEN=your_github_token
   ```

## Run It

### Option 1: Command Line
```bash
python combined_pipeline.py
```

### Option 2: Test Script
```bash
python test_combined_pipeline.py
```

### Option 3: Import as Module
```python
from combined_pipeline import combined_pipeline

result = combined_pipeline(
    company_repo="your/repo",
    job_title="Your Title",
    resume_pdf_path="resume.pdf",
    testing=True
)
```

## Key Parameters

| Parameter | Required | Example |
|-----------|----------|---------|
| `company_repo` | Yes | `"fastapi/fastapi"` |
| `job_title` | Yes | `"Senior Backend Developer"` |
| `resume_pdf_path` | Yes | `"resume.pdf"` |
| `salary_range` | No | `"$140k-$180k"` |
| `testing` | No | `True` (enable caching) |

## Understanding the Output

### Job Description (Pipeline 1)
```python
jd.job_title                           # Job title
jd.technical_requirements              # Languages, frameworks, tools
jd.responsibilities                    # Key responsibilities
jd.qualifications                      # Required skills
jd.experience_requirement              # Experience level & years
```

### Candidate Evaluation (Pipeline 2)
```python
evaluation.candidate_name              # Candidate name
evaluation.final_decision.is_fit       # True/False
evaluation.final_decision.overall_score # Score out of 100
evaluation.final_decision.recommendation # hire/no-hire/maybe
evaluation.skill_gaps                  # List of gaps
evaluation.strengths                   # List of strengths
```

## Caching (Recommended)

Enable caching to avoid repeated API calls:

```python
combined_pipeline(..., testing=True)
```

- **First run:** Fetches data from GitHub (30-60 seconds)
- **Subsequent runs:** Uses cache (5-10 seconds)
- **Cache location:** `./cache/github_data/`

**Clear cache:**
```bash
rm -rf ./cache/github_data/
```

## Common Issues

### Missing credentials
```
ValueError: HOLISTIC_AI_TEAM_ID and HOLISTIC_AI_API_TOKEN not set
```
→ Create `.env` file with your credentials

### Resume not found
```
FileNotFoundError: resume.pdf
```
→ Use absolute path or ensure file exists

### GitHub rate limit
```
GitHub API rate limit exceeded
```
→ Enable testing mode (`testing=True`) and/or add `GITHUB_TOKEN` to `.env`

## Files Created

After running, you'll have:

1. `{company_repo}_jd.toon` - Job description
2. `{candidate_name}_evaluation.toon` - Evaluation
3. `./cache/github_data/` - Cached data (if testing=True)

## Examples

See `example_usage.py` for:
- Basic usage
- Multiple candidates
- Custom requirements
- Accessing detailed data
- Working with TOON format

## Next Steps

1. **Read full docs:** `COMBINED_PIPELINE_README.md`
2. **View examples:** `example_usage.py`
3. **Check summary:** `SUMMARY.md`

## Support

- Check `COMBINED_PIPELINE_README.md` for troubleshooting
- See `example_usage.py` for code examples
- Review `SUMMARY.md` for architecture details

---

## Quick Reference - Output Structure

```
CandidateEvaluation
├── candidate_name
├── job_title
├── resume_analysis
│   ├── years_of_experience
│   ├── education_match
│   ├── skill_matches []
│   └── resume_strength_score
├── github_analysis
│   ├── github_username
│   ├── has_github
│   ├── relevant_projects []
│   └── github_contribution_score
├── skill_gaps []
├── strengths []
└── final_decision
    ├── is_fit
    ├── overall_score
    ├── resume_score
    ├── github_score
    ├── skill_match_score
    ├── recommendation
    ├── confidence_level
    └── fit_reason
```

---

**Ready to evaluate candidates? Run `python combined_pipeline.py`**
