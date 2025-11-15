"""
Agent 1: Company Repository to Job Description Generator
Analyzes company repository and generates JD for candidate onboarding
Output: TOON format
"""

import sys
from pathlib import Path
from typing import List, Optional
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
# Job Description Schema
# ============================================

class TechnicalRequirements(BaseModel):
    """Technical skills required"""
    primary_languages: List[str] = Field(description="Primary programming languages")
    frameworks_libraries: List[str] = Field(description="Key frameworks and libraries")
    tools_platforms: List[str] = Field(description="Development tools and platforms")
    databases: List[str] = Field(default_factory=list, description="Database systems")


class Responsibilities(BaseModel):
    """Job responsibilities"""
    main_tasks: List[str] = Field(description="Main job responsibilities (5-7 items)")
    code_areas: List[str] = Field(description="Code areas candidate will work on")


class Qualifications(BaseModel):
    """Candidate qualifications"""
    must_have_skills: List[str] = Field(description="Essential skills (5-8 items)")
    nice_to_have_skills: List[str] = Field(description="Preferred skills (3-5 items)")
    experience_level: str = Field(description="Required experience: junior, mid-level, senior, expert")
    minimum_years: int = Field(description="Minimum years of experience")


class JobDescription(BaseModel):
    """Complete Job Description"""
    job_title: str = Field(description="Job title")
    company_repo: str = Field(description="Company repository name")
    overview: str = Field(description="2-3 sentence job overview")
    technical_requirements: TechnicalRequirements = Field(description="Technical requirements")
    responsibilities: Responsibilities = Field(description="Job responsibilities")
    qualifications: Qualifications = Field(description="Required qualifications")
    what_youll_learn: List[str] = Field(description="What candidate will learn/gain (3-5 items)")


# ============================================
# GitHub Tools
# ============================================

@tool
def fetch_repo_metadata(repo_full_name: str) -> dict:
    """Fetch repository metadata.

    Args:
        repo_full_name: Full repository name (e.g., 'company/project')

    Returns:
        Repository metadata
    """
    try:
        client = GitHubClient()
        owner, repo_name = repo_full_name.split('/')
        repos = client.get_public_repositories(owner)

        repo_data = next((r for r in repos if r['name'] == repo_name), None)
        if not repo_data:
            return {"error": f"Repository {repo_full_name} not found"}

        languages = client.get_repository_languages(repo_full_name)
        repo_data['languages'] = languages

        return repo_data
    except Exception as e:
        return {"error": str(e)}


@tool
def sample_repo_code(repo_full_name: str, max_files: int = 10) -> dict:
    """Sample code files from repository.

    Args:
        repo_full_name: Full repository name
        max_files: Max files to sample (default: 10)

    Returns:
        Sampled code files
    """
    try:
        client = GitHubClient()
        extensions = ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs', '.rb', '.php']

        files = client.sample_files_efficiently(
            repo_full_name,
            extensions,
            max_files=max_files
        )

        return {'files': files, 'total_sampled': len(files)}
    except Exception as e:
        return {"error": str(e)}


# ============================================
# Main Function
# ============================================

def generate_jd_from_repo(repo_full_name: str, verbose: bool = True):
    """Generate Job Description from company repository.

    Args:
        repo_full_name: Full repository name (e.g., 'facebook/react')
        verbose: Print details

    Returns:
        Tuple of (JobDescription, toon_output)
    """
    if verbose:
        print("\n" + "="*70)
        print("📋 Agent 1: Company Repo → Job Description Generator")
        print("="*70)
        print(f"🏢 Repository: {repo_full_name}\n")

    # Create LLM and agent
    llm = get_chat_model("claude-3-5-sonnet")
    agent = create_react_agent(
        llm,
        tools=[fetch_repo_metadata, sample_repo_code],
        response_format=JobDescription
    )

    # Prompt
    prompt = f"""Analyze company repository and generate a Job Description: {repo_full_name}

Use the tools:
1. fetch_repo_metadata - Get repo info, languages
2. sample_repo_code - Sample 10 code files

Generate a JD for onboarding a new developer to this project.

JOB DESCRIPTION STRUCTURE:

job_title: STRING - Appropriate job title (e.g., "Senior Python Developer", "Full-Stack Engineer")

company_repo: STRING - "{repo_full_name}"

overview: STRING - 2-3 sentences describing the role and project

technical_requirements:
  primary_languages: LIST of main languages (e.g., ["Python", "JavaScript"])
  frameworks_libraries: LIST of frameworks (e.g., ["React", "FastAPI", "PostgreSQL"])
  tools_platforms: LIST of tools (e.g., ["Docker", "Git", "CI/CD"])
  databases: LIST of databases (e.g., ["PostgreSQL", "Redis"])

responsibilities:
  main_tasks: LIST of 5-7 main responsibilities
  code_areas: LIST of code areas they'll work on (e.g., ["API development", "Frontend components"])

qualifications:
  must_have_skills: LIST of 5-8 essential skills
  nice_to_have_skills: LIST of 3-5 preferred skills
  experience_level: STRING (junior/mid-level/senior/expert)
  minimum_years: INTEGER

what_youll_learn: LIST of 3-5 things candidate will learn/gain

Be specific based on actual code patterns, tech stack, and project structure.
Make it realistic for onboarding to THIS specific project."""

    # Invoke agent
    if verbose:
        print("🤖 Analyzing repository and generating JD...\n")

    result = agent.invoke({
        "messages": [HumanMessage(content=prompt)]
    })

    # Get structured output
    data = result['structured_response']

    # Convert to TOON
    output_toon = toon_encode(data.model_dump())

    if verbose:
        print("="*70)
        print("✅ JOB DESCRIPTION GENERATED")
        print("="*70)

        print(f"\n📌 {data.job_title}")
        print(f"🏢 Project: {data.company_repo}")
        print(f"\n{data.overview}")

        print(f"\n\n💻 TECHNICAL REQUIREMENTS:")
        print("-"*70)
        print(f"Languages:   {', '.join(data.technical_requirements.primary_languages)}")
        print(f"Frameworks:  {', '.join(data.technical_requirements.frameworks_libraries)}")
        print(f"Tools:       {', '.join(data.technical_requirements.tools_platforms)}")
        if data.technical_requirements.databases:
            print(f"Databases:   {', '.join(data.technical_requirements.databases)}")

        print(f"\n\n📋 RESPONSIBILITIES:")
        print("-"*70)
        for i, task in enumerate(data.responsibilities.main_tasks, 1):
            print(f"{i}. {task}")

        print(f"\n\n🎯 QUALIFICATIONS:")
        print("-"*70)
        print(f"Experience:  {data.qualifications.experience_level} ({data.qualifications.minimum_years}+ years)")
        print(f"\nMust Have:")
        for skill in data.qualifications.must_have_skills:
            print(f"  ✓ {skill}")
        print(f"\nNice to Have:")
        for skill in data.qualifications.nice_to_have_skills:
            print(f"  • {skill}")

        print(f"\n\n🚀 WHAT YOU'LL LEARN:")
        print("-"*70)
        for item in data.what_youll_learn:
            print(f"  • {item}")

    # Save TOON
    output_file = f"{repo_full_name.replace('/', '_')}_jd.toon"
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
    # Example
    repo = "fastapi/fastapi"
    jd, toon = generate_jd_from_repo(repo, verbose=True)
