"""
PIPELINE 2: Complete Candidate Evaluator
Input: Resume PDF + Job Description
Output: Full evaluation with GitHub analysis + Fit/No-Fit decision with detailed reasons

Every decision includes a 'reason' field explaining why.
"""

import sys
from pathlib import Path
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
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


# ============================================
# Enhanced Schema with Reason Fields
# ============================================

class SkillMatch(BaseModel):
    """Skill matching with reasoning"""
    skill_name: str = Field(description="Skill from JD")
    has_skill: bool = Field(description="Does candidate have this skill")
    evidence: str = Field(description="Where in resume/GitHub this skill is demonstrated")
    proficiency_score: int = Field(description="Proficiency level 1-10")
    reason: str = Field(description="Why this score was given")


class ResumeAnalysis(BaseModel):
    """Resume analysis with reasoning"""
    years_of_experience: int = Field(description="Total years of experience")
    years_reason: str = Field(description="How years were calculated")

    education_match: bool = Field(description="Education meets requirements")
    education_reason: str = Field(description="Why education matches or not")

    skill_matches: List[SkillMatch] = Field(description="Detailed skill matching")

    relevant_experience: List[str] = Field(description="Relevant work experiences")
    relevant_experience_reason: str = Field(description="Why these experiences are relevant")

    resume_strength_score: int = Field(description="Resume strength 1-100")
    resume_strength_reason: str = Field(description="Why this score")


class GitHubProjectRelevance(BaseModel):
    """GitHub project relevance with reasoning"""
    project_name: str = Field(description="Project name")
    github_url: str = Field(description="GitHub URL")
    is_relevant: bool = Field(description="Is relevant to JD")
    relevance_score: int = Field(description="Relevance score 1-10")
    relevance_reason: str = Field(description="Why relevant or not")
    technologies_matched: List[str] = Field(description="Technologies that match JD")


class GitHubCodeQuality(BaseModel):
    """Code quality assessment with reasoning"""
    project_name: str = Field(description="Project name")
    code_quality_score: int = Field(description="Code quality 1-10")
    code_quality_reason: str = Field(description="Why this quality score")

    technical_depth_score: int = Field(description="Technical depth 1-10")
    technical_depth_reason: str = Field(description="Why this depth score")

    best_practices_score: int = Field(description="Best practices 1-10")
    best_practices_reason: str = Field(description="Why this practices score")

    files_analyzed: List[str] = Field(description="Files analyzed (2-3 max)")
    key_strengths: List[str] = Field(description="Key strengths found")
    key_weaknesses: List[str] = Field(description="Areas to improve")


class GitHubAnalysis(BaseModel):
    """Complete GitHub analysis"""
    github_username: Optional[str] = Field(default=None, description="GitHub username")
    has_github: bool = Field(description="Does candidate have GitHub")
    github_check_reason: str = Field(description="How GitHub was identified")

    projects_found: int = Field(default=0, description="Total projects found")
    projects_found_reason: str = Field(description="How projects were found")

    relevant_projects: List[GitHubProjectRelevance] = Field(default_factory=list, description="Relevant projects")
    quality_assessments: List[GitHubCodeQuality] = Field(default_factory=list, description="Quality assessments")

    github_contribution_score: int = Field(description="GitHub activity score 1-100")
    github_score_reason: str = Field(description="Why this GitHub score")


class ExperienceGapAnalysis(BaseModel):
    """Gap analysis with detailed reasons"""
    gap_name: str = Field(description="Name of the gap")
    severity: str = Field(description="critical, moderate, or minor")
    description: str = Field(description="Description of the gap")
    reason: str = Field(description="Why this is a gap and its severity")
    can_be_learned: bool = Field(description="Can this gap be filled with training")
    learning_reason: str = Field(description="Why it can or cannot be learned")


