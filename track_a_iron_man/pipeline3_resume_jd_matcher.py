"""
PIPELINE 3: Direct Resume-JD Matcher (No GitHub Required)
Input: Resume PDF + Job Description (TOON or text)
Output: Detailed matching analysis with Fit/No-Fit decision

This pipeline is designed for scenarios where:
- Candidate has no GitHub profile
- GitHub profile is private/inaccessible
- Quick screening needed without deep code analysis
- Focus on traditional qualifications (education, experience, skills)

Evaluates:
1. Education match (degree, field of study, certifications)
2. Experience match (years, roles, industries)
3. Technical skills match (languages, frameworks, tools)
4. Soft skills and qualifications
5. Career progression and growth
6. Cultural fit indicators
"""

import sys
import json
import uuid
import os
from pathlib import Path
from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict
from dotenv import load_dotenv

# Import TOON encoder/decoder
from toon import encode as toon_encode, decode as toon_decode

# Import LangChain components
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

# Import resume extractor
from pdf_extractor import extract_pdf

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

# Import Holistic AI Bedrock helper
sys.path.insert(0, str(Path(__file__).parent.parent / 'core'))
from react_agent.holistic_ai_bedrock import get_chat_model

# Import observability
from observability import (
    StepType, StepStatus, StepData, PipelineExecution, StepTracker
)


# ============================================
# Enhanced Schema for Resume-JD Matching
# ============================================

class EducationMatch(BaseModel):
    """Education matching analysis"""
    required_degree: str = Field(default="Bachelor's degree", description="Degree required by JD")
    candidate_degree: str = Field(default="Not specified", description="Candidate's degree")
    degree_match: bool = Field(default=False, description="Does degree level match")
    degree_match_reason: str = Field(default="Education information analyzed", description="Why degree matches or not")

    required_field: Optional[str] = Field(default=None, description="Field of study required")
    candidate_field: Optional[str] = Field(default=None, description="Candidate's field")
    field_match: bool = Field(default=True, description="Does field match")
    field_match_reason: str = Field(default="Field analysis completed", description="Why field matches or not")

    certifications: List[str] = Field(default_factory=list, description="Relevant certifications")
    certifications_reason: str = Field(default="No certifications listed", description="How certifications add value")

    education_score: int = Field(default=50, description="Education match score 1-100")
    education_score_reason: str = Field(default="Based on education analysis", description="Why this education score")


class ExperienceMatch(BaseModel):
    """Experience matching analysis"""
    required_years: int = Field(default=0, description="Years required by JD")
    candidate_years: int = Field(default=0, description="Candidate's total years")
    years_match: bool = Field(default=False, description="Does experience meet requirement")
    years_match_reason: str = Field(default="Experience analyzed", description="Why years match or not")

    relevant_roles: List[str] = Field(default_factory=list, description="Relevant job roles from resume")
    relevant_roles_reason: str = Field(default="Roles analyzed", description="Why these roles are relevant")

    industry_match: bool = Field(default=True, description="Industry experience matches")
    industry_match_reason: str = Field(default="Industry alignment analyzed", description="Industry alignment analysis")

    seniority_level: str = Field(default="mid-level", description="junior, mid-level, senior, or expert")
    seniority_match: bool = Field(default=False, description="Seniority level matches requirement")
    seniority_reason: str = Field(default="Seniority level analyzed", description="Why seniority matches or not")

    career_progression: str = Field(default="Career progression analyzed", description="Describe career growth pattern")
    career_progression_score: int = Field(default=50, description="Career growth score 1-100")
    career_progression_reason: str = Field(default="Based on work history", description="Why this progression score")

    experience_score: int = Field(default=50, description="Overall experience score 1-100")
    experience_score_reason: str = Field(default="Based on experience analysis", description="Why this experience score")


class TechnicalSkillMatch(BaseModel):
    """Individual technical skill matching"""
    model_config = ConfigDict(populate_by_name=True)

    skill_name: str = Field(default="Unknown", description="Skill from JD", alias="skill")
    required_level: str = Field(default="intermediate", description="Required proficiency level")

    has_skill: bool = Field(default=False, description="Candidate has this skill")
    candidate_level: str = Field(default="beginner", description="Candidate's proficiency level")

    years_of_experience: int = Field(default=0, description="Years using this skill")
    evidence: str = Field(default="Not mentioned", description="Where in resume this skill appears")

    match_quality: str = Field(default="missing", description="exact, close, partial, or missing")
    match_reason: str = Field(default="Skill match analysis", description="Why this match quality")

    importance: str = Field(default="must-have", description="must-have or nice-to-have")
    gap_severity: Optional[str] = Field(default=None, description="If missing: critical, moderate, minor")


