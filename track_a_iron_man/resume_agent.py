"""
Token-Optimized Resume Analysis Agent
Uses TOON format for OUTPUT to reduce tokens by 30-60%
(Full PDF context is still passed to LLM for analysis)
"""

import sys
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import tiktoken
import json

# Import TOON encoder
from toon import encode as toon_encode

# Import LangChain components
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

# Import PDF extractor
from pdf_extractor import extract_pdf

# Load environment variables
env_path = Path('./.env')
if env_path.exists():
    load_dotenv(env_path)

# Import Holistic AI Bedrock helper
sys.path.insert(0, './core')
try:
    from react_agent.holistic_ai_bedrock import get_chat_model
except ImportError:
    print("⚠️  Could not import Holistic AI Bedrock helper")
    from langchain_openai import ChatOpenAI
    def get_chat_model(model_name):
        return ChatOpenAI(model="gpt-4")


# ============================================
# Comprehensive Resume Schema
# ============================================

class Education(BaseModel):
    """Educational background"""
    degree: str = Field(description="Degree name (e.g., MSc, BTech, BS)")
    institution: str = Field(description="University/College name")
    field: Optional[str] = Field(default=None, description="Field of study/major")
    year: Optional[str] = Field(default=None, description="Graduation year or duration")
    gpa: Optional[str] = Field(default=None, description="GPA if mentioned")


class WorkExperience(BaseModel):
    """Work experience entry"""
    title: str = Field(description="Job title")
    company: str = Field(description="Company name")
    duration: Optional[str] = Field(default=None, description="Time period (e.g., Jan 2023 - Present)")
    location: Optional[str] = Field(default=None, description="Location if mentioned")


class Project(BaseModel):
    """Project from resume"""
    name: str = Field(description="Project name")
    github_link: Optional[str] = Field(default=None, description="GitHub link if available")
    description: str = Field(description="Brief description")


class ContactInfo(BaseModel):
    """Contact information"""
    name: Optional[str] = Field(default=None, description="Full name")
    email: Optional[str] = Field(default=None, description="Email address")
    phone: Optional[str] = Field(default=None, description="Phone number")
    linkedin: Optional[str] = Field(default=None, description="LinkedIn URL")
    github: Optional[str] = Field(default=None, description="GitHub URL")
    location: Optional[str] = Field(default=None, description="City/Country")


class ResumeExtract(BaseModel):
    """Comprehensive resume extraction"""
    contact: ContactInfo = Field(description="Contact information")
    education: List[Education] = Field(description="Educational background")
    experience: List[WorkExperience] = Field(description="Work experience")
    projects: List[Project] = Field(description="Projects")
    tools: List[str] = Field(description="All tools, technologies, languages, frameworks")
    certifications: List[str] = Field(default_factory=list, description="Certifications and awards")
    years_experience: Optional[int] = Field(default=None, description="Estimated total years of work experience")


# ============================================
# Token Counter Utility
# ============================================

def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count tokens in text using tiktoken."""
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except:
        # Fallback: approximate 1 token = 4 chars
        return len(text) // 4


# ============================================
# Tool (keeps FULL PDF context)
# ============================================

@tool
def extract_resume_text(pdf_path: str) -> str:
    """Extract FULL text from resume PDF.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Complete resume text (no truncation - full context preserved)
    """
    try:
        # Return FULL text - no truncation
        return extract_pdf(pdf_path)
    except Exception as e:
        return f"Error: {str(e)}"


# ============================================
# Main Analysis Function
# ============================================

def analyze_resume_with_toon(pdf_path: str, verbose: bool = True):
    """Analyze resume and save in TOON format for token efficiency.

    TOON optimization is applied to OUTPUT, not input.
    The LLM receives the FULL PDF context.

    Args:
        pdf_path: Path to resume PDF
        verbose: Print details

    Returns:
        Tuple of (ResumeExtract, token_stats)
    """
    if verbose:
        print("\n" + "="*70)
        print("🔍 Token-Optimized Resume Analysis")
        print("="*70)
        print(f"📄 File: {pdf_path}")
        print("💡 Strategy: Full PDF context for analysis")
        print("           TOON format for output (30-60% token reduction)\n")

    # Create LLM and agent
    llm = get_chat_model("claude-3-5-sonnet")
    agent = create_react_agent(
        llm,
        tools=[extract_resume_text],
        response_format=ResumeExtract
    )

    # Prompt (comprehensive extraction)
    prompt = f"""Extract ALL information from resume: {pdf_path}

Use extract_resume_text tool to read FULL content.

