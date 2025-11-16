"""
PIPELINE 2: Complete Candidate Evaluator
Input: Resume PDF + Job Description
Output: Full evaluation with GitHub analysis + Fit/No-Fit decision with detailed reasons

Every decision includes a 'reason' field explaining why.
"""

import sys
import json
import uuid
import os
from pathlib import Path
from typing import List, Optional, Dict, Union, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from dotenv import load_dotenv

# Import TOON encoder
from toon import encode as toon_encode

# Import LangChain components
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

# Import resume extractor
from pdf_extractor import extract_pdf

# Import GitHub client
from src.github.github_client import GitHubClient

# Load environment variables
env_path = Path('.env')
if env_path.exists():
    load_dotenv(env_path)

# Import Holistic AI Bedrock helper
sys.path.insert(0, './core')
from react_agent.holistic_ai_bedrock import get_chat_model

# Import observability
from observability import (
    StepType, StepStatus, StepData, PipelineExecution, StepTracker
)


# ============================================
# Enhanced Schema with Reason Fields
# ============================================

class SkillMatch(BaseModel):
    """Skill matching with reasoning"""
    model_config = ConfigDict(populate_by_name=True)

    skill_name: str = Field(default="Unknown", description="Skill from JD", alias="skill")
    has_skill: bool = Field(default=True, description="Does candidate have this skill")
    evidence: str = Field(default="", description="Where in resume/GitHub this skill is demonstrated")
    proficiency_score: int = Field(default=5, description="Proficiency level 1-10", alias="proficiency")
    reason: str = Field(default="Based on resume analysis", description="Why this score was given")


class ResumeAnalysis(BaseModel):
    """Resume analysis with reasoning"""
    years_of_experience: int = Field(default=0, description="Total years of experience")
    years_reason: str = Field(default="Calculated from work history", description="How years were calculated")

    education_match: bool = Field(default=True, description="Education meets requirements")
    education_reason: str = Field(default="Education information analyzed", description="Why education matches or not")

    skill_matches: List[SkillMatch] = Field(default_factory=list, description="Detailed skill matching")

    relevant_experience: List[str] = Field(default_factory=list, description="Relevant work experiences")
    relevant_experience_reason: str = Field(default="Based on work history", description="Why these experiences are relevant")

    resume_strength_score: int = Field(default=50, description="Resume strength 1-100")
    resume_strength_reason: str = Field(default="Based on overall resume quality", description="Why this score")

    @field_validator('skill_matches', mode='before')
    @classmethod
    def convert_skill_matches_dict(cls, v):
        """Convert dict skill matches to list format if needed"""
        if isinstance(v, dict):
            # Convert dict like {'python': True, 'fastapi_django': False} to list
            result = []
            for skill_name, has_skill in v.items():
                result.append({
                    'skill': skill_name.replace('_', ' ').title(),
                    'has_skill': has_skill,
                    'proficiency': 7 if has_skill else 3,
                    'evidence': 'Based on resume analysis',
                    'reason': 'Skill identified in resume' if has_skill else 'Skill not found in resume'
                })
            return result
        return v


class GitHubProjectRelevance(BaseModel):
    """GitHub project relevance with reasoning"""
    model_config = ConfigDict(populate_by_name=True)

    project_name: str = Field(default="Unknown", description="Project name", alias="name")
    github_url: str = Field(default="", description="GitHub URL", alias="url")
    is_relevant: bool = Field(default=True, description="Is relevant to JD")
    relevance_score: int = Field(default=5, description="Relevance score 1-10")
    relevance_reason: str = Field(default="Relevant to job requirements", description="Why relevant or not")
    technologies_matched: List[str] = Field(default_factory=list, description="Technologies that match JD", alias="technologies")


class GitHubCodeQuality(BaseModel):
    """Code quality assessment with reasoning"""
    project_name: str = Field(default="Unknown", description="Project name")
    code_quality_score: int = Field(default=5, description="Code quality 1-10")
    code_quality_reason: str = Field(default="Code quality assessment", description="Why this quality score")

    technical_depth_score: int = Field(default=5, description="Technical depth 1-10")
    technical_depth_reason: str = Field(default="Technical depth assessment", description="Why this depth score")

    best_practices_score: int = Field(default=5, description="Best practices 1-10")
    best_practices_reason: str = Field(default="Best practices assessment", description="Why this practices score")

    files_analyzed: List[str] = Field(default_factory=list, description="Files analyzed (2-3 max)")
    key_strengths: List[str] = Field(default_factory=list, description="Key strengths found")
    key_weaknesses: List[str] = Field(default_factory=list, description="Areas to improve")


