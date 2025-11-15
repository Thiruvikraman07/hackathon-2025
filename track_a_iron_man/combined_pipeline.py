"""
COMBINED PIPELINE: End-to-End Candidate Evaluation
Input: Company Repo + Job Title + Resume PDF + Optional Parameters
Output: Job Description + Complete Candidate Evaluation + Final Decision

This pipeline combines:
- Pipeline 1: JD Generator (from company repo)
- Pipeline 2: Candidate Evaluator (resume + GitHub analysis)
- Pipeline 3: Resume-JD Matcher (direct comparison without GitHub dependency)
- Final Decision: Weighted combination of all evaluations

Features:
- Testing mode with caching to avoid repeated API calls
- Complete evaluation with all reasoning fields
- TOON format outputs for all pipelines
- Comprehensive final decision with detailed reasoning
"""

import sys
import json
from pathlib import Path
from typing import List, Optional, Tuple, Dict
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Add core to path for react_agent imports (relative to project root)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'core'))

# Import all three pipelines
from pipeline1_jd_generator import generate_jd, JobDescription
from pipeline2_candidate_evaluator import evaluate_candidate, CandidateEvaluation
from pipeline3_resume_jd_matcher import match_resume_to_jd, ResumeJDMatch

# Import TOON encoder
from toon import encode as toon_encode

# Load environment variables
env_path = Path('.env')
if env_path.exists():
    load_dotenv(env_path)


# ============================================
# Final Decision Schema
# ============================================

class FinalCombinedDecision(BaseModel):
    """Final decision combining all three pipelines"""
    # Candidate Info
    candidate_name: str = Field(description="Candidate name")
    job_title: str = Field(description="Job title")
    company_repo: str = Field(description="Company repository")

    # Individual Pipeline Scores
    pipeline2_score: int = Field(description="Pipeline 2 (GitHub) score 1-100")
    pipeline2_has_github: bool = Field(description="Does candidate have GitHub")
    pipeline2_weight: float = Field(description="Weight given to Pipeline 2")

    pipeline3_score: int = Field(description="Pipeline 3 (Resume-JD) score 1-100")
    pipeline3_weight: float = Field(description="Weight given to Pipeline 3")

    # Combined Score
    final_score: int = Field(description="Final weighted score 1-100")
    score_calculation: str = Field(description="How final score was calculated")

    # Final Decision
    is_hire: bool = Field(description="Should we hire this candidate")
    decision_category: str = Field(description="strong-hire, hire, maybe, or no-hire")
    proceed_to_interview: bool = Field(description="Should proceed to interview")

    # Detailed Reasoning
    decision_reason: str = Field(description="Comprehensive reason for the decision")
    why_hire_or_not: str = Field(description="Clear explanation of hire/no-hire decision")

    # Key Findings
    top_strengths: List[str] = Field(description="Top 5 strengths across all evaluations")
    critical_gaps: List[str] = Field(description="Critical gaps that impact hiring")

    # Scores Breakdown
    education_score: int = Field(description="Education score from Pipeline 3")
    experience_score: int = Field(description="Experience score from Pipeline 3")
    technical_skills_score: int = Field(description="Technical skills score")
    github_contribution_score: int = Field(description="GitHub contribution score from Pipeline 2")

    # Recommendations
    hiring_recommendation: str = Field(description="Recommendation for hiring manager")
    suggestions_for_candidate: Optional[str] = Field(default=None, description="Suggestions if rejected")
    alternative_roles: List[str] = Field(default_factory=list, description="Alternative roles candidate might fit")

    # Confidence
    confidence_level: int = Field(description="Confidence in decision 1-100")
    confidence_reason: str = Field(description="Why this confidence level")