class TechnicalSkillsAnalysis(BaseModel):
    """Complete technical skills analysis"""
    programming_languages: List[TechnicalSkillMatch] = Field(default_factory=list, description="Programming languages match")
    frameworks_libraries: List[TechnicalSkillMatch] = Field(default_factory=list, description="Frameworks match")
    tools_platforms: List[TechnicalSkillMatch] = Field(default_factory=list, description="Tools match")
    databases: List[TechnicalSkillMatch] = Field(default_factory=list, description="Database skills match")
    other_technical: List[TechnicalSkillMatch] = Field(default_factory=list, description="Other tech skills")

    total_skills_required: int = Field(default=0, description="Total technical skills in JD")
    skills_matched: int = Field(default=0, description="Number of skills candidate has")
    skills_missing: int = Field(default=0, description="Number of skills candidate lacks")

    must_have_matched: int = Field(default=0, description="Must-have skills matched")
    must_have_total: int = Field(default=0, description="Total must-have skills")
    must_have_percentage: float = Field(default=0.0, description="Percentage of must-haves matched")

    technical_skills_score: int = Field(default=50, description="Technical skills score 1-100")
    technical_skills_reason: str = Field(default="Technical skills analyzed", description="Why this technical score")

    @field_validator('programming_languages', 'frameworks_libraries', 'tools_platforms', 'databases', 'other_technical', mode='before')
    @classmethod
    def convert_dict_to_list(cls, v):
        """Convert dict of skills to list of TechnicalSkillMatch objects."""
        if isinstance(v, dict):
            result = []
            for skill_name, skill_data in v.items():
                if isinstance(skill_data, dict):
                    result.append({
                        'skill_name': skill_name,
                        'required_level': skill_data.get('required_level', 'intermediate'),
                        'has_skill': skill_data.get('match_quality', 'missing') != 'missing',
                        'candidate_level': skill_data.get('candidate_level', 'beginner'),
                        'years_of_experience': skill_data.get('years_of_experience', 0),
                        'evidence': skill_data.get('evidence', 'Based on resume analysis'),
                        'match_quality': skill_data.get('match_quality', 'missing'),
                        'match_reason': skill_data.get('match_reason', f'{skill_name} analyzed'),
                        'importance': skill_data.get('importance', 'must-have'),
                        'gap_severity': skill_data.get('gap_severity', None)
                    })
                else:
                    result.append({
                        'skill_name': skill_name,
                        'required_level': 'intermediate',
                        'has_skill': True,
                        'candidate_level': 'intermediate',
                        'years_of_experience': 0,
                        'evidence': 'Based on resume analysis',
                        'match_quality': 'partial',
                        'match_reason': f'{skill_name} identified',
                        'importance': 'must-have',
                        'gap_severity': None
                    })
            return result
        return v if isinstance(v, list) else []


class SoftSkillsAnalysis(BaseModel):
    """Soft skills and qualifications analysis"""
    communication_skills: bool = Field(default=False, description="Has communication skills")
    communication_evidence: str = Field(default="", description="Evidence of communication skills")

    leadership_skills: bool = Field(default=False, description="Has leadership experience")
    leadership_evidence: str = Field(default="", description="Evidence of leadership")

    team_collaboration: bool = Field(default=False, description="Team collaboration evidence")
    team_evidence: str = Field(default="", description="Evidence of teamwork")

    problem_solving: bool = Field(default=False, description="Problem-solving demonstrated")
    problem_solving_evidence: str = Field(default="", description="Evidence of problem-solving")

    other_qualifications: List[str] = Field(default_factory=list, description="Other relevant qualifications")
    other_qualifications_reason: str = Field(default="", description="Why these matter")

    soft_skills_score: int = Field(default=50, description="Soft skills score 1-100")
    soft_skills_reason: str = Field(default="Soft skills analyzed", description="Why this soft skills score")

    @field_validator('leadership_skills', mode='before')
    @classmethod
    def convert_leadership_to_bool(cls, v):
        """Convert string leadership assessments to boolean."""
        if isinstance(v, str):
            positive_words = ['yes', 'true', 'evident', 'demonstrated', 'shown', 'good', 'strong', 'excellent']
            negative_words = ['no', 'false', 'limited', 'minimal', 'none', 'lacking']
            v_lower = v.lower()
            if any(word in v_lower for word in positive_words):
                return True
            elif any(word in v_lower for word in negative_words):
                return False
            return True
        return v

    @field_validator('communication_skills', mode='before')
    @classmethod
    def convert_communication_to_bool(cls, v):
        """Convert string communication assessments to boolean."""
        if isinstance(v, str):
            positive_words = ['yes', 'true', 'evident', 'demonstrated', 'shown', 'good', 'strong', 'excellent']
            negative_words = ['no', 'false', 'limited', 'minimal', 'none', 'lacking']
            v_lower = v.lower()
            if any(word in v_lower for word in positive_words):
                return True
            elif any(word in v_lower for word in negative_words):
                return False
            return True
        return v

    @field_validator('team_collaboration', mode='before')
    @classmethod
    def convert_team_to_bool(cls, v):
        """Convert string team collaboration assessments to boolean."""
        if isinstance(v, str):
            positive_words = ['yes', 'true', 'evident', 'demonstrated', 'shown', 'good', 'strong', 'excellent']
            negative_words = ['no', 'false', 'limited', 'minimal', 'none', 'lacking']
            v_lower = v.lower()
            if any(word in v_lower for word in positive_words):
                return True
            elif any(word in v_lower for word in negative_words):
                return False
            return True
        return v

    @field_validator('problem_solving', mode='before')
    @classmethod
    def convert_problem_solving_to_bool(cls, v):
        """Convert string problem solving assessments to boolean."""
        if isinstance(v, str):
            positive_words = ['yes', 'true', 'evident', 'demonstrated', 'shown', 'good', 'strong', 'excellent']
            negative_words = ['no', 'false', 'limited', 'minimal', 'none', 'lacking']
            v_lower = v.lower()
            if any(word in v_lower for word in positive_words):
                return True
            elif any(word in v_lower for word in negative_words):
                return False
            return True
        return v


