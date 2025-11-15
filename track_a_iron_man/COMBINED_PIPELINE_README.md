# Combined Pipeline: End-to-End Candidate Evaluation

This combined pipeline integrates Pipeline 1 (JD Generator) and Pipeline 2 (Candidate Evaluator) into a single, seamless workflow.

## Overview

The combined pipeline performs the following steps:

1. **Pipeline 1**: Generates a detailed Job Description by analyzing a company's GitHub repository
2. **Pipeline 2**: Evaluates a candidate's resume and GitHub profile against the generated JD
3. **Output**: Complete evaluation with reasoning, TOON format outputs, and a fit/no-fit decision

## Features

- **Testing Mode with Caching**: Avoid repeated API calls by caching GitHub data
- **Complete Reasoning**: Every decision includes detailed reasoning
- **TOON Format Output**: Both JD and evaluation are saved in TOON format
- **Comprehensive Analysis**: Includes resume analysis, GitHub code quality review, and skill gap analysis

## Installation

Ensure you have all dependencies installed:

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root with your credentials:

```
HOLISTIC_AI_TEAM_ID=your_team_id
HOLISTIC_AI_API_TOKEN=your_api_token
GITHUB_TOKEN=your_github_token
```

## Usage

### Basic Usage

```python
from combined_pipeline import combined_pipeline

# Run the combined pipeline
jd, jd_toon, evaluation, eval_toon = combined_pipeline(
    company_repo="fastapi/fastapi",
    job_title="Senior Python Backend Developer",
    resume_pdf_path="path/to/resume.pdf",
    salary_range="$140k-$180k",
    additional_requirements=[
        "Experience with microservices architecture",
        "Strong communication skills for remote work"
    ],
    verbose=True,
    testing=True  # Enable caching
)

# Access the results
print(f"Candidate: {evaluation.candidate_name}")
print(f"Fit: {'YES' if evaluation.final_decision.is_fit else 'NO'}")
print(f"Score: {evaluation.final_decision.overall_score}/100")
```

### Testing Mode (Recommended)

When `testing=True`, the pipeline caches all GitHub API calls to avoid rate limits and speed up subsequent runs:

```python
jd, jd_toon, evaluation, eval_toon = combined_pipeline(
    company_repo="fastapi/fastapi",
    job_title="Senior Python Backend Developer",
    resume_pdf_path="resume.pdf",
    testing=True  # Cache GitHub data
)
```

Cached data is stored in `./cache/github_data/`. Delete this directory to fetch fresh data.

### Command Line Usage

Run the example directly:

```bash
python combined_pipeline.py
```

Or use the test script:

```bash
python test_combined_pipeline.py
```

## Input Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `company_repo` | str | Yes | GitHub repository (e.g., "fastapi/fastapi") |
| `job_title` | str | Yes | Job title (e.g., "Senior Python Backend Developer") |
| `resume_pdf_path` | str | Yes | Path to candidate's resume PDF |
| `salary_range` | str | No | Salary range (e.g., "$140k-$180k") |
| `additional_requirements` | List[str] | No | Additional JD requirements |
| `verbose` | bool | No | Print detailed output (default: True) |
| `testing` | bool | No | Enable caching mode (default: False) |

## Output

The pipeline returns a tuple of 4 items:

1. **JobDescription**: Pydantic model with complete JD
2. **jd_toon**: JD in TOON format (string)
3. **CandidateEvaluation**: Pydantic model with complete evaluation
4. **eval_toon**: Evaluation in TOON format (string)

### Output Files

Two TOON files are automatically created:

- `{company_repo}_jd.toon`: Job description
- `{candidate_name}_evaluation.toon`: Candidate evaluation

## Pipeline Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    COMBINED PIPELINE                        │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
        ┌────────────────────────────────────────┐
        │      STEP 1: JD Generation             │
        │  (Pipeline 1)                          │
        ├────────────────────────────────────────┤
        │  1. Fetch repo metadata                │
        │  2. Get file structure                 │
        │  3. Analyze code files                 │
        │  4. Generate JD with reasoning         │
        │  5. Output: JobDescription + TOON      │
        └────────────────────────────────────────┘
                             │
                             ▼
        ┌────────────────────────────────────────┐
        │    STEP 2: Candidate Evaluation        │
        │  (Pipeline 2)                          │
        ├────────────────────────────────────────┤
        │  1. Extract resume text                │
        │  2. Analyze resume vs JD               │
        │  3. Fetch GitHub profile               │
        │  4. Analyze GitHub projects            │
        │  5. Identify skill gaps                │
        │  6. Make fit/no-fit decision           │
        │  7. Output: Evaluation + TOON          │
        └────────────────────────────────────────┘
                             │
                             ▼
        ┌────────────────────────────────────────┐
        │         FINAL OUTPUT                   │
        ├────────────────────────────────────────┤
        │  • Complete Job Description            │
        │  • Complete Candidate Evaluation       │
        │  • Fit/No-Fit Decision                 │
        │  • Detailed Reasoning                  │
        │  • TOON Format Files                   │
        └────────────────────────────────────────┘