def make_final_decision(
    jd: JobDescription,
    pipeline2_eval: CandidateEvaluation,
    pipeline3_match: ResumeJDMatch,
    verbose: bool = True
) -> FinalCombinedDecision:
    """
    Create final hiring decision by combining Pipeline 2 and Pipeline 3 results.

    Args:
        jd: Job description from Pipeline 1
        pipeline2_eval: Evaluation from Pipeline 2 (with GitHub)
        pipeline3_match: Match from Pipeline 3 (Resume-JD direct)
        verbose: Print decision process

    Returns:
        Final combined decision
    """
    if verbose:
        print("\n" + "="*80)
        print("📊 MAKING FINAL DECISION")
        print("="*80)

    # Determine weights based on GitHub availability
    has_github = pipeline2_eval.github_analysis.has_github

    if has_github:
        # GitHub available - weight both pipelines
        p2_weight = 0.6  # GitHub analysis more important
        p3_weight = 0.4  # Resume analysis as backup
        if verbose:
            print(f"✓ GitHub profile found: Using weighted combination (60% P2 + 40% P3)")
    else:
        # No GitHub - rely more on Pipeline 3
        p2_weight = 0.3  # Resume analysis from P2
        p3_weight = 0.7  # Direct resume-JD matching more important
        if verbose:
            print(f"✗ No GitHub profile: Relying on resume analysis (30% P2 + 70% P3)")

    # Get scores
    p2_score = pipeline2_eval.final_decision.overall_score
    p3_score = pipeline3_match.final_decision.overall_match_score

    # Calculate weighted final score
    final_score = int(p2_score * p2_weight + p3_score * p3_weight)
    score_calculation = f"({p2_score} × {p2_weight:.1f}) + ({p3_score} × {p3_weight:.1f}) = {final_score}"

    if verbose:
        print(f"\n📊 Score Calculation:")
        print(f"   Pipeline 2 (GitHub): {p2_score}/100 × {p2_weight:.1f} = {p2_score * p2_weight:.1f}")
        print(f"   Pipeline 3 (Resume): {p3_score}/100 × {p3_weight:.1f} = {p3_score * p3_weight:.1f}")
        print(f"   Final Score: {final_score}/100")

    # Determine decision category
    if final_score >= 80:
        decision_category = "strong-hire"
        is_hire = True
        proceed_to_interview = True
    elif final_score >= 65:
        decision_category = "hire"
        is_hire = True
        proceed_to_interview = True
    elif final_score >= 50:
        decision_category = "maybe"
        is_hire = False
        proceed_to_interview = True
    else:
        decision_category = "no-hire"
        is_hire = False
        proceed_to_interview = False

    # Combine strengths from both pipelines
    strengths_set = set()
    strengths_set.update(pipeline2_eval.strengths[:3])
    strengths_set.update(pipeline3_match.strengths[:3])
    top_strengths = list(strengths_set)[:5]

    # Combine critical gaps
    critical_gaps = []
    # From Pipeline 2
    p2_critical = [g.gap_name for g in pipeline2_eval.skill_gaps if g.severity == 'critical']
    critical_gaps.extend(p2_critical[:3])
    # From Pipeline 3
    p3_critical = [g.gap_name for g in pipeline3_match.gaps if g.severity == 'critical']
    for gap in p3_critical:
        if gap not in critical_gaps:
            critical_gaps.append(gap)
    critical_gaps = critical_gaps[:5]

    # Build comprehensive decision reason with detailed explanations
    decision_reason_parts = []

    if is_hire:
        decision_reason_parts.append(f"HIRE DECISION: Candidate scores {final_score}/100 overall.")
        decision_reason_parts.append(f"Pipeline 2 (GitHub analysis): {p2_score}/100 - {pipeline2_eval.final_decision.fit_reason}")
        decision_reason_parts.append(f"Pipeline 3 (Resume-JD match): {p3_score}/100 - {pipeline3_match.final_decision.match_reason}")

        # Add education reasoning
        decision_reason_parts.append(f"\nEDUCATION ({pipeline3_match.education_match.education_score}/100):")
        decision_reason_parts.append(f"- Degree: {pipeline3_match.education_match.candidate_degree}")
        decision_reason_parts.append(f"- {pipeline3_match.education_match.education_score_reason}")

        # Add experience reasoning
        decision_reason_parts.append(f"\nEXPERIENCE ({pipeline3_match.experience_match.experience_score}/100):")
        decision_reason_parts.append(f"- Years: {pipeline3_match.experience_match.candidate_years} (required: {pipeline3_match.experience_match.required_years}+)")
        decision_reason_parts.append(f"- {pipeline3_match.experience_match.experience_score_reason}")

        # Add technical skills reasoning
        decision_reason_parts.append(f"\nTECHNICAL SKILLS ({pipeline3_match.technical_skills.technical_skills_score}/100):")
        decision_reason_parts.append(f"- {pipeline3_match.technical_skills.technical_skills_reason}")

        # Add GitHub reasoning if available
        if has_github:
            decision_reason_parts.append(f"\nGITHUB CONTRIBUTIONS ({pipeline2_eval.github_analysis.github_contribution_score}/100):")
            decision_reason_parts.append(f"- {pipeline2_eval.github_analysis.github_score_reason}")

        why_hire = f"The candidate demonstrates strong qualifications for this {jd.job_title} role. "
        if has_github and pipeline2_eval.github_analysis.github_contribution_score > 60:
            why_hire += f"GitHub profile shows solid contribution history ({pipeline2_eval.github_analysis.github_contribution_score}/100). "
        why_hire += f"Resume analysis shows {len(top_strengths)} key strengths aligned with job requirements."

        if critical_gaps:
            why_hire += f" While there are {len(critical_gaps)} gaps identified, they are manageable through training and onboarding."
    else:
        decision_reason_parts.append(f"NO-HIRE DECISION: Candidate scores {final_score}/100 overall, below hiring threshold.")
        decision_reason_parts.append(f"Pipeline 2 (GitHub analysis): {p2_score}/100 - {pipeline2_eval.final_decision.fit_reason}")
        decision_reason_parts.append(f"Pipeline 3 (Resume-JD match): {p3_score}/100 - {pipeline3_match.final_decision.match_reason}")

        # Add detailed score breakdowns with reasons
        decision_reason_parts.append(f"\nDETAILED ANALYSIS:")

        # Education
        decision_reason_parts.append(f"\n1. EDUCATION ({pipeline3_match.education_match.education_score}/100):")
        decision_reason_parts.append(f"   Degree: {pipeline3_match.education_match.candidate_degree}")
        decision_reason_parts.append(f"   Match: {'✓' if pipeline3_match.education_match.degree_match else '✗'}")
        decision_reason_parts.append(f"   Reason: {pipeline3_match.education_match.degree_match_reason}")
        decision_reason_parts.append(f"   Score Reason: {pipeline3_match.education_match.education_score_reason}")

        # Experience
        decision_reason_parts.append(f"\n2. EXPERIENCE ({pipeline3_match.experience_match.experience_score}/100):")
        decision_reason_parts.append(f"   Required: {pipeline3_match.experience_match.required_years}+ years ({jd.experience_requirement.level})")
        decision_reason_parts.append(f"   Candidate: {pipeline3_match.experience_match.candidate_years} years ({pipeline3_match.experience_match.seniority_level})")
        decision_reason_parts.append(f"   Match: {'✓' if pipeline3_match.experience_match.years_match else '✗'}")
        decision_reason_parts.append(f"   Reason: {pipeline3_match.experience_match.years_match_reason}")
        decision_reason_parts.append(f"   Score Reason: {pipeline3_match.experience_match.experience_score_reason}")
        if pipeline3_match.experience_match.required_years > pipeline3_match.experience_match.candidate_years:
            years_gap = pipeline3_match.experience_match.required_years - pipeline3_match.experience_match.candidate_years
            decision_reason_parts.append(f"   ⚠️ GAP: {years_gap} years below requirement")

        # Technical Skills
        decision_reason_parts.append(f"\n3. TECHNICAL SKILLS ({pipeline3_match.technical_skills.technical_skills_score}/100):")
        decision_reason_parts.append(f"   Total Required: {pipeline3_match.technical_skills.total_skills_required}")
        decision_reason_parts.append(f"   Matched: {pipeline3_match.technical_skills.skills_matched}")
        decision_reason_parts.append(f"   Missing: {pipeline3_match.technical_skills.skills_missing}")
        decision_reason_parts.append(f"   Must-Have Match: {pipeline3_match.technical_skills.must_have_matched}/{pipeline3_match.technical_skills.must_have_total} ({pipeline3_match.technical_skills.must_have_percentage:.0f}%)")
        decision_reason_parts.append(f"   Reason: {pipeline3_match.technical_skills.technical_skills_reason}")

        # GitHub (if available)
        if has_github:
            decision_reason_parts.append(f"\n4. GITHUB CONTRIBUTIONS ({pipeline2_eval.github_analysis.github_contribution_score}/100):")
            decision_reason_parts.append(f"   Projects Found: {pipeline2_eval.github_analysis.projects_found}")
            decision_reason_parts.append(f"   Relevant Projects: {len(pipeline2_eval.github_analysis.relevant_projects)}")
            decision_reason_parts.append(f"   Reason: {pipeline2_eval.github_analysis.github_score_reason}")
        else:
            decision_reason_parts.append(f"\n4. GITHUB: Not available")
            decision_reason_parts.append(f"   Reason: {pipeline2_eval.github_analysis.github_check_reason}")

        # Gaps Summary
        if critical_gaps:
            decision_reason_parts.append(f"\nCRITICAL GAPS IDENTIFIED:")
            for i, gap in enumerate(critical_gaps, 1):
                decision_reason_parts.append(f"   {i}. {gap}")
            decision_reason_parts.append(f"\nGaps Summary: {pipeline3_match.gaps_summary}")

        why_hire = f"The candidate does not meet the requirements for this {jd.job_title} role. "
        if critical_gaps:
            why_hire += f"Critical gaps identified: {', '.join(critical_gaps[:3])}. "

        # Check experience gap
        if pipeline3_match.experience_match.required_years > pipeline3_match.experience_match.candidate_years:
            years_gap = pipeline3_match.experience_match.required_years - pipeline3_match.experience_match.candidate_years
            why_hire += f"Experience gap: {years_gap} years below requirement. "

        # Check seniority mismatch
        if not pipeline3_match.experience_match.seniority_match:
            why_hire += f"Seniority level ({pipeline3_match.experience_match.seniority_level}) does not match requirement ({jd.experience_requirement.level}). "

    decision_reason = "\n".join(decision_reason_parts)

    # Suggestions for candidate if rejected
    suggestions = None
    alternative_roles = []

    if not is_hire:
        suggestion_parts = []

        # Experience suggestions
        if pipeline3_match.experience_match.candidate_years < pipeline3_match.experience_match.required_years:
            years_needed = pipeline3_match.experience_match.required_years - pipeline3_match.experience_match.candidate_years
            suggestion_parts.append(f"Gain {years_needed}+ more years of relevant experience")

        # Technical skills suggestions
        if pipeline3_match.technical_skills.skills_missing > 0:
            missing_count = min(3, len(pipeline3_match.technical_skills.programming_languages) +
                              len(pipeline3_match.technical_skills.frameworks_libraries))
            if missing_count > 0:
                suggestion_parts.append(f"Develop skills in missing technologies (see critical gaps)")

        # GitHub suggestions
        if not has_github:
            suggestion_parts.append("Build a GitHub profile with relevant projects to demonstrate technical skills")
        elif pipeline2_eval.github_analysis.github_contribution_score < 40:
            suggestion_parts.append("Increase GitHub contributions and build more substantial projects")

        # Education suggestions
        if not pipeline3_match.education_match.degree_match:
            suggestion_parts.append("Complete formal education degree if still in progress")

        suggestions = ". ".join(suggestion_parts) + "." if suggestion_parts else None

        # Suggest alternative roles
        if pipeline3_match.experience_match.seniority_level == "junior":
            alternative_roles = ["Junior Developer", "Associate Engineer", "Entry-level positions"]
        elif pipeline3_match.experience_match.seniority_level == "mid-level":
            alternative_roles = ["Mid-level Developer", "Software Engineer II", "Intermediate positions"]

    # Hiring recommendation
    if is_hire:
        hiring_recommendation = f"RECOMMENDED FOR HIRE. Proceed with interview process. "
        hiring_recommendation += f"Focus interview on: {', '.join(pipeline3_match.interview_focus_areas[:3])}."
    else:
        hiring_recommendation = f"NOT RECOMMENDED FOR HIRE at this time. "
        if decision_category == "maybe":
            hiring_recommendation += f"Consider for interview if no better candidates available. "
        hiring_recommendation += f"Candidate may be better suited for {alternative_roles[0] if alternative_roles else 'junior roles'}."

    # Confidence level
    confidence = final_score if is_hire else (100 - final_score)
    confidence = min(95, max(60, confidence))  # Cap between 60-95%

    confidence_reason = f"Based on comprehensive analysis across {2 if has_github else 1} evaluation pipelines. "
    if has_github:
        confidence_reason += "GitHub analysis provides additional validation of technical skills. "
    else:
        confidence_reason += "Limited to resume analysis due to missing GitHub profile. "

    return FinalCombinedDecision(
        candidate_name=pipeline2_eval.candidate_name,
        job_title=jd.job_title,
        company_repo=jd.company_repo,
        pipeline2_score=p2_score,
        pipeline2_has_github=has_github,
        pipeline2_weight=p2_weight,
        pipeline3_score=p3_score,
        pipeline3_weight=p3_weight,
        final_score=final_score,
        score_calculation=score_calculation,
        is_hire=is_hire,
        decision_category=decision_category,
        proceed_to_interview=proceed_to_interview,
        decision_reason=decision_reason,
        why_hire_or_not=why_hire,
        top_strengths=top_strengths,
        critical_gaps=critical_gaps,
        education_score=pipeline3_match.education_match.education_score,
        experience_score=pipeline3_match.experience_match.experience_score,
        technical_skills_score=pipeline3_match.technical_skills.technical_skills_score,
        github_contribution_score=pipeline2_eval.github_analysis.github_contribution_score,
        hiring_recommendation=hiring_recommendation,
        suggestions_for_candidate=suggestions,
        alternative_roles=alternative_roles,
        confidence_level=confidence,
        confidence_reason=confidence_reason
    )