class GapAnalysis(BaseModel):
    """Detailed gap analysis"""
    model_config = ConfigDict(populate_by_name=True)

    gap_category: str = Field(default="technical", description="education, experience, technical, or soft-skills", alias="category")
    gap_name: str = Field(default="Unknown gap", description="Name of the gap", alias="name")
    gap_description: str = Field(default="Gap identified", description="Detailed description", alias="description")

    severity: str = Field(default="moderate", description="critical, moderate, or minor")
    severity_reason: str = Field(default="Gap severity analyzed", description="Why this severity level")

    impact_on_hiring: str = Field(default="This gap impacts hiring decision", description="How this gap affects hiring decision")

    can_be_filled: bool = Field(default=True, description="Can gap be filled through training")
    time_to_fill: Optional[str] = Field(default=None, description="Estimated time to fill gap")
    fill_strategy: Optional[str] = Field(default=None, description="How to fill this gap")


class MatchingDecision(BaseModel):
    """Final matching decision"""
    is_match: bool = Field(default=False, description="Is candidate a match for JD")
    match_reason: str = Field(default="Match analysis completed", description="Comprehensive reason for match/no-match")

    overall_match_score: int = Field(default=50, description="Overall match score 1-100")
    score_breakdown: str = Field(default="Score calculated from all criteria", description="How score was calculated")

    education_weight: float = Field(default=0.20, description="Education weight in decision")
    experience_weight: float = Field(default=0.30, description="Experience weight in decision")
    technical_weight: float = Field(default=0.35, description="Technical skills weight in decision")
    soft_skills_weight: float = Field(default=0.15, description="Soft skills weight in decision")

    weighted_score: float = Field(default=50.0, description="Weighted average score")
    weighted_calculation: str = Field(default="Weighted average calculated", description="How weighted score was calculated")

    recommendation: str = Field(default="partial-match", description="strong-match, good-match, partial-match, or no-match")
    recommendation_reason: str = Field(default="Based on overall analysis", description="Why this recommendation")

    proceed_to_interview: bool = Field(default=False, description="Should candidate proceed to interview")
    interview_reason: str = Field(default="Based on match score and gaps", description="Why proceed or not to interview")

    confidence_level: int = Field(default=70, description="Confidence in decision 1-100")
    confidence_reason: str = Field(default="Based on available information", description="Why this confidence level")


class ResumeJDMatch(BaseModel):
    """Complete Resume-JD matching analysis"""
    candidate_name: str = Field(default="Unknown", description="Candidate name from resume")
    job_title: str = Field(default="Unknown Position", description="Job title from JD")
    company_repo: Optional[str] = Field(default=None, description="Company repository if available")

    education_match: EducationMatch = Field(default_factory=EducationMatch, description="Education matching analysis")
    experience_match: ExperienceMatch = Field(default_factory=ExperienceMatch, description="Experience matching analysis")
    technical_skills: TechnicalSkillsAnalysis = Field(default_factory=TechnicalSkillsAnalysis, description="Technical skills analysis")
    soft_skills: SoftSkillsAnalysis = Field(default_factory=SoftSkillsAnalysis, description="Soft skills analysis")

    gaps: List[GapAnalysis] = Field(default_factory=list, description="All identified gaps")
    gaps_summary: str = Field(default="Gaps analyzed", description="Summary of all gaps and their impact")

    strengths: List[str] = Field(default_factory=list, description="Top 5-7 candidate strengths")
    strengths_reason: str = Field(default="Strengths identified based on analysis", description="Why these are top strengths")

    @field_validator('gaps', mode='before')
    @classmethod
    def convert_gaps_strings(cls, v):
        """Convert list of strings to GapAnalysis objects."""
        if isinstance(v, list) and v:
            result = []
            for item in v:
                if isinstance(item, str):
                    # Determine severity from string content
                    severity = 'moderate'
                    category = 'technical'
                    if any(word in item.lower() for word in ['critical', 'major', 'senior', 'expert', 'years']):
                        severity = 'critical'
                    elif any(word in item.lower() for word in ['minor', 'small']):
                        severity = 'minor'

                    if any(word in item.lower() for word in ['degree', 'education', 'bachelor', 'master']):
                        category = 'education'
                    elif any(word in item.lower() for word in ['years', 'experience', 'senior', 'junior']):
                        category = 'experience'
                    elif any(word in item.lower() for word in ['communication', 'leadership', 'teamwork']):
                        category = 'soft-skills'

                    result.append({
                        'gap_category': category,
                        'gap_name': item,
                        'gap_description': item,
                        'severity': severity,
                        'severity_reason': f'Identified as {severity} gap',
                        'impact_on_hiring': f'This gap impacts hiring decision: {item}',
                        'can_be_filled': True,
                        'time_to_fill': '3-6 months' if severity == 'minor' else '6-12 months' if severity == 'moderate' else '12-24 months',
                        'fill_strategy': 'Training and on-the-job experience'
                    })
                elif isinstance(item, dict):
                    result.append(item)
                else:
                    result.append(item)
            return result
        return v if isinstance(v, list) else []

    weaknesses: List[str] = Field(default_factory=list, description="Top 3-5 candidate weaknesses")
    weaknesses_reason: str = Field(default="Weaknesses identified based on analysis", description="Why these are weaknesses")

    final_decision: MatchingDecision = Field(default_factory=MatchingDecision, description="Final matching decision")

    candidate_feedback: str = Field(default="Feedback provided based on evaluation", description="Feedback for candidate (2-3 paragraphs)")
    recruiter_notes: str = Field(default="Notes provided for recruiter", description="Notes for recruiter (2-3 paragraphs)")
    interview_focus_areas: List[str] = Field(default_factory=list, description="Areas to explore in interview")