```

## Example Output

### Job Description (Pipeline 1)

```
Job Title: Senior Python Backend Developer
Repository: fastapi/fastapi
Salary: $140k-$180k

Technical Requirements:
  - Python [must-have]: Primary language used throughout codebase
  - FastAPI [must-have]: Core framework of the repository
  - Pydantic [must-have]: Used extensively for data validation

Experience: senior (5+ years)
Reason: Complex async patterns and advanced type hints require senior expertise
```

### Candidate Evaluation (Pipeline 2)

```
Candidate: John Doe
Position: Senior Python Backend Developer

FINAL DECISION: ✅ FIT
Overall Score: 85/100
Recommendation: HIRE
Confidence: 90%

Decision Reason:
Strong Python experience with FastAPI projects on GitHub. Resume shows
7 years of backend development. Minor gaps in testing practices but
overall excellent match for the role.

Score Breakdown:
  Resume Score: 85/100
  GitHub Score: 80/100
  Skill Match: 90/100
```

## Caching Details

### What Gets Cached?

**Pipeline 1 (JD Generator):**
- Repository metadata
- File structure
- Code file contents

**Pipeline 2 (Candidate Evaluator):**
- GitHub profile data
- Repository lists
- File structures
- Code file contents

### Cache Location

All cache files are stored in:
```
./cache/github_data/
```

### Cache File Naming

Files are named based on the data type and identifier:
```
{identifier}_{cache_type}.json
```

Examples:
- `fastapi_fastapi_metadata.json`
- `bel-learning_profile.json`
- `bel-learning_repositories.json`

### Managing Cache

**Clear all cache:**
```bash
rm -rf ./cache/github_data/
```

**Clear specific repository cache:**
```bash
rm ./cache/github_data/fastapi_fastapi_*
```

## Troubleshooting

### Issue: Environment variables not set

**Error:**
```
ValueError: HOLISTIC_AI_TEAM_ID and HOLISTIC_AI_API_TOKEN not set.
```

**Solution:**
Create a `.env` file with your credentials or modify the code to use OpenAI.

### Issue: GitHub rate limit exceeded

**Error:**
```
GitHub API rate limit exceeded
```

**Solution:**
1. Enable testing mode: `testing=True`
2. Set `GITHUB_TOKEN` in your `.env` file
3. Wait for rate limit to reset (usually 1 hour)

### Issue: Resume PDF not found

**Error:**
```
File not found: resume.pdf
```

**Solution:**
Provide the absolute path to the resume PDF file.

## Advanced Usage

### Custom Cache Directory

Modify the cache directory in both pipelines:

```python
# In pipeline1_jd_generator.py and pipeline2_candidate_evaluator.py
CACHE_DIR = Path("./my_custom_cache")
```

### Disable Verbose Output

```python
jd, jd_toon, evaluation, eval_toon = combined_pipeline(
    company_repo="fastapi/fastapi",
    job_title="Senior Python Backend Developer",
    resume_pdf_path="resume.pdf",
    verbose=False  # Suppress detailed output
)
```

### Access Detailed Fields

```python
# Job Description details
print(f"Languages: {[lang.name for lang in jd.technical_requirements.primary_languages]}")
print(f"Responsibilities: {len(jd.responsibilities)}")

# Evaluation details
print(f"Years of Experience: {evaluation.resume_analysis.years_of_experience}")
print(f"GitHub Username: {evaluation.github_analysis.github_username}")
print(f"Skill Gaps: {len(evaluation.skill_gaps)}")

# Detailed gaps
for gap in evaluation.skill_gaps:
    print(f"  - {gap.gap_name} [{gap.severity}]: {gap.description}")
```

## Files Created

After running the pipeline, you'll have:

1. **TOON Files:**
   - `{company_repo}_jd.toon`
   - `{candidate_name}_evaluation.toon`

2. **Cache Directory:**
   - `./cache/github_data/` (if testing mode enabled)

## Integration with Other Systems

The TOON format outputs can be easily integrated with other systems:

```python
import json

# Parse TOON output (it's base64 encoded JSON)
from toon import decode as toon_decode

# Decode TOON back to dict
jd_dict = toon_decode(jd_toon)
eval_dict = toon_decode(eval_toon)

# Send to API, database, etc.
```

## Performance Tips

1. **Use Testing Mode**: Dramatically reduces API calls
2. **Reuse JD**: Generate JD once, evaluate multiple candidates
3. **Batch Processing**: Evaluate multiple candidates sequentially with caching
4. **Monitor Rate Limits**: Use GitHub tokens to increase limits

## License

See main project LICENSE file.
