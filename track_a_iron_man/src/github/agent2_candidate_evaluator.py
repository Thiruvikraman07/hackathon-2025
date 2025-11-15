"""
Agent 2: Candidate Project Evaluator
Two paths:
  Path 2.1: GitHub project links provided → Filter relevant → Rate quality
  Path 2.2: Only GitHub username → Get repos → Filter by title → Rate quality
Output: TOON format
"""

import sys
from pathlib import Path
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Import TOON encoder
sys.path.insert(0, '../../')
from toon import encode as toon_encode

# Import LangChain components
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

# Import GitHub client
from github_client import GitHubClient

# Load environment variables
env_path = Path('../../../.env')
if env_path.exists():
    load_dotenv(env_path)

# Import Holistic AI Bedrock helper
sys.path.insert(0, '../../../core')
from react_agent.holistic_ai_bedrock import get_chat_model


# ============================================
# Candidate Evaluation Schema
# ============================================

class ProjectRelevance(BaseModel):
    """Project relevance to JD"""
    project_name: str = Field(description="Project name")
    github_url: str = Field(description="GitHub URL")
    is_relevant: bool = Field(description="Is project relevant to JD")
    relevance_score: int = Field(description="Relevance score 1-10")
    relevance_reason: str = Field(description="Why relevant or not relevant")
    matching_skills: List[str] = Field(description="Skills that match JD requirements")


class ProjectQuality(BaseModel):
    """Quality assessment of a relevant project"""
    project_name: str = Field(description="Project name")
    github_url: str = Field(description="GitHub URL")
    code_quality_score: int = Field(description="Code quality 1-10")
    technical_depth_score: int = Field(description="Technical depth 1-10")
    best_practices_score: int = Field(description="Best practices 1-10")
    overall_score: int = Field(description="Overall score 1-100")
    strengths: List[str] = Field(description="Key strengths (3-5 items)")
    weaknesses: List[str] = Field(description="Areas to improve (2-4 items)")
    technologies_used: List[str] = Field(description="Technologies demonstrated")
    key_files_analyzed: List[str] = Field(description="Key files analyzed (2-3 files)")


class CandidateEvaluation(BaseModel):
    """Complete candidate evaluation"""
    candidate_github_username: str = Field(description="GitHub username")
    evaluation_path: str = Field(description="Path used: path_2.1 (links provided) or path_2.2 (username only)")
    total_projects_found: int = Field(description="Total projects found")
    relevant_projects: List[ProjectRelevance] = Field(description="All projects with relevance assessment")
    quality_assessments: List[ProjectQuality] = Field(description="Quality ratings for relevant projects only")
    overall_rating: int = Field(description="Overall candidate rating 1-100")
    jd_fit_score: int = Field(description="How well candidate fits JD 1-100")
    recommendation: str = Field(description="Hiring recommendation: strong-yes, yes, maybe, no")
    summary: str = Field(description="2-3 sentence summary")


# ============================================
# GitHub Tools
# ============================================

@tool
def get_user_repositories(username: str) -> dict:
    """Get all repositories for a GitHub user.

    Args:
        username: GitHub username

    Returns:
        List of all repositories
    """
    try:
        client = GitHubClient()
        repos = client.get_public_repositories(username)
        return {
            'username': username,
            'repositories': repos,
            'total': len(repos)
        }
    except Exception as e:
        return {"error": str(e)}