# ============================================
# Tools
# ============================================

@tool
def extract_resume_text(pdf_path: str) -> str:
    """Extract full text from resume PDF.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Full resume text
    """
    try:
        return extract_pdf(pdf_path)
    except Exception as e:
        return f"Error extracting PDF: {str(e)}"


def load_jd_from_toon(toon_file_path: str) -> dict:
    """Load Job Description from TOON file.

    Args:
        toon_file_path: Path to TOON file

    Returns:
        Parsed JD data
    """
    try:
        with open(toon_file_path, 'r', encoding='utf-8') as f:
            toon_content = f.read()

        # Decode TOON to dict
        jd_data = toon_decode(toon_content)
        return jd_data
    except Exception as e:
        return {"error": f"Failed to load TOON file: {str(e)}"}


def get_langsmith_url(run_id: str, project_name: str) -> Optional[str]:
    """Generate LangSmith URL for a run."""
    try:
        if os.getenv('LANGSMITH_API_KEY') and os.getenv('LANGSMITH_TRACING') == 'true':
            return f"https://smith.langchain.com/o/projects/p/{project_name}/r/{run_id}"
    except:
        pass
    return None


# ============================================
# Main Pipeline 3 Function
# ============================================

def match_resume_to_jd(
    resume_pdf_path: str,
    jd_input: Union[str, dict],
    jd_source: str = "text",  # "text", "toon", or "dict"
    verbose: bool = True,
    enable_observability: bool = True
):
    """PIPELINE 3: Match resume directly to JD without GitHub dependency.

    Args:
        resume_pdf_path: Path to candidate's resume PDF
        jd_input: Job description (text string, TOON file path, or dict)
        jd_source: Source type - "text", "toon", or "dict"
        verbose: Print detailed output
        enable_observability: Enable execution tracking and logging

    Returns:
        Tuple of (ResumeJDMatch, toon_output, execution)
    """
    if verbose:
        print("\n" + "="*80)
        print("🎯 PIPELINE 3: Direct Resume-JD Matcher")
        print("="*80)
        print(f"📄 Resume: {resume_pdf_path}")
        print(f"📋 JD Source: {jd_source}")
        print()

    # Initialize observability
    execution_id = str(uuid.uuid4())
    execution = None
    tracker = None

    if enable_observability:
        from datetime import datetime
        execution = PipelineExecution(
            execution_id=execution_id,
            pipeline_name="pipeline3_resume_jd_matcher",
            repository_type="local",  # Using 'local' for resume files
            repository_path=resume_pdf_path,
            job_title="JD Matching",  # Will be updated after parsing JD
            start_time=datetime.now()
        )
        tracker = StepTracker(execution)


        if enable_observability:
            print(f"🔍 Execution ID: {execution_id}")

    try:
        # STEP 1: Parse JD based on source
        if jd_source == "toon":
            if verbose:
                print(f"📦 Loading JD from TOON file: {jd_input}")
            jd_data = load_jd_from_toon(jd_input)
            if "error" in jd_data:
                raise ValueError(f"Failed to load TOON: {jd_data['error']}")
            jd_text = json.dumps(jd_data, indent=2)
            jd_title = jd_data.get('job_title', 'Unknown Position')
        elif jd_source == "dict":
            jd_data = jd_input
            jd_text = json.dumps(jd_data, indent=2)
            jd_title = jd_data.get('job_title', 'Unknown Position')
        else:  # text
            jd_text = jd_input
            jd_title = "Position from JD"  # Will be extracted by LLM

        # Update execution with actual job title
        if tracker and jd_title:
            execution.job_title = jd_title

        # STEP 2: Initialize LLM and Agent
        if tracker:
            with tracker.track_step(
                StepType.INITIALIZATION,
                "Initialize LLM and Agent",
                input_data={"model": "claude-3-5-sonnet"},
                reason="Create agent with resume extraction tool"
            ):
                llm = get_chat_model("claude-3-5-sonnet")
                agent = create_react_agent(
                    llm,
                    tools=[extract_resume_text],
                    response_format=ResumeJDMatch
                )
                tracker.update_output({
                    "tools_loaded": ["extract_resume_text"],
                    "tool_count": 1,
                    "response_format": "ResumeJDMatch"
                })
        else:
            llm = get_chat_model("claude-3-5-sonnet")
            agent = create_react_agent(
                llm,
                tools=[extract_resume_text],
                response_format=ResumeJDMatch
            )

        # Build comprehensive prompt
        prompt = f"""Perform COMPLETE Resume-JD matching analysis WITHOUT GitHub dependency.

JOB DESCRIPTION:
{jd_text}

RESUME PDF PATH: {resume_pdf_path}

EVALUATION PROCESS (ALL FIELDS REQUIRED WITH REASONS):

STEP 1: EXTRACT RESUME
- Use extract_resume_text to get full resume content
- Parse: name, education, work experience, skills, certifications, achievements

STEP 2: EDUCATION MATCHING
education_match:
  required_degree: STRING - Degree required by JD
  candidate_degree: STRING - Candidate's degree
  degree_match: BOOLEAN - Does degree level match (BS vs MS vs PhD)
  degree_match_reason: STRING - Why it matches or not

  required_field: STRING - Field of study required (CS, Engineering, etc.)
  candidate_field: STRING - Candidate's field
  field_match: BOOLEAN - Does field match or is it relevant
  field_match_reason: STRING - Why field matches or not

  certifications: LIST - All relevant certifications (AWS, GCP, PMP, etc.)
  certifications_reason: STRING - How certifications add value

  education_score: INTEGER 1-100
  education_score_reason: STRING - Why this score

STEP 3: EXPERIENCE MATCHING
experience_match:
  required_years: INTEGER - Years required by JD
  candidate_years: INTEGER - Candidate's total experience
  years_match: BOOLEAN - Meets requirement
  years_match_reason: STRING - Why matches or not

  relevant_roles: LIST - Job titles that match JD requirements
  relevant_roles_reason: STRING - Why these roles are relevant

  industry_match: BOOLEAN - Has industry experience
  industry_match_reason: STRING - Industry alignment

  seniority_level: STRING - junior/mid-level/senior/expert
  seniority_match: BOOLEAN - Level matches JD
  seniority_reason: STRING - Why seniority matches or not

  career_progression: STRING - Describe growth pattern (promotions, increasing responsibility)
  career_progression_score: INTEGER 1-100
  career_progression_reason: STRING - Why this score

  experience_score: INTEGER 1-100
  experience_score_reason: STRING - Why this score

STEP 4: TECHNICAL SKILLS ANALYSIS
For EVERY technical skill in JD, create a TechnicalSkillMatch:
  skill_name: STRING
  required_level: STRING - beginner/intermediate/advanced/expert
  has_skill: BOOLEAN
  candidate_level: STRING - their proficiency
  years_of_experience: INTEGER
  evidence: STRING - Where in resume (which job, project, section)
  match_quality: STRING - exact/close/partial/missing
  match_reason: STRING - Why this match quality
  importance: STRING - must-have or nice-to-have
  gap_severity: STRING - If missing: critical/moderate/minor

technical_skills:
  programming_languages: LIST of TechnicalSkillMatch
  frameworks_libraries: LIST of TechnicalSkillMatch
  tools_platforms: LIST of TechnicalSkillMatch
  databases: LIST of TechnicalSkillMatch
  other_technical: LIST of TechnicalSkillMatch

  total_skills_required: INTEGER
  skills_matched: INTEGER
  skills_missing: INTEGER

  must_have_matched: INTEGER
  must_have_total: INTEGER
  must_have_percentage: FLOAT

  technical_skills_score: INTEGER 1-100
  technical_skills_reason: STRING - Why this score

STEP 5: SOFT SKILLS ANALYSIS
soft_skills:
  communication_skills: BOOLEAN
  communication_evidence: STRING - Where demonstrated

  leadership_skills: BOOLEAN
  leadership_evidence: STRING - Examples from resume

  team_collaboration: BOOLEAN
  team_evidence: STRING - Team projects, collaboration

  problem_solving: BOOLEAN
  problem_solving_evidence: STRING - Examples

  other_qualifications: LIST - Other relevant qualifications from JD
  other_qualifications_reason: STRING - Why they matter

  soft_skills_score: INTEGER 1-100
  soft_skills_reason: STRING - Why this score

STEP 6: GAP ANALYSIS
For EVERY gap (education, experience, technical, soft skills):
gaps: LIST of GapAnalysis
  Each: {{
    gap_category: STRING - education/experience/technical/soft-skills
    gap_name: STRING
    gap_description: STRING - Detailed description
    severity: STRING - critical/moderate/minor
    severity_reason: STRING - Why this severity
    impact_on_hiring: STRING - How this affects decision
    can_be_filled: BOOLEAN
    time_to_fill: STRING - e.g., "3-6 months with training"
    fill_strategy: STRING - How to address this gap
  }}

gaps_summary: STRING - Overall impact of all gaps

STEP 7: STRENGTHS & WEAKNESSES
strengths: LIST - Top 5-7 strengths specific to this JD
strengths_reason: STRING - Why these are top strengths

weaknesses: LIST - Top 3-5 weaknesses
weaknesses_reason: STRING - Why these are weaknesses

STEP 8: FINAL DECISION (MOST CRITICAL)
final_decision:
  is_match: BOOLEAN - Overall match yes/no
  match_reason: STRING - COMPREHENSIVE reason (must reference education, experience, technical, soft skills, gaps)

  overall_match_score: INTEGER 1-100
  score_breakdown: STRING - How calculated

  education_weight: FLOAT - Default 0.20
  experience_weight: FLOAT - Default 0.30
  technical_weight: FLOAT - Default 0.35
  soft_skills_weight: FLOAT - Default 0.15

  weighted_score: FLOAT - (education_score * education_weight) + ...
  weighted_calculation: STRING - Show formula

  recommendation: STRING - strong-match/good-match/partial-match/no-match
  recommendation_reason: STRING - Why this level

  proceed_to_interview: BOOLEAN
  interview_reason: STRING - Why proceed or not

  confidence_level: INTEGER 1-100
  confidence_reason: STRING - Why this confidence

candidate_feedback: STRING - 2-3 paragraphs for candidate
recruiter_notes: STRING - 2-3 paragraphs for recruiter
interview_focus_areas: LIST - Areas to probe in interview

CRITICAL RULES:
1. EVERY field needs a reason/evidence
2. Be objective - don't inflate scores
3. List ALL gaps, even minor ones
4. Base analysis ONLY on resume content vs JD requirements
5. If information is missing from resume, note it as a gap
6. Compare required vs actual for every skill
7. Calculate weighted score accurately
8. Provide actionable interview focus areas

Return complete analysis with all reasoning."""

        # STEP 3: Agent Matching with LangSmith tracing
        try:
            from langsmith import uuid7
            run_id = str(uuid7())
        except ImportError:
            run_id = str(uuid.uuid4())

        if tracker:
            execution.langsmith_run_id = run_id
            langsmith_project = "Synapse-Pipeline3"
            execution.langsmith_project = langsmith_project

            with tracker.track_step(
                StepType.AGENT_REASONING,
                "Agent Resume-JD Matching",
                input_data={
                    "resume_path": resume_pdf_path,
                    "jd_source": jd_source,
                    "prompt_length": len(prompt)
                },
                reason="Agent matches resume against job description requirements"
            ):
                if verbose:
                    print("🤖 Analyzing resume against JD requirements...\n")

                result = agent.invoke(
                    {"messages": [HumanMessage(content=prompt)]},
                    {"run_id": run_id, "project_name": langsmith_project, "tags": ["resume-jd-matching", "no-github"]}
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
                    "match_generated": True,
                    "is_match": data.final_decision.is_match,
                    "overall_score": data.final_decision.overall_match_score,
                    "recommendation": data.final_decision.recommendation,
                    "langsmith_run_id": run_id,
                    "tokens_used": tokens_used,
                    "cost_usd": round(cost_usd, 4) if cost_usd > 0 else 0
                })
        else:
            if verbose:
                print("🤖 Analyzing resume against JD requirements...\n")

            result = agent.invoke({
                "messages": [HumanMessage(content=prompt)]
            })
            data = result['structured_response']

        # STEP 4: Convert to TOON
        if tracker:
            with tracker.track_step(
                StepType.OUTPUT_GENERATION,
                "Generate TOON Output",
                input_data={"output_format": "TOON"},
                reason="Convert matching results to TOON format for storage"
            ):
                output_toon = toon_encode(data.model_dump())
                tracker.update_output({
                    "encoding": "TOON",
                    "size_bytes": len(output_toon)
                })
        else:
            output_toon = toon_encode(data.model_dump())

        if verbose:
            print_detailed_match_results(data)

        # Save TOON
        output_file = f"{data.candidate_name.replace(' ', '_')}_match.toon"
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