class GitHubAnalysis(BaseModel):
    """Complete GitHub analysis"""
    github_username: Optional[str] = Field(default=None, description="GitHub username")
    has_github: bool = Field(default=False, description="Does candidate have GitHub")
    github_check_reason: str = Field(default="GitHub profile checked", description="How GitHub was identified")

    projects_found: int = Field(default=0, description="Total projects found")
    projects_found_reason: str = Field(default="GitHub profile analyzed", description="How projects were found")

    relevant_projects: List[GitHubProjectRelevance] = Field(default_factory=list, description="Relevant projects")
    quality_assessments: List[GitHubCodeQuality] = Field(default_factory=list, description="Quality assessments")

    github_contribution_score: int = Field(default=0, description="GitHub activity score 1-100")
    github_score_reason: str = Field(default="Based on GitHub activity", description="Why this GitHub score")

    @field_validator('relevant_projects', mode='before')
    @classmethod
    def convert_relevant_projects_strings(cls, v):
        """Convert string project names to GitHubProjectRelevance objects"""
        if isinstance(v, list) and v:
            result = []
            for item in v:
                if isinstance(item, str):
                    # Convert string to object
                    result.append({
                        'project_name': item,
                        'github_url': f'https://github.com/{item}',
                        'is_relevant': True,
                        'relevance_score': 7,
                        'relevance_reason': 'Identified as relevant project',
                        'technologies_matched': []
                    })
                elif isinstance(item, dict):
                    # Create a normalized dict with all required fields
                    normalized = {}

                    # Handle project_name / name
                    normalized['project_name'] = item.get('project_name', item.get('name', 'Unknown Project'))

                    # Handle github_url / url
                    normalized['github_url'] = item.get('github_url', item.get('url', f"https://github.com/{normalized['project_name']}"))

                    # Handle technologies_matched / technologies
                    normalized['technologies_matched'] = item.get('technologies_matched', item.get('technologies', []))

                    # Set defaults for other required fields
                    normalized['is_relevant'] = item.get('is_relevant', True)
                    normalized['relevance_score'] = item.get('relevance_score', 7)
                    normalized['relevance_reason'] = item.get('relevance_reason', 'Relevant to job requirements')

                    result.append(normalized)
                else:
                    result.append(item)
            return result
        return v


class ExperienceGapAnalysis(BaseModel):
    """Gap analysis with detailed reasons"""
    model_config = ConfigDict(populate_by_name=True)

    gap_name: str = Field(default="Unknown gap", description="Name of the gap", alias="name")
    severity: str = Field(default="moderate", description="critical, moderate, or minor")
    description: str = Field(default="Gap identified", description="Description of the gap", alias="details")
    reason: str = Field(default="Based on requirement analysis", description="Why this is a gap and its severity")
    can_be_learned: bool = Field(default=True, description="Can this gap be filled with training")
    learning_reason: str = Field(default="Can be learned with training", description="Why it can or cannot be learned")


class FinalDecision(BaseModel):
    """Final hiring decision with comprehensive reasoning"""
    is_fit: bool = Field(default=False, description="Is candidate a fit for the role")
    fit_reason: str = Field(default="Decision analysis", description="Comprehensive reason for fit/no-fit decision")

    overall_score: int = Field(default=50, description="Overall candidate score 1-100")
    overall_score_breakdown: str = Field(default="Score calculated from resume, GitHub, and skills", description="How overall score was calculated")

    resume_score: int = Field(default=50, description="Resume contribution to score 1-100")
    github_score: int = Field(default=50, description="GitHub contribution to score 1-100")
    skill_match_score: int = Field(default=50, description="Skill matching score 1-100")

    recommendation: str = Field(default="maybe", description="strong-hire, hire, maybe, no-hire")
    recommendation_reason: str = Field(default="Based on overall assessment", description="Why this recommendation level")

    confidence_level: int = Field(default=50, description="Confidence in decision 1-100")
    confidence_reason: str = Field(default="Confidence based on available information", description="Why this confidence level")