def combined_pipeline(
    company_repo: str,
    job_title: str,
    resume_pdf_path: str,
    salary_range: Optional[str] = None,
    additional_requirements: Optional[List[str]] = None,
    verbose: bool = True,
    testing: bool = False
) -> Tuple[JobDescription, str, CandidateEvaluation, str, ResumeJDMatch, str, FinalCombinedDecision, str]:
    """
    Combined Pipeline: Generate JD from repo and evaluate candidate with all three pipelines.

    Args:
        company_repo: Company repository (e.g., 'facebook/react')
        job_title: Job title (e.g., 'Senior Python Developer')
        resume_pdf_path: Path to candidate's resume PDF
        salary_range: Optional salary range (e.g., '$120k-$160k')
        additional_requirements: Optional additional requirements for JD
        verbose: Print detailed output
        testing: Enable caching mode for all pipelines

    Returns:
        Tuple of (JobDescription, jd_toon, CandidateEvaluation, eval_toon,
                  ResumeJDMatch, match_toon, FinalCombinedDecision, final_toon)
    """
    if verbose:
        print("\n" + "="*80)
        print("🎯 COMBINED PIPELINE: Complete Candidate Evaluation")
        print("="*80)
        print(f"📦 Company Repo: {company_repo}")
        print(f"💼 Job Title: {job_title}")
        print(f"📄 Resume: {resume_pdf_path}")
        if salary_range:
            print(f"💰 Salary: {salary_range}")
        if additional_requirements:
            print(f"📋 Additional Requirements: {len(additional_requirements)}")
        if testing:
            print(f"🧪 Testing Mode: ENABLED (caching data for all pipelines)")
        print("="*80)

    # ============================================
    # STEP 1: Generate Job Description
    # ============================================
    if verbose:
        print("\n" + "="*80)
        print("STEP 1: Generating Job Description from Repository")
        print("="*80)

    jd, jd_toon = generate_jd(
        company_repo=company_repo,
        job_title=job_title,
        salary_range=salary_range,
        additional_requirements=additional_requirements,
        verbose=verbose,
        testing=testing
    )

    if verbose:
        print("\n✅ Job Description Generated Successfully!")
        print(f"   - {len(jd.technical_requirements.primary_languages)} languages")
        print(f"   - {len(jd.responsibilities)} responsibilities")
        print(f"   - {len(jd.qualifications)} qualifications")
        print(f"   - Experience: {jd.experience_requirement.level} ({jd.experience_requirement.minimum_years}+ years)")

    # ============================================
    # STEP 2: Evaluate Candidate
    # ============================================
    if verbose:
        print("\n" + "="*80)
        print("STEP 2: Evaluating Candidate Against Job Description")
        print("="*80)

    # Create JD text from the generated JobDescription
    jd_text = format_jd_for_evaluation(jd)

    evaluation, eval_toon = evaluate_candidate(
        resume_pdf_path=resume_pdf_path,
        jd_text=jd_text,
        jd_job_title=job_title,
        verbose=verbose,
        testing=testing
    )

    # ============================================
    # STEP 3: Direct Resume-JD Matching
    # ============================================
    if verbose:
        print("\n" + "="*80)
        print("STEP 3: Direct Resume-JD Matching (No GitHub Dependency)")
        print("="*80)

    # Save JD to temp TOON file for Pipeline 3
    temp_jd_file = f"temp_{company_repo.replace('/', '_')}_jd.toon"
    with open(temp_jd_file, 'w') as f:
        f.write(jd_toon)

    match_result, match_toon = match_resume_to_jd(
        resume_pdf_path=resume_pdf_path,
        jd_input=temp_jd_file,
        jd_source="toon",
        verbose=verbose
    )

    # Clean up temp file
    Path(temp_jd_file).unlink(missing_ok=True)

    # ============================================
    # STEP 4: Make Final Combined Decision
    # ============================================
    final_decision = make_final_decision(
        jd=jd,
        pipeline2_eval=evaluation,
        pipeline3_match=match_result,
        verbose=verbose
    )

    # Convert final decision to TOON
    final_toon = toon_encode(final_decision.model_dump())

    # ============================================
    # FINAL SUMMARY
    # ============================================
    if verbose:
        print("\n" + "="*80)
        print("🎉 COMBINED PIPELINE COMPLETE - FINAL DECISION")
        print("="*80)

        print(f"\n👤 Candidate: {final_decision.candidate_name}")
        print(f"💼 Position: {final_decision.job_title}")
        print(f"🏢 Company: {final_decision.company_repo}")

        # Final Decision
        decision_icon = "✅ HIRE" if final_decision.is_hire else "❌ NO HIRE"
        print(f"\n{'='*80}")
        print(f"{decision_icon} - {final_decision.decision_category.upper()}")
        print(f"{'='*80}")

        print(f"\n🎯 Final Score: {final_decision.final_score}/100")
        print(f"   {final_decision.score_calculation}")

        print(f"\nInterview: {'YES' if final_decision.proceed_to_interview else 'NO'}")
        print(f"Confidence: {final_decision.confidence_level}%")

        print(f"\n💡 Why {'Hire' if final_decision.is_hire else 'Not Hire'}:")
        print(f"   {final_decision.why_hire_or_not}")

        print(f"\n📋 COMPLETE DECISION REASONING:")
        print("-"*80)
        # Print the detailed decision_reason which includes all scores and reasoning
        for line in final_decision.decision_reason.split('\n'):
            print(f"   {line}")

        # Score breakdown
        print(f"\n📊 Detailed Scores:")
        print(f"   Education: {final_decision.education_score}/100")
        print(f"   Experience: {final_decision.experience_score}/100")
        print(f"   Technical Skills: {final_decision.technical_skills_score}/100")
        print(f"   GitHub Contributions: {final_decision.github_contribution_score}/100")

        # Strengths
        print(f"\n💪 Top Strengths ({len(final_decision.top_strengths)}):")
        for strength in final_decision.top_strengths:
            print(f"   • {strength}")

        # Critical Gaps
        if final_decision.critical_gaps:
            print(f"\n🔴 Critical Gaps ({len(final_decision.critical_gaps)}):")
            for gap in final_decision.critical_gaps:
                print(f"   • {gap}")

        # Recommendations
        print(f"\n📋 Hiring Manager Recommendation:")
        print(f"   {final_decision.hiring_recommendation}")

        # Suggestions for candidate if not hired
        if not final_decision.is_hire and final_decision.suggestions_for_candidate:
            print(f"\n💡 Suggestions for Candidate:")
            print(f"   {final_decision.suggestions_for_candidate}")

        if final_decision.alternative_roles:
            print(f"\n🔄 Alternative Roles:")
            for role in final_decision.alternative_roles:
                print(f"   • {role}")

        # Files saved
        jd_file = f"{company_repo.replace('/', '_')}_jd.toon"
        eval_file = f"{evaluation.candidate_name.replace(' ', '_')}_evaluation.toon"
        match_file = f"{match_result.candidate_name.replace(' ', '_')}_match.toon"
        final_file = f"{final_decision.candidate_name.replace(' ', '_')}_final_decision.toon"

        print(f"\n💾 Output Files:")
        print(f"   • Job Description: {jd_file}")
        print(f"   • P2 Evaluation (GitHub): {eval_file}")
        print(f"   • P3 Match (Resume-JD): {match_file}")
        print(f"   • Final Decision: {final_file}")

        if testing:
            print(f"\n🧪 Cache: ./cache/github_data/")
            print(f"   Subsequent runs will use cached data")

    # Save final decision TOON
    final_output_file = f"{final_decision.candidate_name.replace(' ', '_')}_final_decision.toon"
    with open(final_output_file, 'w') as f:
        f.write(final_toon)

    return jd, jd_toon, evaluation, eval_toon, match_result, match_toon, final_decision, final_toon