def print_detailed_match_results(data: ResumeJDMatch):
    """Print detailed matching results."""
    print("="*80)
    print("✅ RESUME-JD MATCHING COMPLETE")
    print("="*80)

    print(f"\n👤 Candidate: {data.candidate_name}")
    print(f"💼 Position: {data.job_title}")

    # FINAL DECISION (Most Important)
    print(f"\n\n{'='*80}")
    print("🎯 FINAL DECISION")
    print(f"{'='*80}")

    match_status = "✅ MATCH" if data.final_decision.is_match else "❌ NO MATCH"
    print(f"\n{match_status}")
    print(f"Overall Score: {data.final_decision.overall_match_score}/100")
    print(f"Weighted Score: {data.final_decision.weighted_score:.2f}/100")
    print(f"Recommendation: {data.final_decision.recommendation.upper()}")
    print(f"Interview: {'YES' if data.final_decision.proceed_to_interview else 'NO'}")
    print(f"Confidence: {data.final_decision.confidence_level}%")

    print(f"\n💡 Match Reason:")
    print(f"   {data.final_decision.match_reason}")

    print(f"\n📊 Score Breakdown:")
    print(f"   {data.final_decision.score_breakdown}")

    print(f"\n⚖️  Weighted Calculation:")
    print(f"   {data.final_decision.weighted_calculation}")

    print(f"\n💡 Interview Decision:")
    print(f"   {data.final_decision.interview_reason}")

    # Education Match
    print(f"\n\n🎓 EDUCATION MATCH:")
    print("-"*80)
    print(f"Required: {data.education_match.required_degree}" +
          (f" in {data.education_match.required_field}" if data.education_match.required_field else ""))
    print(f"Candidate: {data.education_match.candidate_degree}" +
          (f" in {data.education_match.candidate_field}" if data.education_match.candidate_field else ""))
    print(f"Degree Match: {'✓' if data.education_match.degree_match else '✗'}")
    print(f"💡 {data.education_match.degree_match_reason}")
    print(f"Field Match: {'✓' if data.education_match.field_match else '✗'}")
    print(f"💡 {data.education_match.field_match_reason}")

    if data.education_match.certifications:
        print(f"\nCertifications: {', '.join(data.education_match.certifications)}")
        print(f"💡 {data.education_match.certifications_reason}")

    print(f"\nEducation Score: {data.education_match.education_score}/100")
    print(f"💡 {data.education_match.education_score_reason}")

    # Experience Match
    print(f"\n\n⏱️  EXPERIENCE MATCH:")
    print("-"*80)
    print(f"Required: {data.experience_match.required_years}+ years")
    print(f"Candidate: {data.experience_match.candidate_years} years")
    print(f"Years Match: {'✓' if data.experience_match.years_match else '✗'}")
    print(f"💡 {data.experience_match.years_match_reason}")

    print(f"\nRelevant Roles:")
    for role in data.experience_match.relevant_roles:
        print(f"   • {role}")
    print(f"💡 {data.experience_match.relevant_roles_reason}")

    print(f"\nSeniority: {data.experience_match.seniority_level}")
    print(f"Seniority Match: {'✓' if data.experience_match.seniority_match else '✗'}")
    print(f"💡 {data.experience_match.seniority_reason}")

    print(f"\nCareer Progression: {data.experience_match.career_progression}")
    print(f"Progression Score: {data.experience_match.career_progression_score}/100")
    print(f"💡 {data.experience_match.career_progression_reason}")

    print(f"\nExperience Score: {data.experience_match.experience_score}/100")
    print(f"💡 {data.experience_match.experience_score_reason}")

    # Technical Skills
    print(f"\n\n💻 TECHNICAL SKILLS ANALYSIS:")
    print("-"*80)
    print(f"Skills Required: {data.technical_skills.total_skills_required}")
    print(f"Skills Matched: {data.technical_skills.skills_matched}")
    print(f"Skills Missing: {data.technical_skills.skills_missing}")
    print(f"Must-Have Match: {data.technical_skills.must_have_matched}/{data.technical_skills.must_have_total} ({data.technical_skills.must_have_percentage:.1f}%)")

    # Show all skill categories
    skill_categories = [
        ("Programming Languages", data.technical_skills.programming_languages),
        ("Frameworks/Libraries", data.technical_skills.frameworks_libraries),
        ("Tools/Platforms", data.technical_skills.tools_platforms),
        ("Databases", data.technical_skills.databases),
        ("Other Technical", data.technical_skills.other_technical)
    ]

    for category_name, skills in skill_categories:
        if skills:
            print(f"\n🔹 {category_name}:")
            for skill in skills:
                status = "✓" if skill.has_skill else "✗"
                match_icon = {"exact": "🟢", "close": "🟡", "partial": "🟠", "missing": "🔴"}.get(skill.match_quality, "⚪")
                print(f"   {status} {match_icon} {skill.skill_name} [{skill.importance}]")
                print(f"      Required: {skill.required_level} | Candidate: {skill.candidate_level}")
                print(f"      Evidence: {skill.evidence}")
                print(f"      💡 {skill.match_reason}")
                if skill.gap_severity:
                    print(f"      ⚠️  Gap Severity: {skill.gap_severity}")

    print(f"\nTechnical Skills Score: {data.technical_skills.technical_skills_score}/100")
    print(f"💡 {data.technical_skills.technical_skills_reason}")

    # Soft Skills
    print(f"\n\n🤝 SOFT SKILLS ANALYSIS:")
    print("-"*80)
    print(f"Communication: {'✓' if data.soft_skills.communication_skills else '✗'}")
    if data.soft_skills.communication_evidence:
        print(f"   {data.soft_skills.communication_evidence}")

    print(f"\nLeadership: {'✓' if data.soft_skills.leadership_skills else '✗'}")
    if data.soft_skills.leadership_evidence:
        print(f"   {data.soft_skills.leadership_evidence}")

    print(f"\nTeam Collaboration: {'✓' if data.soft_skills.team_collaboration else '✗'}")
    if data.soft_skills.team_evidence:
        print(f"   {data.soft_skills.team_evidence}")

    print(f"\nProblem Solving: {'✓' if data.soft_skills.problem_solving else '✗'}")
    if data.soft_skills.problem_solving_evidence:
        print(f"   {data.soft_skills.problem_solving_evidence}")

    if data.soft_skills.other_qualifications:
        print(f"\nOther Qualifications:")
        for qual in data.soft_skills.other_qualifications:
            print(f"   • {qual}")
        print(f"💡 {data.soft_skills.other_qualifications_reason}")

    print(f"\nSoft Skills Score: {data.soft_skills.soft_skills_score}/100")
    print(f"💡 {data.soft_skills.soft_skills_reason}")

    # Gaps
    if data.gaps:
        print(f"\n\n⚠️  GAP ANALYSIS:")
        print("-"*80)

        # Group by category
        gaps_by_category = {}
        for gap in data.gaps:
            if gap.gap_category not in gaps_by_category:
                gaps_by_category[gap.gap_category] = []
            gaps_by_category[gap.gap_category].append(gap)

        for category, gaps in gaps_by_category.items():
            print(f"\n📂 {category.upper()}:")
            for gap in gaps:
                severity_icon = {"critical": "🔴", "moderate": "🟡", "minor": "🟢"}.get(gap.severity, "⚪")
                print(f"\n   {severity_icon} {gap.gap_name} [{gap.severity.upper()}]")
                print(f"      {gap.gap_description}")
                print(f"      💡 {gap.severity_reason}")
                print(f"      Impact: {gap.impact_on_hiring}")
                print(f"      Can be filled: {'Yes' if gap.can_be_filled else 'No'}")
                if gap.time_to_fill:
                    print(f"      Time to fill: {gap.time_to_fill}")
                if gap.fill_strategy:
                    print(f"      Strategy: {gap.fill_strategy}")

        print(f"\n💡 Gaps Summary:")
        print(f"   {data.gaps_summary}")

    # Strengths
    print(f"\n\n💪 STRENGTHS:")
    print("-"*80)
    for i, strength in enumerate(data.strengths, 1):
        print(f"{i}. {strength}")
    print(f"\n💡 {data.strengths_reason}")

    # Weaknesses
    print(f"\n\n⚠️  WEAKNESSES:")
    print("-"*80)
    for i, weakness in enumerate(data.weaknesses, 1):
        print(f"{i}. {weakness}")
    print(f"\n💡 {data.weaknesses_reason}")

    # Interview Focus Areas
    if data.interview_focus_areas:
        print(f"\n\n🎤 INTERVIEW FOCUS AREAS:")
        print("-"*80)
        for i, area in enumerate(data.interview_focus_areas, 1):
            print(f"{i}. {area}")

    # Feedback
    print(f"\n\n📝 CANDIDATE FEEDBACK:")
    print("-"*80)
    print(data.candidate_feedback)

    print(f"\n\n📋 RECRUITER NOTES:")
    print("-"*80)
    print(data.recruiter_notes)