class CandidateEvaluation(BaseModel):
    """Complete candidate evaluation with all reasoning"""
    candidate_name: str = Field(default="Unknown", description="Candidate name")
    job_title: str = Field(default="Unknown", description="Job title from JD")

    resume_analysis: Optional[ResumeAnalysis] = Field(default=None, description="Resume analysis")
    github_analysis: Optional[GitHubAnalysis] = Field(default=None, description="GitHub analysis")

    skill_gaps: List[ExperienceGapAnalysis] = Field(default_factory=list, description="Identified gaps")
    skill_gaps_summary: str = Field(default="", description="Overall gaps summary with reasoning")

    strengths: List[str] = Field(default_factory=list, description="Top 5 candidate strengths")
    strengths_reason: str = Field(default="", description="Why these are the top strengths")

    final_decision: Optional[FinalDecision] = Field(default=None, description="Final hiring decision")

    detailed_feedback: str = Field(default="", description="Detailed feedback for candidate (2-3 paragraphs)")
    hiring_manager_notes: str = Field(default="", description="Notes for hiring manager (2-3 paragraphs)")

    @field_validator('skill_gaps', mode='before')
    @classmethod
    def convert_skill_gaps_strings(cls, v):
        """Convert list of strings to ExperienceGapAnalysis objects"""
        if isinstance(v, list) and v:
            result = []
            for item in v:
                if isinstance(item, str):
                    # Parse severity from string if possible
                    severity = 'moderate'
                    if any(word in item.lower() for word in ['critical', 'major', 'important']):
                        severity = 'critical'
                    elif any(word in item.lower() for word in ['minor', 'small', 'slight']):
                        severity = 'minor'

                    result.append({
                        'name': item,
                        'severity': severity,
                        'details': item,
                        'reason': f'Gap identified: {item}',
                        'can_be_learned': True,
                        'learning_reason': 'Can be acquired through training and practice'
                    })
                elif isinstance(item, dict):
                    # Handle dict that might have different field names
                    if 'gap_name' not in item and 'name' not in item:
                        # Try to extract from other fields
                        item['name'] = item.get('description', 'Unspecified gap')
                    result.append(item)
                else:
                    result.append(item)
            return result
        return v

    @field_validator('final_decision', mode='before')
    @classmethod
    def convert_final_decision_string(cls, v):
        """Convert string final decision to FinalDecision object"""
        if isinstance(v, str):
            # Extract decision from string
            is_fit = not any(word in v.lower() for word in ['not', 'no', 'reject', 'fail'])
            return {
                'is_fit': is_fit,
                'fit_reason': v,
                'overall_score': 70 if is_fit else 30,
                'overall_score_breakdown': 'Based on overall evaluation',
                'resume_score': 50,
                'github_score': 50,
                'skill_match_score': 50,
                'recommendation': 'hire' if is_fit else 'no-hire',
                'recommendation_reason': v,
                'confidence_level': 70,
                'confidence_reason': 'Based on available information'
            }
        elif isinstance(v, dict):
            # Handle dict that might have different field names
            normalized = {}

            # Handle decision -> is_fit
            if 'decision' in v and 'is_fit' not in v:
                decision = v.get('decision', '').lower()
                normalized['is_fit'] = decision not in ['reject', 'no', 'fail', 'not fit', 'no-hire']
            else:
                normalized['is_fit'] = v.get('is_fit', False)

            # Handle reason -> fit_reason
            normalized['fit_reason'] = v.get('fit_reason', v.get('reason', 'Decision based on evaluation'))

            # Handle scores
            normalized['overall_score'] = v.get('overall_score', 70 if normalized['is_fit'] else 30)
            normalized['overall_score_breakdown'] = v.get('overall_score_breakdown', 'Based on overall evaluation')
            normalized['resume_score'] = v.get('resume_score', 50)
            normalized['github_score'] = v.get('github_score', 50)
            normalized['skill_match_score'] = v.get('skill_match_score', 50)

            # Handle recommendation
            if 'recommendation' not in v:
                normalized['recommendation'] = 'hire' if normalized['is_fit'] else 'no-hire'
            else:
                normalized['recommendation'] = v.get('recommendation')

            normalized['recommendation_reason'] = v.get('recommendation_reason', normalized['fit_reason'])

            # Handle confidence
            normalized['confidence_level'] = v.get('confidence_level', 70)
            normalized['confidence_reason'] = v.get('confidence_reason', 'Based on available information')

            return normalized
        return v


# ============================================
# Cache Management for Testing
# ============================================

CACHE_DIR = Path("./cache/github_data")
TESTING_MODE = False  # Set to True to enable caching

def get_cache_path(identifier: str, cache_type: str) -> Path:
    """Get cache file path for an identifier and cache type."""
    safe_identifier = identifier.replace('/', '_').replace(' ', '_')
    return CACHE_DIR / f"{safe_identifier}_{cache_type}.json"

def load_from_cache(identifier: str, cache_type: str) -> Optional[dict]:
    """Load cached data if it exists."""
    if not TESTING_MODE:
        return None

    cache_path = get_cache_path(identifier, cache_type)
    if cache_path.exists():
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load cache from {cache_path}: {e}")
    return None

def save_to_cache(identifier: str, cache_type: str, data: dict) -> None:
    """Save data to cache."""
    if not TESTING_MODE:
        return

    cache_path = get_cache_path(identifier, cache_type)
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"💾 Cached {cache_type} data to {cache_path}")
    except Exception as e:
        print(f"Warning: Failed to save cache to {cache_path}: {e}")

# ============================================
# Tools
# ============================================