class FinalDecision(BaseModel):
    """Final hiring decision with comprehensive reasoning"""
    is_fit: bool = Field(description="Is candidate a fit for the role")
    fit_reason: str = Field(description="Comprehensive reason for fit/no-fit decision")

    overall_score: int = Field(description="Overall candidate score 1-100")
    overall_score_breakdown: str = Field(description="How overall score was calculated")

    resume_score: int = Field(description="Resume contribution to score 1-100")
    github_score: int = Field(description="GitHub contribution to score 1-100")
    skill_match_score: int = Field(description="Skill matching score 1-100")

    recommendation: str = Field(description="strong-hire, hire, maybe, no-hire")
    recommendation_reason: str = Field(description="Why this recommendation level")

    confidence_level: int = Field(description="Confidence in decision 1-100")
    confidence_reason: str = Field(description="Why this confidence level")


class CandidateEvaluation(BaseModel):
    """Complete candidate evaluation with all reasoning"""
    candidate_name: str = Field(description="Candidate name")
    job_title: str = Field(description="Job title from JD")

    resume_analysis: ResumeAnalysis = Field(description="Resume analysis")
    github_analysis: GitHubAnalysis = Field(description="GitHub analysis")

    skill_gaps: List[ExperienceGapAnalysis] = Field(description="Identified gaps")
    skill_gaps_summary: str = Field(description="Overall gaps summary with reasoning")

    strengths: List[str] = Field(description="Top 5 candidate strengths")
    strengths_reason: str = Field(description="Why these are the top strengths")

    final_decision: FinalDecision = Field(description="Final hiring decision")

    detailed_feedback: str = Field(description="Detailed feedback for candidate (2-3 paragraphs)")
    hiring_manager_notes: str = Field(description="Notes for hiring manager (2-3 paragraphs)")


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
    try:
        client = GitHubClient()
        return client.get_profile_info(username)
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
    try:
        client = GitHubClient()
        repos = client.get_public_repositories(username)
        return {'username': username, 'repositories': repos, 'total': len(repos)}
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

        return {'repo': repo_full_name, 'files': files, 'total_code_files': len(files['code_files'])}
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

        return {'files': files_content, 'total_fetched': len(files_content)}
    except Exception as e:
        return {"error": str(e)}


# ============================================
# Main Pipeline 2 Function
# ============================================

def evaluate_candidate(
    resume_pdf_path: str,
    jd_text: str,
    jd_job_title: str,
    verbose: bool = True
):
    """PIPELINE 2: Complete candidate evaluation with resume + GitHub analysis.

    Args:
        resume_pdf_path: Path to candidate's resume PDF
        jd_text: Job description text (from Pipeline 1 or custom)
        jd_job_title: Job title from JD
        verbose: Print details

    Returns:
        Tuple of (CandidateEvaluation, toon_output)
    """
    if verbose:
        print("\n" + "="*80)
        print("🎯 PIPELINE 2: Complete Candidate Evaluator")
        print("="*80)
        print(f"📄 Resume: {resume_pdf_path}")
        print(f"💼 Job Title: {jd_job_title}")
        print()

    # Create LLM and agent
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

    # Invoke agent
    if verbose:
        print("🤖 Analyzing resume and GitHub projects...\n")

    result = agent.invoke({
        "messages": [HumanMessage(content=prompt)]
    })

    # Get structured output
    data = result['structured_response']

    # Convert to TOON
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

        # Resume Analysis
        print(f"\n\n📄 RESUME ANALYSIS:")
        print("-"*80)
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

        # GitHub Analysis
        print(f"\n\n💻 GITHUB ANALYSIS:")
        print("-"*80)
        if data.github_analysis.has_github:
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
        else:
            print(f"No GitHub found")
            print(f"💡 {data.github_analysis.github_check_reason}")

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

    return data, output_toon


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
    evaluation, toon = evaluate_candidate(
        resume_pdf_path="/Users/thiruanand/2025-hackaton/hackathon-2025/track_a_iron_man/Resume V20.pdf",
        jd_text=jd_text,
        jd_job_title="Senior Python Backend Developer",
        verbose=True
    )

    print(f"\n🎉 Pipeline 2 Complete!")
    print(f"   Candidate: {evaluation.candidate_name}")
    print(f"   Fit: {'YES' if evaluation.final_decision.is_fit else 'NO'}")
    print(f"   Score: {evaluation.final_decision.overall_score}/100")
    print(f"   Recommendation: {evaluation.final_decision.recommendation}")