# ============================================
# Main
# ============================================

if __name__ == "__main__":
    # Example: Using TOON file from Pipeline 1
    jd_toon_path = "/Users/thiruanand/2025-hackaton/hackathon-2025/fastapi_fastapi_jd.toon"

    # Run matching
    match_result, toon, execution = match_resume_to_jd(
        resume_pdf_path="/Users/thiruanand/2025-hackaton/hackathon-2025/track_a_iron_man/Resume V20.pdf",
        jd_input=jd_toon_path,
        jd_source="toon",
        verbose=True
    )

    print(f"\n🎉 Pipeline 3 Complete!")
    print(f"   Candidate: {match_result.candidate_name}")
    print(f"   Match: {'YES' if match_result.final_decision.is_match else 'NO'}")
    print(f"   Score: {match_result.final_decision.overall_match_score}/100")
    print(f"   Weighted Score: {match_result.final_decision.weighted_score:.2f}/100")
    print(f"   Recommendation: {match_result.final_decision.recommendation}")
    print(f"   Interview: {'YES' if match_result.final_decision.proceed_to_interview else 'NO'}")

    if execution:
        print(f"\n📊 Execution Tracking:")
        print(f"   Execution ID: {execution.execution_id}")
        print(f"   Duration: {execution.total_duration_ms:.2f}ms")
        print(f"   Total Tokens: {execution.total_tokens}")
        print(f"   Total Cost: ${execution.total_cost_usd:.4f}")
        if execution.langsmith_url:
            print(f"   LangSmith: {execution.langsmith_url}")