@tool
def extract_resume(pdf_path: str) -> str:
    """Extract full text from resume PDF.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Full resume text
    """
    try:
        return extract_pdf(pdf_path)
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_github_profile(username: str) -> dict:
    """Get GitHub profile information.

    Args:
        username: GitHub username

    Returns:
        Profile info
    """
    # Check cache first
    cached_data = load_from_cache(username, "profile")
    if cached_data is not None:
        print(f"📦 Using cached profile for {username}")
        return cached_data

    try:
        client = GitHubClient()
        profile = client.get_profile_info(username)

        # Save to cache
        save_to_cache(username, "profile", profile)

        return profile
    except Exception as e:
        return {"error": str(e)}


@tool
def get_github_repositories(username: str) -> dict:
    """Get all repositories for a GitHub user.

    Args:
        username: GitHub username

    Returns:
        List of repositories
    """
    # Check cache first
    cached_data = load_from_cache(username, "repositories")
    if cached_data is not None:
        print(f"📦 Using cached repositories for {username}")
        return cached_data

    try:
        client = GitHubClient()
        repos = client.get_public_repositories(username)
        result = {'username': username, 'repositories': repos, 'total': len(repos)}

        # Save to cache
        save_to_cache(username, "repositories", result)

        return result
    except Exception as e:
        return {"error": str(e)}


