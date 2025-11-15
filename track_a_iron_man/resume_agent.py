"""
Simple Resume Analysis Agent
Extracts: Projects with GitHub links + Tools/Technologies
"""

import os
import sys
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Import LangChain components
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

# Import PDF extractor
from pdf_extractor import extract_pdf

# Load environment variables
env_path = Path('../.env')
if env_path.exists():
    load_dotenv(env_path)

# Import Holistic AI Bedrock helper
sys.path.insert(0, '../core')
try:
    from react_agent.holistic_ai_bedrock import get_chat_model
except ImportError:
    print("⚠️  Could not import Holistic AI Bedrock helper")
    from langchain_openai import ChatOpenAI
    def get_chat_model(model_name):
        return ChatOpenAI(model="gpt-4")


# ============================================
# Simple Schema - Just Projects & Tools
# ============================================

class Project(BaseModel):
    """A project from the resume"""
    name: str = Field(description="Project name")
    github_link: Optional[str] = Field(default=None, description="GitHub repository link if available, null if not mentioned")
    description: str = Field(description="Brief description of what the project does")


class ResumeExtract(BaseModel):
    """Simple extraction: projects and tools"""
    projects: List[Project] = Field(description="List of projects with their name, GitHub link (if available), and description as structured objects")
    tools: List[str] = Field(description="All tools, technologies, programming languages, frameworks the person knows")


# ============================================
# Simple Tool
# ============================================

@tool
def extract_resume_text(pdf_path: str) -> str:
    """Extract text from resume PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Text content from the PDF
    """
    try:
        return extract_pdf(pdf_path)
    except Exception as e:
        return f"Error: {str(e)}"


# ============================================
# Simple Resume Agent
# ============================================

def analyze_resume(pdf_path: str):
    """Extract projects and tools from resume.

    Args:
        pdf_path: Path to resume PDF

    Returns:
        ResumeExtract with projects and tools
    """
    print("🤖 Initializing Resume Agent...")

    # Create LLM
    llm = get_chat_model("claude-3-5-sonnet")

    # Create agent with structured output
    agent = create_react_agent(
        llm,
        tools=[extract_resume_text],
        response_format=ResumeExtract
    )

    print(f"📄 Analyzing: {pdf_path}\n")

    # Run the agent
    result = agent.invoke({
        "messages": [HumanMessage(content=f"""Extract from this resume: {pdf_path}

1. All PROJECTS with their GitHub links (if mentioned)
2. All TOOLS/TECHNOLOGIES the person knows (programming languages, frameworks, databases, cloud platforms, etc.)

Use the extract_resume_text tool first to read the PDF.""")]
    })

    # Get structured output
    data = result['structured_response']

    # Print results
    print("="*70)
    print("✅ EXTRACTION COMPLETE")
    print("="*70)

    print(f"\n📦 PROJECTS ({len(data.projects)}):")
    print("-"*70)
    for i, proj in enumerate(data.projects, 1):
        print(f"\n{i}. {proj.name}")
        if proj.github_link:
            print(f"   🔗 GitHub: {proj.github_link}")
        print(f"   📝 {proj.description}")

    print(f"\n\n🛠️  TOOLS & TECHNOLOGIES ({len(data.tools)}):")
    print("-"*70)
    for tool in data.tools:
        print(f"  • {tool}")

    return data


# ============================================
# Main
# ============================================

if __name__ == "__main__":
    pdf_path = "/Users/thiruanand/2025-hackaton/hackathon-2025/track_a_iron_man/cv_lt (2).pdf"

    result = analyze_resume(pdf_path)

    # Save to JSON
    import json
    output_file = "resume_extract.json"
    with open(output_file, 'w') as f:
        json.dump(result.model_dump(), f, indent=2)

    print(f"\n\n💾 Saved to: {output_file}")
