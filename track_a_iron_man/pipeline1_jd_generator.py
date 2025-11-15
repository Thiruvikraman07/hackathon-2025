"""
PIPELINE 1: JD Generator - FIXED VERSION
Input: Company Repo + Job Title + Salary + Additional Requirements
Output: Complete Job Description (TOON format)

Fixed Issues:
1. Simplified schema to reduce token usage
2. Better prompt structure with explicit output format
3. Added retry logic for validation errors
"""

import sys
from pathlib import Path
from typing import List, Optional, Dict, Union, Any
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from dotenv import load_dotenv

# Import TOON encoder
from toon import encode as toon_encode

# Import LangChain components
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

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
# Enhanced Schema with Reason Fields (OPTIMIZED)
# ============================================

class TechRequirementItem(BaseModel):
    """Single tech requirement with reason"""
    name: str = Field(description="Technology name")
    importance: str = Field(description="must-have or nice-to-have")
    reason: str = Field(description="Why this technology is required (max 50 words)")


class TechnicalRequirements(BaseModel):
    """Technical requirements with reasoning"""
    primary_languages: List[TechRequirementItem] = Field(description="Primary languages with reasons (2-3 items)")
    frameworks_libraries: List[TechRequirementItem] = Field(description="Frameworks with reasons (2-4 items)")
    tools_platforms: List[TechRequirementItem] = Field(description="Tools with reasons (2-3 items)")
    databases: List[TechRequirementItem] = Field(default_factory=list, description="Databases with reasons (0-2 items)")

    @field_validator('primary_languages', 'frameworks_libraries', 'tools_platforms', 'databases', mode='before')
    @classmethod
    def convert_strings_to_items(cls, v):
        """Convert string items to TechRequirementItem objects"""
        if not isinstance(v, list):
            return v
        result = []
        for item in v:
            if isinstance(item, str):
                # Convert string to TechRequirementItem with default values
                result.append({
                    'name': item,
                    'importance': 'must-have',
                    'reason': 'Required based on repository analysis'
                })
            elif isinstance(item, dict):
                result.append(item)
            else:
                result.append(item)
        return result


class ResponsibilityItem(BaseModel):
    """Responsibility with reasoning"""
    model_config = ConfigDict(populate_by_name=True)

    responsibility: str = Field(description="Responsibility description (max 30 words)", alias="task")
    reason: str = Field(description="Why this is needed based on repo (max 40 words)")


class QualificationItem(BaseModel):
    """Qualification with reasoning"""
    model_config = ConfigDict(populate_by_name=True)

    qualification: str = Field(description="Required skill (max 20 words)", alias="skill")
    importance: str = Field(default="must-have", description="must-have or nice-to-have")
    reason: str = Field(description="Why this skill is needed (max 40 words)")


class ExperienceRequirement(BaseModel):
    """Experience level with reasoning"""
    level: str = Field(description="junior, mid-level, senior, or expert")
    minimum_years: int = Field(description="Minimum years required")
    reason: str = Field(description="Why this level based on code complexity (max 50 words)")