@tool
def get_repo_file_structure(repo_full_name: str) -> dict:
    """Get repository file structure.

    Args:
        repo_full_name: Full repository name

    Returns:
        File structure
    """
    # Check cache first
    cached_data = load_from_cache(repo_full_name, "file_structure")
    if cached_data is not None:
        print(f"📦 Using cached file structure for {repo_full_name}")
        return cached_data

    try:
        client = GitHubClient()
        repo = client.github.get_repo(repo_full_name)
        tree = repo.get_git_tree(repo.default_branch, recursive=True)

        files = {'code_files': [], 'config_files': [], 'doc_files': []}

        for item in tree.tree:
            if item.type == "blob":
                path = item.path
                if any(path.endswith(ext) for ext in ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs']):
                    files['code_files'].append(path)
                elif path.endswith(('.json', '.yaml', '.yml')):
                    files['config_files'].append(path)
                elif path.endswith(('.md', '.txt')):
                    files['doc_files'].append(path)

        result = {'repo': repo_full_name, 'files': files, 'total_code_files': len(files['code_files'])}

        # Save to cache
        save_to_cache(repo_full_name, "file_structure", result)

        return result
    except Exception as e:
        return {"error": str(e)}


@tool
def fetch_code_files(repo_full_name: str, file_paths: List[str]) -> dict:
    """Fetch specific code files (max 3).

    Args:
        repo_full_name: Full repository name
        file_paths: List of file paths

    Returns:
        File contents
    """
    # Create a cache key based on the file paths
    cache_key = "_".join(sorted(file_paths[:3])).replace('/', '_')[:100]  # Limit length
    cache_type = f"files_{cache_key}"

    # Check cache first
    cached_data = load_from_cache(repo_full_name, cache_type)
    if cached_data is not None:
        print(f"📦 Using cached file contents for {repo_full_name}")
        return cached_data

    try:
        client = GitHubClient()
        repo = client.github.get_repo(repo_full_name)
        default_branch = repo.default_branch

        files_content = []
        for file_path in file_paths[:3]:
            try:
                raw_url = f"https://raw.githubusercontent.com/{repo_full_name}/{default_branch}/{file_path}"
                import requests
                response = requests.get(raw_url, timeout=10)
                if response.status_code == 200:
                    files_content.append({'path': file_path, 'content': response.text[:5000]})
            except:
                continue

        result = {'files': files_content, 'total_fetched': len(files_content)}

        # Save to cache
        save_to_cache(repo_full_name, cache_type, result)

        return result
    except Exception as e:
        return {"error": str(e)}


# ============================================
# Helper Functions
# ============================================

def get_langsmith_url(run_id: str, project_name: str) -> Optional[str]:
    """Generate LangSmith URL for a run."""
    try:
        if os.getenv('LANGSMITH_API_KEY') and os.getenv('LANGSMITH_TRACING') == 'true':
            return f"https://smith.langchain.com/o/projects/p/{project_name}/r/{run_id}"
    except:
        pass
    return None


# ============================================
# Main Pipeline 2 Function
# ============================================

def evaluate_candidate(
    resume_pdf_path: str,
    jd_text: str,
    jd_job_title: str,
    verbose: bool = True,
    testing: bool = False,
    enable_observability: bool = True
):
    """PIPELINE 2: Complete candidate evaluation with resume + GitHub analysis.

    Args:
        resume_pdf_path: Path to candidate's resume PDF
        jd_text: Job description text (from Pipeline 1 or custom)
        jd_job_title: Job title from JD
        verbose: Print details
        testing: Enable caching mode - fetches GitHub data once and reuses for subsequent runs
        enable_observability: Enable execution tracking and logging

    Returns:
        Tuple of (CandidateEvaluation, toon_output, execution)
    """
    # Set global testing mode
    global TESTING_MODE
    TESTING_MODE = testing

    # Initialize observability
    execution_id = str(uuid.uuid4())
    execution = None
    tracker = None

    if enable_observability:
        from datetime import datetime
        execution = PipelineExecution(
            execution_id=execution_id,
            pipeline_name="pipeline2_candidate_evaluator",
            repository_type="local",  # Using 'local' for resume files
            repository_path=resume_pdf_path,
            job_title=jd_job_title,
            start_time=datetime.now()
        )
        tracker = StepTracker(execution)

    if verbose:
        print("\n" + "="*80)
        print("🎯 PIPELINE 2: Complete Candidate Evaluator")
        print("="*80)
        print(f"📄 Resume: {resume_pdf_path}")
        print(f"💼 Job Title: {jd_job_title}")
        if testing:
            print(f"🧪 Testing Mode: ENABLED (caching GitHub data)")
        if enable_observability:
            print(f"🔍 Execution ID: {execution_id}")
        print()

    try:
        # STEP 1: Initialize LLM and Agent
        if tracker:
            with tracker.track_step(
                StepType.INITIALIZATION,
                "Initialize LLM and Agent",
                input_data={"model": "claude-3-5-sonnet"},
                reason="Create agent with resume and GitHub analysis tools"
            ):
                llm = get_chat_model("claude-3-5-sonnet")
                agent = create_react_agent(
                    llm,
                    tools=[extract_resume, get_github_profile, get_github_repositories,
                           get_repo_file_structure, fetch_code_files],
                    response_format=CandidateEvaluation
                )
                tracker.update_output({
                    "tools_loaded": ["extract_resume", "get_github_profile", "get_github_repositories",
                                   "get_repo_file_structure", "fetch_code_files"],
                    "tool_count": 5,
                    "response_format": "CandidateEvaluation"
                })
        else:
            llm = get_chat_model("claude-3-5-sonnet")
            agent = create_react_agent(
                llm,
                tools=[extract_resume, get_github_profile, get_github_repositories,
                       get_repo_file_structure, fetch_code_files],
                response_format=CandidateEvaluation
            )

        # Prompt
        prompt = f"""Evaluate candidate completely against Job Description.

JOB DESCRIPTION:
{jd_text}

JOB TITLE: {jd_job_title}

RESUME PDF: {resume_pdf_path}

EVALUATION PROCESS (ALL WITH REASONS):

STEP 1: RESUME ANALYSIS
- Use extract_resume to get full resume text
- Extract: name, years of experience, education, skills, work history
- For EACH field, provide a 'reason' explaining your analysis

resume_analysis:
  years_of_experience: INTEGER
  years_reason: STRING - How you calculated this

  education_match: BOOLEAN
  education_reason: STRING - Why education matches or not

  skill_matches: LIST of objects
    Each: {{skill_name: STRING, has_skill: BOOLEAN, evidence: STRING,
           proficiency_score: 1-10, reason: STRING}}
    Match EVERY skill from JD

  relevant_experience: LIST of relevant work experiences
  relevant_experience_reason: STRING - Why these are relevant

  resume_strength_score: INTEGER 1-100
  resume_strength_reason: STRING - Why this score

STEP 2: GITHUB ANALYSIS
- Check if resume has GitHub username or project links
- If GitHub username found:
  - Use get_github_profile
  - Use get_github_repositories
  - Filter repos by relevance to JD (by title and description)
  - For TOP 2-3 relevant repos:
    - Use get_repo_file_structure
    - Select 2-3 most relevant code files
    - Use fetch_code_files
    - Analyze code quality

github_analysis:
  github_username: STRING or None
  has_github: BOOLEAN
  github_check_reason: STRING - How GitHub was found/not found

  projects_found: INTEGER
  projects_found_reason: STRING - How projects were discovered

  relevant_projects: LIST of objects
    Each: {{project_name, github_url, is_relevant: BOOLEAN,
           relevance_score: 1-10, relevance_reason: STRING,
           technologies_matched: LIST}}

  quality_assessments: LIST (only for relevant projects)
    Each: {{project_name, code_quality_score: 1-10, code_quality_reason: STRING,
           technical_depth_score: 1-10, technical_depth_reason: STRING,
           best_practices_score: 1-10, best_practices_reason: STRING,
           files_analyzed: LIST, key_strengths: LIST, key_weaknesses: LIST}}

  github_contribution_score: INTEGER 1-100
  github_score_reason: STRING - Why this score

STEP 3: GAP ANALYSIS
- Identify ALL gaps between candidate and JD requirements
- For EACH gap:

skill_gaps: LIST of objects
  Each: {{gap_name: STRING, severity: "critical"|"moderate"|"minor",
         description: STRING, reason: STRING,
         can_be_learned: BOOLEAN, learning_reason: STRING}}

skill_gaps_summary: STRING - Overall summary of gaps

STEP 4: STRENGTHS
strengths: LIST of top 5 strengths
strengths_reason: STRING - Why these are the top strengths

STEP 5: FINAL DECISION (MOST IMPORTANT)
final_decision:
  is_fit: BOOLEAN - True if candidate is fit, False if not
  fit_reason: STRING - COMPREHENSIVE reason for decision (must reference resume + GitHub + gaps)

  overall_score: INTEGER 1-100
  overall_score_breakdown: STRING - Explain calculation (resume + GitHub + skills)

  resume_score: INTEGER 1-100
  github_score: INTEGER 1-100
  skill_match_score: INTEGER 1-100

  recommendation: STRING - "strong-hire"|"hire"|"maybe"|"no-hire"
  recommendation_reason: STRING - Why this level

  confidence_level: INTEGER 1-100
  confidence_reason: STRING - Why this confidence

detailed_feedback: STRING - 2-3 paragraphs for candidate

hiring_manager_notes: STRING - 2-3 paragraphs for hiring manager

CRITICAL RULES:
1. EVERY decision needs a 'reason' field
2. If candidate is NOT FIT, explain EXACTLY WHY in fit_reason
3. List ALL gaps, even minor ones
4. Be objective - don't inflate or deflate scores
5. Base GitHub analysis on ACTUAL CODE, not just descriptions
6. Analyze max 2-3 projects, 2-3 files per project
7. If no GitHub, explain impact on decision

Return complete evaluation with all reasoning."""

        # STEP 2: Agent Evaluation with LangSmith tracing
        try:
            from langsmith import uuid7
            run_id = str(uuid7())
        except ImportError:
            run_id = str(uuid.uuid4())

        if tracker:
            execution.langsmith_run_id = run_id
            langsmith_project = "Synapse-Pipeline2"
            execution.langsmith_project = langsmith_project

            with tracker.track_step(
                StepType.AGENT_REASONING,
                "Agent Candidate Evaluation",
                input_data={
                    "job_title": jd_job_title,
                    "resume_path": resume_pdf_path,
                    "prompt_length": len(prompt)
                },
                reason="Agent evaluates resume and GitHub projects against job requirements"
            ):
                if verbose:
                    print("🤖 Analyzing resume and GitHub projects...\n")

                result = agent.invoke(
                    {"messages": [HumanMessage(content=prompt)]},
                    {"run_id": run_id, "project_name": langsmith_project, "tags": ["candidate-evaluation", "resume-analysis"]}
                )

                data = result['structured_response']

                # Count tokens using tiktoken
                try:
                    import tiktoken
                    encoding = tiktoken.encoding_for_model('gpt-4')

                    def count_tokens(text: str) -> int:
                        return len(encoding.encode(str(text)))

                    input_tokens = count_tokens(prompt)
                    output_tokens = 0
                    if 'messages' in result:
                        for msg in result['messages']:
                            if hasattr(msg, 'content') and msg.content:
                                output_tokens += count_tokens(msg.content)
                            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                output_tokens += count_tokens(str(msg.tool_calls))

                    tokens_used = input_tokens + output_tokens
                    input_cost = (input_tokens / 1_000_000) * 3.0
                    output_cost = (output_tokens / 1_000_000) * 15.0
                    cost_usd = input_cost + output_cost
                except ImportError:
                    tokens_used = 0
                    cost_usd = 0.0

                # Get LangSmith URL
                langsmith_url = get_langsmith_url(run_id, langsmith_project)
                if langsmith_url:
                    execution.langsmith_url = langsmith_url

                tracker.update_metrics(
                    tokens=tokens_used if tokens_used > 0 else None,
                    cost=cost_usd if cost_usd > 0 else None
                )
                tracker.update_output({
                    "evaluation_generated": True,
                    "is_fit": data.final_decision.is_fit if data.final_decision else False,
                    "overall_score": data.final_decision.overall_score if data.final_decision else 0,
                    "recommendation": data.final_decision.recommendation if data.final_decision else "unknown",
                    "langsmith_run_id": run_id,
                    "tokens_used": tokens_used,
                    "cost_usd": round(cost_usd, 4) if cost_usd > 0 else 0
                })
        else:
            if verbose:
                print("🤖 Analyzing resume and GitHub projects...\n")

            result = agent.invoke({
                "messages": [HumanMessage(content=prompt)]
            })
            data = result['structured_response']

        # STEP 3: Convert to TOON
        if tracker:
            with tracker.track_step(
                StepType.OUTPUT_GENERATION,
                "Generate TOON Output",
                input_data={"output_format": "TOON"},
                reason="Convert evaluation to TOON format for storage"
            ):
                output_toon = toon_encode(data.model_dump())
                tracker.update_output({
                    "encoding": "TOON",
                    "size_bytes": len(output_toon)
                })
        else:
            output_toon = toon_encode(data.model_dump())

        if verbose:
            print("="*80)
            print("✅ EVALUATION COMPLETE")
            print("="*80)

        print(f"\n👤 Candidate: {data.candidate_name}")
        print(f"💼 Position: {data.job_title}")

        # Final Decision First (Most Important)
        print(f"\n\n{'='*80}")
        print("🎯 FINAL DECISION")
        print(f"{'='*80}")

        if data.final_decision:
            fit_status = "✅ FIT" if data.final_decision.is_fit else "❌ NOT FIT"
            print(f"\n{fit_status}")
            print(f"Overall Score: {data.final_decision.overall_score}/100")
            print(f"Recommendation: {data.final_decision.recommendation.upper()}")
            print(f"Confidence: {data.final_decision.confidence_level}%")

            print(f"\n💡 Decision Reason:")
            print(f"   {data.final_decision.fit_reason}")

            print(f"\n📊 Score Breakdown:")
            print(f"   {data.final_decision.overall_score_breakdown}")

            print(f"\n   Resume Score: {data.final_decision.resume_score}/100")
            print(f"   GitHub Score: {data.final_decision.github_score}/100")
            print(f"   Skill Match: {data.final_decision.skill_match_score}/100")

            print(f"\n💡 Recommendation Reason:")
            print(f"   {data.final_decision.recommendation_reason}")

            print(f"\n💡 Confidence Reason:")
            print(f"   {data.final_decision.confidence_reason}")
        else:
            print(f"\nFinal decision not completed - partial evaluation only")

        # Resume Analysis
        print(f"\n\n📄 RESUME ANALYSIS:")
        print("-"*80)
        if data.resume_analysis:
            print(f"Years of Experience: {data.resume_analysis.years_of_experience}")
            print(f"💡 {data.resume_analysis.years_reason}")

            print(f"\nEducation Match: {'✓' if data.resume_analysis.education_match else '✗'}")
            print(f"💡 {data.resume_analysis.education_reason}")

            print(f"\nResume Strength: {data.resume_analysis.resume_strength_score}/100")
            print(f"💡 {data.resume_analysis.resume_strength_reason}")

            # Skill Matches
            print(f"\n\n🎯 SKILL MATCHING:")
            print("-"*80)
            for skill in data.resume_analysis.skill_matches:
                status = "✓" if skill.has_skill else "✗"
                print(f"\n{status} {skill.skill_name} - Proficiency: {skill.proficiency_score}/10")
                print(f"   Evidence: {skill.evidence}")
                print(f"   💡 {skill.reason}")
        else:
            print(f"Resume analysis not completed")

        # GitHub Analysis
        print(f"\n\n💻 GITHUB ANALYSIS:")
        print("-"*80)
        if data.github_analysis and data.github_analysis.has_github:
            print(f"Username: {data.github_analysis.github_username}")
            print(f"Projects Found: {data.github_analysis.projects_found}")
            print(f"💡 {data.github_analysis.github_check_reason}")
            print(f"💡 {data.github_analysis.projects_found_reason}")

            print(f"\nRelevant Projects:")
            for proj in data.github_analysis.relevant_projects:
                status = "✓" if proj.is_relevant else "✗"
                print(f"\n{status} {proj.project_name} ({proj.relevance_score}/10)")
                print(f"   {proj.github_url}")
                print(f"   💡 {proj.relevance_reason}")
                if proj.technologies_matched:
                    print(f"   Technologies: {', '.join(proj.technologies_matched)}")

            if data.github_analysis.quality_assessments:
                print(f"\nCode Quality Assessments:")
                for qual in data.github_analysis.quality_assessments:
                    print(f"\n📦 {qual.project_name}")
                    print(f"   Code Quality: {qual.code_quality_score}/10")
                    print(f"   💡 {qual.code_quality_reason}")
                    print(f"   Technical Depth: {qual.technical_depth_score}/10")
                    print(f"   💡 {qual.technical_depth_reason}")
                    print(f"   Best Practices: {qual.best_practices_score}/10")
                    print(f"   💡 {qual.best_practices_reason}")
                    print(f"   Files: {', '.join(qual.files_analyzed)}")

            print(f"\nGitHub Score: {data.github_analysis.github_contribution_score}/100")
            print(f"💡 {data.github_analysis.github_score_reason}")
        elif data.github_analysis:
            print(f"No GitHub found")
            print(f"💡 {data.github_analysis.github_check_reason}")
        else:
            print(f"GitHub analysis not completed")

        # Gaps
        if data.skill_gaps:
            print(f"\n\n⚠️  SKILL/EXPERIENCE GAPS:")
            print("-"*80)
            for gap in data.skill_gaps:
                severity_icon = "🔴" if gap.severity == "critical" else "🟡" if gap.severity == "moderate" else "🟢"
                print(f"\n{severity_icon} {gap.gap_name} [{gap.severity.upper()}]")
                print(f"   {gap.description}")
                print(f"   💡 {gap.reason}")
                print(f"   Can be learned: {'Yes' if gap.can_be_learned else 'No'}")
                print(f"   💡 {gap.learning_reason}")

            print(f"\n💡 Gaps Summary:")
            print(f"   {data.skill_gaps_summary}")

        # Strengths
        print(f"\n\n💪 TOP STRENGTHS:")
        print("-"*80)
        for i, strength in enumerate(data.strengths, 1):
            print(f"{i}. {strength}")
        print(f"\n💡 {data.strengths_reason}")

        # Feedback
        print(f"\n\n📝 DETAILED FEEDBACK:")
        print("-"*80)
        print(data.detailed_feedback)

        print(f"\n\n📋 HIRING MANAGER NOTES:")
        print("-"*80)
        print(data.hiring_manager_notes)

        # Save TOON
        output_file = f"{data.candidate_name.replace(' ', '_')}_evaluation.toon"
        with open(output_file, 'w') as f:
            f.write(output_toon)

        if verbose:
            print("\n" + "="*80)
            print("💾 SAVED OUTPUT")
            print("="*80)
            print(f"✅ TOON: {output_file}")
            print(f"   Size: {len(output_toon)} characters")
            if enable_observability and execution:
                print(f"\n📊 Execution Logs:")
                print(f"   Detailed: execution_logs/{execution_id}.json")
                print(f"   Frontend: execution_logs/{execution_id}_frontend.json")
                if execution.langsmith_url:
                    print(f"\n🔍 LangSmith Trace: {execution.langsmith_url}")

    except Exception as e:
        if tracker:
            tracker.finalize(success=False)
        if verbose:
            print(f"\n❌ Error: {str(e)}")
        raise
    finally:
        # Finalize execution tracking
        if enable_observability and tracker:
            tracker.finalize()

            # Save execution logs
            log_dir = Path("execution_logs")
            log_dir.mkdir(exist_ok=True)

            log_file = log_dir / f"{execution_id}.json"
            with open(log_file, 'w') as f:
                json.dump(execution.model_dump(), f, indent=2, default=str)

            frontend_log_file = log_dir / f"{execution_id}_frontend.json"
            with open(frontend_log_file, 'w') as f:
                json.dump(execution.to_frontend_json(), f, indent=2)

    return data, output_toon, execution


# ============================================
# Main
# ============================================

if __name__ == "__main__":
    # Example JD text
    jd_text = """
    Senior Python Backend Developer

    Required Skills:
    - Expert Python programming
    - FastAPI or Django
    - REST API design
    - PostgreSQL
    - Docker
    - Git
    - Unit testing
    - 5+ years experience
    """

    # Example usage
    evaluation, toon, execution = evaluate_candidate(
        resume_pdf_path="/Users/thiruanand/2025-hackaton/hackathon-2025/track_a_iron_man/Resume V20.pdf",
        jd_text=jd_text,
        jd_job_title="Senior Python Backend Developer",
        verbose=True,
        testing=True  # Enable testing mode to cache GitHub data
    )

    print(f"\n🎉 Pipeline 2 Complete!")
    print(f"   Candidate: {evaluation.candidate_name}")
    if evaluation.final_decision:
        print(f"   Fit: {'YES' if evaluation.final_decision.is_fit else 'NO'}")
        print(f"   Score: {evaluation.final_decision.overall_score}/100")
        print(f"   Recommendation: {evaluation.final_decision.recommendation}")
    else:
        print(f"   Fit: INCOMPLETE")
        print(f"   Score: N/A")
        print(f"   Recommendation: partial-evaluation")

    if execution:
        print(f"\n📊 Execution Tracking:")
        print(f"   Execution ID: {execution.execution_id}")
        print(f"   Duration: {execution.total_duration_ms:.2f}ms")
        print(f"   Total Tokens: {execution.total_tokens}")
        print(f"   Total Cost: ${execution.total_cost_usd:.4f}")
        if execution.langsmith_url:
            print(f"   LangSmith: {execution.langsmith_url}")

    if TESTING_MODE:
        print(f"\n💾 Cache location: {CACHE_DIR}")
        print(f"   Subsequent runs will use cached data until testing=False")