Extract:
- contact: name, email, phone, linkedin, github, location
- education: degree, institution, field of study, year, GPA
- experience: job title, company, duration, location
- projects: name, github_link (if exists), description
- tools: all technologies/languages/frameworks
- certifications: all certifications, awards, honors
- years_experience: estimated total years of professional work"""

    # Invoke agent
    result = agent.invoke({
        "messages": [HumanMessage(content=prompt)]
    })

    # Get structured output
    data = result['structured_response']

    # Compare JSON vs TOON output
    output_json = json.dumps(data.model_dump(), indent=2)
    output_toon = toon_encode(data.model_dump())

    json_tokens = count_tokens(output_json)
    toon_tokens = count_tokens(output_toon)
    reduction_pct = ((json_tokens - toon_tokens) / json_tokens * 100) if json_tokens > 0 else 0

    stats = {
        'output_json_tokens': json_tokens,
        'output_toon_tokens': toon_tokens,
        'tokens_saved': json_tokens - toon_tokens,
        'reduction_percent': reduction_pct
    }

    if verbose:
        print("="*70)
        print("📊 TOKEN COMPARISON (OUTPUT FORMAT)")
        print("="*70)
        print(f"JSON output:      {stats['output_json_tokens']:>6} tokens")
        print(f"TOON output:      {stats['output_toon_tokens']:>6} tokens")
        print(f"Tokens saved:     {stats['tokens_saved']:>6} tokens")
        print(f"Reduction:        {stats['reduction_percent']:>6.1f}%")

        print("\n" + "="*70)
        print("✅ EXTRACTION RESULTS")
        print("="*70)

        # Contact Info
        print(f"\n👤 CONTACT INFO:")
        print("-"*70)
        if data.contact.name:
            print(f"Name:      {data.contact.name}")
        if data.contact.email:
            print(f"Email:     {data.contact.email}")
        if data.contact.phone:
            print(f"Phone:     {data.contact.phone}")
        if data.contact.location:
            print(f"Location:  {data.contact.location}")
        if data.contact.linkedin:
            print(f"LinkedIn:  {data.contact.linkedin}")
        if data.contact.github:
            print(f"GitHub:    {data.contact.github}")

        # Education
        print(f"\n\n🎓 EDUCATION ({len(data.education)}):")
        print("-"*70)
        for i, edu in enumerate(data.education, 1):
            print(f"\n{i}. {edu.degree}")
            print(f"   Institution: {edu.institution}")
            if edu.field:
                print(f"   Field:       {edu.field}")
            if edu.year:
                print(f"   Year:        {edu.year}")
            if edu.gpa:
                print(f"   GPA:         {edu.gpa}")

        # Work Experience
        print(f"\n\n💼 WORK EXPERIENCE ({len(data.experience)}):")
        print("-"*70)
        for i, exp in enumerate(data.experience, 1):
            print(f"\n{i}. {exp.title}")
            print(f"   Company:  {exp.company}")
            if exp.duration:
                print(f"   Duration: {exp.duration}")
            if exp.location:
                print(f"   Location: {exp.location}")

        # Projects
        print(f"\n\n📦 PROJECTS ({len(data.projects)}):")
        print("-"*70)
        for i, proj in enumerate(data.projects, 1):
            print(f"\n{i}. {proj.name}")
            if proj.github_link:
                print(f"   🔗 {proj.github_link}")
            print(f"   📝 {proj.description}")

        # Tools
        print(f"\n\n🛠️  TOOLS ({len(data.tools)}):")
        print("-"*70)
        for tool in data.tools:
            print(f"  • {tool}")

        # Certifications
        if data.certifications:
            print(f"\n\n🏆 CERTIFICATIONS & AWARDS ({len(data.certifications)}):")
            print("-"*70)
            for cert in data.certifications:
                print(f"  • {cert}")

        # Years of Experience
        if data.years_experience:
            print(f"\n\n⏱️  TOTAL EXPERIENCE: ~{data.years_experience} years")

    # Save both formats
    print("\n" + "="*70)
    print("💾 SAVING OUTPUTS")
    print("="*70)

    # Save JSON
    with open('resume_extract.json', 'w') as f:
        f.write(output_json)
    print(f"✅ JSON: resume_extract.json ({json_tokens} tokens)")

    # Save TOON
    with open('resume_extract.toon', 'w') as f:
        f.write(output_toon)
    print(f"✅ TOON: resume_extract.toon ({toon_tokens} tokens)")

    # Show format comparison
    print("\n" + "="*70)
    print("📋 FORMAT COMPARISON")
    print("="*70)

    print("\n🔵 JSON FORMAT (first 300 chars):")
    print("-"*70)
    print(output_json[:300] + "..." if len(output_json) > 300 else output_json)

    print("\n\n🟢 TOON FORMAT (first 300 chars):")
    print("-"*70)
    print(output_toon[:300] + "..." if len(output_toon) > 300 else output_toon)

    # Cost estimate
    print("\n" + "="*70)
    print("💰 COST SAVINGS ESTIMATE")
    print("="*70)
    cost_per_1k = 0.03  # Example: GPT-4 pricing
    json_cost = (json_tokens / 1000) * cost_per_1k
    toon_cost = (toon_tokens / 1000) * cost_per_1k

    print(f"JSON cost:         ${json_cost:.5f}")
    print(f"TOON cost:         ${toon_cost:.5f}")
    print(f"Saved per resume:  ${json_cost - toon_cost:.5f}")
    print(f"Saved per 1K:      ${(json_cost - toon_cost) * 1000:.2f}")

    return data, stats


# ============================================
# Main
# ============================================

if __name__ == "__main__":
    pdf_path = "/Users/thiruanand/2025-hackaton/hackathon-2025/track_a_iron_man/cv_lt (2).pdf"
    result, stats = analyze_resume_with_toon(pdf_path, verbose=True)