class JobDescription(BaseModel):
    """Complete Job Description with reasoning for all decisions"""
    job_title: str = Field(description="Job title from user input")
    company_repo: str = Field(description="Company repository analyzed")
    salary_range: Optional[str] = Field(default=None, description="Salary range from user input")

    overview: str = Field(description="2-3 sentence job overview (max 100 words)")
    overview_reason: str = Field(description="Why this overview is accurate (max 50 words)")

    technical_requirements: TechnicalRequirements = Field(description="Tech requirements with reasons")
    responsibilities: List[ResponsibilityItem] = Field(description="5-6 responsibilities with reasons")
    qualifications: List[QualificationItem] = Field(description="6-8 qualifications with reasons")

    experience_requirement: ExperienceRequirement = Field(description="Experience level with reason")

    additional_requirements: List[str] = Field(default_factory=list, description="User-specified additional requirements")
    what_youll_learn: List[str] = Field(description="4-5 learning opportunities (each max 20 words)")

    total_files_analyzed: int = Field(description="Number of code files analyzed")

    @field_validator('salary_range', mode='before')
    @classmethod
    def convert_salary_dict(cls, v):
        """Convert dict salary to string format"""
        if isinstance(v, dict):
            min_val = v.get('min', '')
            max_val = v.get('max', '')
            currency = v.get('currency', 'USD')
            if min_val and max_val:
                return f"${min_val:,}-${max_val:,}" if currency == 'USD' else f"{min_val:,}-{max_val:,} {currency}"
            return None
        return v


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
        max_files: Max files to sample (default: 10, reduced from 15)

    Returns:
        Sampled code files
    """
    try:
        client = GitHubClient()
        extensions = ['.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs', '.rb', '.php', '.cpp']

        files = client.sample_files_efficiently(
            repo_full_name,
            extensions,
            max_files=max_files
        )

        return {'files': files, 'total_sampled': len(files)}
    except Exception as e:
        return {"error": str(e)}


# ============================================
# Main Pipeline 1 Function
# ============================================

def generate_jd(
    company_repo: str,
    job_title: str,
    salary_range: Optional[str] = None,
    additional_requirements: Optional[List[str]] = None,
    verbose: bool = True
):
    """PIPELINE 1: Generate detailed Job Description from company repo and user input.

    Args:
        company_repo: Company repository (e.g., 'facebook/react')
        job_title: Job title (e.g., 'Senior Python Developer')
        salary_range: Salary range (e.g., '$120k-$160k')
        additional_requirements: List of additional requirements (e.g., ['Remote work', 'Team lead experience'])
        verbose: Print details

    Returns:
        Tuple of (JobDescription, toon_output)
    """
    if verbose:
        print("\n" + "="*80)
        print("🚀 PIPELINE 1: JD Generator")
        print("="*80)
        print(f"📦 Company Repo: {company_repo}")
        print(f"💼 Job Title: {job_title}")
        if salary_range:
            print(f"💰 Salary: {salary_range}")
        if additional_requirements:
            print(f"📋 Additional Requirements: {len(additional_requirements)}")
        print()

    # Create LLM and agent
    llm = get_chat_model("claude-3-5-sonnet")
    agent = create_react_agent(
        llm,
        tools=[fetch_repo_metadata, sample_repo_code],
        response_format=JobDescription
    )

    # Build additional requirements text
    additional_reqs_text = ""
    if additional_requirements:
        additional_reqs_text = f"""
ADDITIONAL USER REQUIREMENTS (include these in additional_requirements field):
{chr(10).join(f"- {req}" for req in additional_requirements)}
"""

    # IMPROVED PROMPT - More explicit about structure and completeness
    prompt = f"""Generate a COMPLETE Job Description by analyzing the company repository.

INPUTS:
- Repository: {company_repo}
- Job Title: {job_title}
- Salary: {salary_range or 'Not specified'}
{additional_reqs_text}

INSTRUCTIONS:
1. Use fetch_repo_metadata to get repo info, stars, languages
2. Use sample_repo_code to analyze 10 actual code files
3. Generate ALL required fields (see structure below)

REQUIRED OUTPUT STRUCTURE - YOU MUST INCLUDE ALL FIELDS:

{{
  "job_title": "{job_title}",
  "company_repo": "{company_repo}",
  "salary_range": "{salary_range or None}",
  
  "overview": "2-3 sentences about the role",
  "overview_reason": "Why this overview fits (be concise)",
  
  "technical_requirements": {{
    "primary_languages": [
      {{"name": "X", "importance": "must-have", "reason": "Brief reason from code"}}
    ],
    "frameworks_libraries": [
      {{"name": "Y", "importance": "must-have", "reason": "Brief reason"}}
    ],
    "tools_platforms": [
      {{"name": "Z", "importance": "must-have", "reason": "Brief reason"}}
    ],
    "databases": []
  }},
  
  "responsibilities": [
    {{"responsibility": "Do X", "reason": "Because code shows Y"}},
    {{"responsibility": "Do Z", "reason": "Because repo has W"}}
  ],

  "qualifications": [
    {{"qualification": "X years of Y", "importance": "must-have", "reason": "Code complexity requires this"}},
    {{"qualification": "Experience with Z", "importance": "nice-to-have", "reason": "Would help with W"}}
  ],
  
  "experience_requirement": {{
    "level": "senior",
    "minimum_years": 5,
    "reason": "Code complexity and architecture requires this"
  }},
  
  "additional_requirements": {additional_requirements or []},
  
  "what_youll_learn": [
    "Learning opportunity 1",
    "Learning opportunity 2"
  ],
  
  "total_files_analyzed": 10
}}

CRITICAL RULES:
1. KEEP REASONS CONCISE (under 50 words each)
2. Include 5-6 responsibilities
3. Include 6-8 qualifications
4. Include 4-5 learning opportunities
5. Base everything on actual code analysis
6. YOU MUST GENERATE ALL FIELDS - the response is incomplete without them

Generate the complete job description now."""

    # Invoke agent
    if verbose:
        print("🤖 Analyzing repository and generating JD with reasoning...\n")

    try:
        result = agent.invoke({
            "messages": [HumanMessage(content=prompt)]
        })

        # Get structured output
        data = result['structured_response']

    except ValueError as e:
        if "Failed to validate structured output" in str(e):
            print("⚠️  First attempt incomplete. Trying with more explicit prompt...\n")
            
            # Retry with even more explicit prompt
            retry_prompt = f"""CRITICAL: Generate COMPLETE JobDescription for {job_title} at {company_repo}.