def format_jd_for_evaluation(jd: JobDescription) -> str:
    """Convert JobDescription object to text format for candidate evaluation."""

    jd_lines = [
        f"Job Title: {jd.job_title}",
        f"",
        f"Overview:",
        f"{jd.overview}",
        f"",
        f"Technical Requirements:",
        ""
    ]

    # Languages
    jd_lines.append("Primary Languages:")
    for lang in jd.technical_requirements.primary_languages:
        jd_lines.append(f"  - {lang.name} [{lang.importance}]: {lang.reason}")
    jd_lines.append("")

    # Frameworks
    jd_lines.append("Frameworks & Libraries:")
    for fw in jd.technical_requirements.frameworks_libraries:
        jd_lines.append(f"  - {fw.name} [{fw.importance}]: {fw.reason}")
    jd_lines.append("")

    # Tools
    if jd.technical_requirements.tools_platforms:
        jd_lines.append("Tools & Platforms:")
        for tool in jd.technical_requirements.tools_platforms:
            jd_lines.append(f"  - {tool.name} [{tool.importance}]: {tool.reason}")
        jd_lines.append("")

    # Databases
    if jd.technical_requirements.databases:
        jd_lines.append("Databases:")
        for db in jd.technical_requirements.databases:
            jd_lines.append(f"  - {db.name} [{db.importance}]: {db.reason}")
        jd_lines.append("")

    # Responsibilities
    jd_lines.append("Key Responsibilities:")
    for i, resp in enumerate(jd.responsibilities, 1):
        jd_lines.append(f"  {i}. {resp.responsibility}")
    jd_lines.append("")

    # Qualifications
    jd_lines.append("Required Qualifications:")
    for qual in jd.qualifications:
        jd_lines.append(f"  - {qual.qualification} [{qual.importance}]")
    jd_lines.append("")

    # Experience
    jd_lines.append("Experience Requirements:")
    jd_lines.append(f"  Level: {jd.experience_requirement.level}")
    jd_lines.append(f"  Minimum Years: {jd.experience_requirement.minimum_years}+")
    jd_lines.append(f"  Reason: {jd.experience_requirement.reason}")
    jd_lines.append("")

    # Additional requirements
    if jd.additional_requirements:
        jd_lines.append("Additional Requirements:")
        for req in jd.additional_requirements:
            jd_lines.append(f"  - {req}")
        jd_lines.append("")

    # Salary
    if jd.salary_range:
        jd_lines.append(f"Salary Range: {jd.salary_range}")

    return "\n".join(jd_lines)


