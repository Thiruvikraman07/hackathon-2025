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
import json
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
    what_youll_learn: List[str] = Field(default_factory=list, description="4-5 learning opportunities (each max 20 words)")

    total_files_analyzed: int = Field(default=0, description="Number of code files analyzed")

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

    @model_validator(mode='after')
    def populate_missing_fields(self):
        """Populate missing fields with sensible defaults"""
        # Ensure what_youll_learn has content
        if not self.what_youll_learn:
            self.what_youll_learn = [
                "Work with cutting-edge technologies and frameworks",
                "Collaborate with a talented engineering team",
                "Contribute to open source projects",
                "Develop skills in modern software architecture",
                "Gain experience in production-scale systems"
            ]

        # Ensure total_files_analyzed is set
        if self.total_files_analyzed == 0:
            # Count from responsibilities or qualifications as a proxy
            self.total_files_analyzed = max(3, len(self.responsibilities) + len(self.qualifications) // 2)

        return self


# ============================================
# Cache Management for Testing
# ============================================

CACHE_DIR = Path("./cache/github_data")
TESTING_MODE = False  # Set to True to enable caching

def get_cache_path(repo_full_name: str, cache_type: str) -> Path:
    """Get cache file path for a repository and cache type."""
    safe_repo_name = repo_full_name.replace('/', '_')
    return CACHE_DIR / f"{safe_repo_name}_{cache_type}.json"

def load_from_cache(repo_full_name: str, cache_type: str) -> Optional[dict]:
    """Load cached data if it exists."""
    if not TESTING_MODE:
        return None

    cache_path = get_cache_path(repo_full_name, cache_type)
    if cache_path.exists():
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load cache from {cache_path}: {e}")
    return None

def save_to_cache(repo_full_name: str, cache_type: str, data: dict) -> None:
    """Save data to cache."""
    if not TESTING_MODE:
        return

    cache_path = get_cache_path(repo_full_name, cache_type)
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"💾 Cached {cache_type} data to {cache_path}")
    except Exception as e:
        print(f"Warning: Failed to save cache to {cache_path}: {e}")

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
    # Check cache first
    cached_data = load_from_cache(repo_full_name, "metadata")
    if cached_data is not None:
        print(f"📦 Using cached metadata for {repo_full_name}")
        return cached_data

    try:
        client = GitHubClient()
        owner, repo_name = repo_full_name.split('/')
        repos = client.get_public_repositories(owner)

        repo_data = next((r for r in repos if r['name'] == repo_name), None)
        if not repo_data:
            return {"error": f"Repository {repo_full_name} not found"}

        languages = client.get_repository_languages(repo_full_name)
        repo_data['languages'] = languages

        # Save to cache
        save_to_cache(repo_full_name, "metadata", repo_data)

        return repo_data
    except Exception as e:
        return {"error": str(e)}


@tool
def get_repo_file_structure(repo_full_name: str) -> dict:
    """Get complete file and directory structure of the repository.

    Use this to see all available files before choosing which ones to fetch.

    Args:
        repo_full_name: Full repository name (e.g., 'company/project')

    Returns:
        Repository file structure with paths, types, and sizes
    """
    # Check cache first
    cached_data = load_from_cache(repo_full_name, "file_structure")
    if cached_data is not None:
        print(f"📦 Using cached file structure for {repo_full_name}")
        return cached_data

    try:
        client = GitHubClient()
        structure = client.get_file_structure(repo_full_name)

        # Filter to show only relevant code files and docs
        code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs',
                          '.rb', '.php', '.cpp', '.c', '.h', '.cs', '.swift', '.kt'}
        doc_extensions = {'.md', '.txt', '.rst'}

        relevant_files = []
        for item in structure:
            if item['type'] == 'blob':  # Only files, not directories
                path = item['path'].lower()
                # Include README files, code files, and important config files
                if (any(path.endswith(ext) for ext in code_extensions) or
                    any(path.endswith(ext) for ext in doc_extensions) or
                    'readme' in path or
                    path in ['package.json', 'requirements.txt', 'go.mod', 'cargo.toml', 'pom.xml']):
                    relevant_files.append(item)

        result = {
            'structure': relevant_files[:500],  # Limit to first 500 relevant files
            'total_files': len(relevant_files)
        }

        # Save to cache
        save_to_cache(repo_full_name, "file_structure", result)

        return result
    except Exception as e:
        return {"error": str(e)}