You MUST include ALL these fields or the validation will fail:
- job_title, company_repo, salary_range, overview, overview_reason
- technical_requirements (with primary_languages, frameworks_libraries, tools_platforms, databases)
- responsibilities (list of 5-6 items)
- qualifications (list of 6-8 items) ⚠️ REQUIRED
- experience_requirement (with level, minimum_years, reason) ⚠️ REQUIRED
- additional_requirements, what_youll_learn (list of 4-5 items) ⚠️ REQUIRED
- total_files_analyzed ⚠️ REQUIRED

The response is INCOMPLETE without qualifications, experience_requirement, what_youll_learn, and total_files_analyzed.

Use the tools to analyze the repo, then generate ALL fields. Keep reasons concise."""
            
            result = agent.invoke({
                "messages": [HumanMessage(content=retry_prompt)]
            })
            data = result['structured_response']
        else:
            raise

    # Convert to TOON
    output_toon = toon_encode(data.model_dump())

    if verbose:
        print("="*80)
        print("✅ JOB DESCRIPTION GENERATED")
        print("="*80)

        print(f"\n📌 {data.job_title}")
        print(f"🏢 Repository: {data.company_repo}")
        if data.salary_range:
            print(f"💰 Salary: {data.salary_range}")

        print(f"\n📝 OVERVIEW:")
        print(f"   {data.overview}")
        print(f"\n   💡 Reason: {data.overview_reason}")

        print(f"\n\n💻 TECHNICAL REQUIREMENTS:")
        print("-"*80)

        print(f"\n🔹 Languages:")
        for lang in data.technical_requirements.primary_languages:
            print(f"   • {lang.name} [{lang.importance}]")
            print(f"     💡 {lang.reason}")

        print(f"\n🔹 Frameworks/Libraries:")
        for fw in data.technical_requirements.frameworks_libraries:
            print(f"   • {fw.name} [{fw.importance}]")
            print(f"     💡 {fw.reason}")

        if data.technical_requirements.tools_platforms:
            print(f"\n🔹 Tools/Platforms:")
            for tool in data.technical_requirements.tools_platforms:
                print(f"   • {tool.name} [{tool.importance}]")
                print(f"     💡 {tool.reason}")

        print(f"\n\n📋 RESPONSIBILITIES:")
        print("-"*80)
        for i, resp in enumerate(data.responsibilities, 1):
            print(f"\n{i}. {resp.responsibility}")
            print(f"   💡 {resp.reason}")

        print(f"\n\n🎯 QUALIFICATIONS:")
        print("-"*80)
        must_have = [q for q in data.qualifications if q.importance == "must-have"]
        nice_to_have = [q for q in data.qualifications if q.importance == "nice-to-have"]

        print(f"\nMust Have:")
        for qual in must_have:
            print(f"   ✓ {qual.qualification}")
            print(f"     💡 {qual.reason}")

        if nice_to_have:
            print(f"\nNice to Have:")
            for qual in nice_to_have:
                print(f"   • {qual.qualification}")
                print(f"     💡 {qual.reason}")

        print(f"\n\n⏱️  EXPERIENCE REQUIREMENT:")
        print("-"*80)
        print(f"Level: {data.experience_requirement.level} ({data.experience_requirement.minimum_years}+ years)")
        print(f"💡 Reason: {data.experience_requirement.reason}")

        if data.additional_requirements:
            print(f"\n\n📌 ADDITIONAL REQUIREMENTS:")
            print("-"*80)
            for req in data.additional_requirements:
                print(f"   • {req}")

        print(f"\n\n🚀 WHAT YOU'LL LEARN:")
        print("-"*80)
        for item in data.what_youll_learn:
            print(f"   • {item}")

        print(f"\n\n📊 ANALYSIS STATS:")
        print("-"*80)
        print(f"Files Analyzed: {data.total_files_analyzed}")

    # Save TOON
    output_file = f"{company_repo.replace('/', '_')}_jd.toon"
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
    # Example usage
    jd, toon = generate_jd(
        company_repo="fastapi/fastapi",
        job_title="Senior Backend Engineer",
        salary_range="$140k-$180k",
        additional_requirements=[
            "Experience leading a team of 3-5 developers",
            "Strong communication skills for remote work",
            "Open source contribution experience"
        ],
        verbose=True
    )

    print(f"\n🎉 Pipeline 1 Complete!")
    print(f"   Job Title: {jd.job_title}")
    print(f"   Experience Level: {jd.experience_requirement.level}")
    print(f"   Total Qualifications: {len(jd.qualifications)}")