@tool
def get_repo_structure(repo_full_name: str) -> dict:
    """Get repository file structure.

    Args:
        repo_full_name: Full repository name

    Returns:
        File structure organized by type
    """
    try:
        client = GitHubClient()
        repo = client.github.get_repo(repo_full_name)
        tree = repo.get_git_tree(repo.default_branch, recursive=True)

        files = {
            'code_files': [],
            'config_files': [],
            'doc_files': []
        }

        for item in tree.tree:
            if item.type == "blob":
                path = item.path
                if any(path.endswith(ext) for ext in ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs']):
                    files['code_files'].append(path)
                elif path.endswith(('.json', '.yaml', '.yml', '.toml')):
                    files['config_files'].append(path)
                elif path.endswith(('.md', '.txt')):
                    files['doc_files'].append(path)

        return {
            'repo': repo_full_name,
            'files': files,
            'total_code_files': len(files['code_files'])
        }
    except Exception as e:
        return {"error": str(e)}


@tool
def fetch_specific_files(repo_full_name: str, file_paths: List[str]) -> dict:
    """Fetch specific files from repository.

    Args:
        repo_full_name: Full repository name
        file_paths: List of file paths to fetch (max 3)

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
                    files_content.append({
                        'path': file_path,
                        'content': response.text[:5000]  # First 5000 chars only
                    })
            except:
                continue

        return {'files': files_content, 'total_fetched': len(files_content)}
    except Exception as e:
        return {"error": str(e)}


# ============================================
# Main Evaluation Function
# ============================================

def evaluate_candidate(
    jd_text: str,
    github_username: Optional[str] = None,
    project_links: Optional[List[str]] = None,
    verbose: bool = True
):
    """Evaluate candidate's GitHub projects against JD.

    Args:
        jd_text: Job description text or key requirements
        github_username: GitHub username (for path 2.2)
        project_links: List of GitHub project URLs (for path 2.1)
        verbose: Print details

    Returns:
        Tuple of (CandidateEvaluation, toon_output)
    """
    if not github_username and not project_links:
        raise ValueError("Must provide either github_username or project_links")

    # Determine path and username
    if project_links:
        path = "path_2.1"
        # Extract username from first project link
        if not github_username:
            github_username = project_links[0].split('/')[-2]
    else:
        path = "path_2.2"

    if verbose:
        print("\n" + "="*70)
        print("🎯 Agent 2: Candidate Project Evaluator")
        print("="*70)
        print(f"👤 Candidate: {github_username}")
        print(f"📍 Path: {path}")
        if project_links:
            print(f"🔗 Project Links: {len(project_links)} provided")
        print()

    # Create LLM and agent
    llm = get_chat_model("claude-3-5-sonnet")
    agent = create_react_agent(
        llm,
        tools=[get_user_repositories, get_repo_structure, fetch_specific_files],
        response_format=CandidateEvaluation
    )

    # Build prompt based on path
    if path == "path_2.1":
        project_instruction = f"""
PATH 2.1: Project links provided

Projects to evaluate:
{chr(10).join(f"  - {link}" for link in project_links)}

Steps:
1. For EACH project, assess relevance to JD
2. For relevant projects ONLY, do quality assessment:
   - Use get_repo_structure to see all files
   - Identify 2-3 most relevant code files
   - Use fetch_specific_files to get those files
   - Rate code quality based on actual code
"""
    else:
        project_instruction = f"""
PATH 2.2: Only GitHub username provided

Steps:
1. Use get_user_repositories to get all repos for: {github_username}
2. Filter repos by TITLE relevance to JD requirements
3. For filtered relevant repos, assess full relevance
4. For relevant projects ONLY, do quality assessment:
   - Use get_repo_structure to see all files
   - Identify 2-3 most relevant code files
   - Use fetch_specific_files to get those files
   - Rate code quality based on actual code
"""

    prompt = f"""Evaluate candidate's GitHub projects against Job Description.

JOB DESCRIPTION / REQUIREMENTS:
{jd_text}

{project_instruction}

OUTPUT STRUCTURE:

candidate_github_username: STRING - "{github_username}"

evaluation_path: STRING - "{path}"

total_projects_found: INTEGER - Total projects examined

relevant_projects: LIST of ALL projects with relevance assessment
  For each project:
    project_name: STRING
    github_url: STRING
    is_relevant: BOOLEAN - true if relevant to JD
    relevance_score: INTEGER 1-10
    relevance_reason: STRING - why relevant or not
    matching_skills: LIST of skills that match JD

quality_assessments: LIST of quality ratings for RELEVANT projects ONLY
  For each relevant project:
    project_name: STRING
    github_url: STRING
    code_quality_score: INTEGER 1-10
    technical_depth_score: INTEGER 1-10
    best_practices_score: INTEGER 1-10
    overall_score: INTEGER 1-100
    strengths: LIST of 3-5 key strengths
    weaknesses: LIST of 2-4 areas to improve
    technologies_used: LIST of technologies demonstrated
    key_files_analyzed: LIST of 2-3 key files you analyzed

overall_rating: INTEGER 1-100 - Overall candidate rating

jd_fit_score: INTEGER 1-100 - How well candidate fits JD

recommendation: STRING - strong-yes/yes/maybe/no

summary: STRING - 2-3 sentence evaluation summary

IMPORTANT:
- Only do quality assessment for relevant projects
- Analyze max 2-3 code files per project
- Base ratings on actual code, not just descriptions"""

    # Invoke agent
    if verbose:
        print(f"🤖 Evaluating projects using {path}...\n")

    result = agent.invoke({
        "messages": [HumanMessage(content=prompt)]
    })

    # Get structured output
    data = result['structured_response']

    # Convert to TOON
    output_toon = toon_encode(data.model_dump())

    if verbose:
        print("="*70)
        print("✅ EVALUATION COMPLETE")
        print("="*70)

        print(f"\n👤 Candidate: {data.candidate_github_username}")
        print(f"📍 Path: {data.evaluation_path}")
        print(f"📊 Overall Rating: {data.overall_rating}/100")
        print(f"🎯 JD Fit Score: {data.jd_fit_score}/100")
        print(f"💡 Recommendation: {data.recommendation.upper()}")

        print(f"\n📝 Summary:")
        print(f"   {data.summary}")

        print(f"\n\n🔍 PROJECT RELEVANCE ({data.total_projects_found} projects):")
        print("-"*70)
        for proj in data.relevant_projects:
            status = "✓ RELEVANT" if proj.is_relevant else "✗ NOT RELEVANT"
            print(f"\n{status} - {proj.project_name} ({proj.relevance_score}/10)")
            print(f"   {proj.github_url}")
            print(f"   Reason: {proj.relevance_reason}")
            if proj.matching_skills:
                print(f"   Skills: {', '.join(proj.matching_skills)}")

        print(f"\n\n⭐ QUALITY ASSESSMENTS ({len(data.quality_assessments)} relevant projects):")
        print("-"*70)
        for qual in data.quality_assessments:
            print(f"\n{qual.project_name} - {qual.overall_score}/100")
            print(f"   Code Quality: {qual.code_quality_score}/10")
            print(f"   Technical Depth: {qual.technical_depth_score}/10")
            print(f"   Best Practices: {qual.best_practices_score}/10")
            print(f"   Technologies: {', '.join(qual.technologies_used)}")
            print(f"   Files Analyzed: {', '.join(qual.key_files_analyzed)}")
            print(f"   Strengths:")
            for s in qual.strengths:
                print(f"     + {s}")
            if qual.weaknesses:
                print(f"   Weaknesses:")
                for w in qual.weaknesses:
                    print(f"     - {w}")

    # Save TOON
    output_file = f"{github_username}_evaluation.toon"
    with open(output_file, 'w') as f:
        f.write(output_toon)

    if verbose:
        print("\n" + "="*70)
        print("💾 SAVED OUTPUT")
        print("="*70)
        print(f"✅ TOON: {output_file}")

    return data, output_toon


# ============================================
# Main
# ============================================

if __name__ == "__main__":
    # Example JD
    jd = """
    Senior Python Developer
    Required: Python, FastAPI, REST APIs, async programming, testing
    Nice to have: Docker, AWS, PostgreSQL
    """

    # Path 2.1: With project links
    print("=" * 80)
    print("Testing PATH 2.1: Project links provided")
    print("=" * 80)
    result1, toon1 = evaluate_candidate(
        jd_text=jd,
        project_links=[
            "https://github.com/baljinnyamday/project1",
            "https://github.com/baljinnyamday/project2"
        ],
        verbose=True
    )

    # Path 2.2: Only username
    print("\n\n" + "=" * 80)
    print("Testing PATH 2.2: Only GitHub username")
    print("=" * 80)
    result2, toon2 = evaluate_candidate(
        jd_text=jd,
        github_username="baljinnyamday",
        verbose=True
    )