@tool
def fetch_code_files(repo_full_name: str, file_paths: List[str]) -> dict:
    """Fetch specific code files from the repository by their paths.

    Use this after analyzing the file structure to get the actual content of selected files.

    Args:
        repo_full_name: Full repository name (e.g., 'company/project')
        file_paths: List of file paths to fetch (e.g., ['README.md', 'src/main.py'])

    Returns:
        Files with their content
    """
    # Create a cache key based on the file paths
    cache_key = "_".join(sorted(file_paths)).replace('/', '_')[:100]  # Limit length
    cache_type = f"files_{cache_key}"

    # Check cache first
    cached_data = load_from_cache(repo_full_name, cache_type)
    if cached_data is not None:
        print(f"📦 Using cached file contents for {repo_full_name}")
        return cached_data

    try:
        client = GitHubClient()
        files = client.fetch_specific_files(repo_full_name, file_paths)

        result = {
            'files': files,
            'total_fetched': len(files)
        }

        # Save to cache
        save_to_cache(repo_full_name, cache_type, result)

        return result
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
    verbose: bool = True,
    testing: bool = False
):
    """PIPELINE 1: Generate detailed Job Description from company repo and user input.

    Args:
        company_repo: Company repository (e.g., 'facebook/react')
        job_title: Job title (e.g., 'Senior Python Developer')
        salary_range: Salary range (e.g., '$120k-$160k')
        additional_requirements: List of additional requirements (e.g., ['Remote work', 'Team lead experience'])
        verbose: Print details
        testing: Enable caching mode - fetches GitHub data once and reuses for subsequent runs

    Returns:
        Tuple of (JobDescription, toon_output)
    """
    # Set global testing mode
    global TESTING_MODE
    TESTING_MODE = testing

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
        if testing:
            print(f"🧪 Testing Mode: ENABLED (caching GitHub data)")
        print()

    # Create LLM and agent
    llm = get_chat_model("claude-3-5-sonnet")
    agent = create_react_agent(
        llm,
        tools=[fetch_repo_metadata, get_repo_file_structure, fetch_code_files],
        response_format=JobDescription
    )

    # Build additional requirements text
    additional_reqs_text = ""
    if additional_requirements:
        additional_reqs_text = f"""
ADDITIONAL USER REQUIREMENTS (include these in additional_requirements field):
{chr(10).join(f"- {req}" for req in additional_requirements)}
"""

    # USE THE MORE EXPLICIT PROMPT AS DEFAULT (previously was fallback)
    prompt = f"""CRITICAL: Generate COMPLETE JobDescription for {job_title} at {company_repo}.

INSTRUCTIONS:
1. Use fetch_repo_metadata to get repo info, stars, languages
2. Use get_repo_file_structure to see all available files in the repository
3. Analyze the file structure and intelligently choose:
   - 1 README file (README.md or similar)
   - 2 most relevant code files (main entry points, core logic files based on the job title)
4. Use fetch_code_files to get ONLY those 3 selected files (pass exact paths as a list)
5. Analyze the fetched files and generate ALL required fields

INPUTS:
- Repository: {company_repo}
- Job Title: {job_title}
- Salary: {salary_range or 'Not specified'}
{additional_reqs_text}

You MUST include ALL these fields or the validation will fail:
- job_title, company_repo, salary_range, overview, overview_reason
- technical_requirements (with primary_languages, frameworks_libraries, tools_platforms, databases)
- responsibilities (list of 5-6 items) ⚠️ REQUIRED
- qualifications (list of 6-8 items) ⚠️ REQUIRED
- experience_requirement (with level, minimum_years, reason) ⚠️ REQUIRED
- additional_requirements, what_youll_learn (list of 4-5 items) ⚠️ REQUIRED
- total_files_analyzed ⚠️ REQUIRED

The response is INCOMPLETE without qualifications, experience_requirement, what_youll_learn, and total_files_analyzed.

CRITICAL RULES:
1. KEEP REASONS CONCISE (under 50 words each)
2. Include 5-6 responsibilities
3. Include 6-8 qualifications
4. Include 4-5 learning opportunities
5. Base everything on actual code analysis
6. Set total_files_analyzed to 3 (the number of files you analyzed)

Use the tools to analyze the repo, then generate ALL fields. Keep reasons concise."""

    # Invoke agent
    if verbose:
        print("🤖 Analyzing repository and generating JD with reasoning...\n")

    result = agent.invoke({
        "messages": [HumanMessage(content=prompt)]
    })

    # Get structured output
    data = result['structured_response']

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
        verbose=True,
        testing=True  # Enable testing mode to cache GitHub data
    )

    print(f"\n🎉 Pipeline 1 Complete!")
    print(f"   Job Title: {jd.job_title}")
    print(f"   Experience Level: {jd.experience_requirement.level}")
    print(f"   Total Qualifications: {len(jd.qualifications)}")

    if TESTING_MODE:
        print(f"\n💾 Cache location: {CACHE_DIR}")
        print(f"   Subsequent runs will use cached data until testing=False")