# ============================================
# Main
# ============================================

if __name__ == "__main__":
    # Example usage - Full end-to-end evaluation with all 3 pipelines

    results = combined_pipeline(
        company_repo="fastapi/fastapi",
        job_title="Senior Python Backend Developer",
        resume_pdf_path="/Users/thiruanand/2025-hackaton/hackathon-2025/track_a_iron_man/Resume V20.pdf",
        salary_range="$140k-$180k",
        additional_requirements=[
            "Experience with microservices architecture",
            "Strong communication skills for remote work",
            "Open source contribution experience"
        ],
        verbose=True,
        testing=True  # Enable caching for all pipelines
    )

    jd, jd_toon, evaluation, eval_toon, match_result, match_toon, final_decision, final_toon = results

    print("\n" + "="*80)
    print("🏁 ALL PIPELINES COMPLETE")
    print("="*80)

    print(f"\n📋 Job Description Generated:")
    print(f"   Title: {jd.job_title}")
    print(f"   Repo: {jd.company_repo}")
    print(f"   Experience: {jd.experience_requirement.level} ({jd.experience_requirement.minimum_years}+ years)")

    print(f"\n🔍 Pipelines Executed:")
    print(f"   ✓ Pipeline 1: JD Generation")
    print(f"   ✓ Pipeline 2: GitHub Evaluation (Score: {final_decision.pipeline2_score}/100)")
    print(f"   ✓ Pipeline 3: Resume-JD Match (Score: {final_decision.pipeline3_score}/100)")

    print(f"\n🎯 FINAL DECISION:")
    decision_symbol = "✅ HIRE" if final_decision.is_hire else "❌ NO HIRE"
    print(f"   {decision_symbol} - {final_decision.decision_category.upper()}")
    print(f"   Final Score: {final_decision.final_score}/100")
    print(f"   Confidence: {final_decision.confidence_level}%")

    print(f"\n💡 Why {'Hire' if final_decision.is_hire else 'Not Hire'}:")
    print(f"   {final_decision.why_hire_or_not}")

    if not final_decision.is_hire and final_decision.suggestions_for_candidate:
        print(f"\n📌 Suggestions for Improvement:")
        print(f"   {final_decision.suggestions_for_candidate}")

    print(f"\n📁 Output Files Generated:")
    print(f"   • {jd.company_repo.replace('/', '_')}_jd.toon")
    print(f"   • {evaluation.candidate_name.replace(' ', '_')}_evaluation.toon")
    print(f"   • {match_result.candidate_name.replace(' ', '_')}_match.toon")
    print(f"   • {final_decision.candidate_name.replace(' ', '_')}_final_decision.toon")
