"""
COMBINED PIPELINE: End-to-End Candidate Evaluation
Input: Company Repo + Job Title + Resume PDF + Optional Parameters
Output: Job Description + Complete Candidate Evaluation

This pipeline combines:
- Pipeline 1: JD Generator (from company repo)
- Pipeline 2: Candidate Evaluator (resume + GitHub analysis)

Features:
- Testing mode with caching to avoid repeated API calls
- Complete evaluation with all reasoning fields
- TOON format outputs for both JD and evaluation
"""

import sys
import json
from pathlib import Path
from typing import List, Optional, Tuple
from dotenv import load_dotenv

# Add core to path for react_agent imports (relative to project root)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'core'))

# Import both pipelines
from pipeline1_jd_generator import generate_jd, JobDescription
from pipeline2_candidate_evaluator import evaluate_candidate, CandidateEvaluation

# Load environment variables
env_path = Path('.env')
if env_path.exists():
    load_dotenv(env_path)


def combined_pipeline(
    company_repo: str,
    job_title: str,
    resume_pdf_path: str,
    salary_range: Optional[str] = None,
    additional_requirements: Optional[List[str]] = None,
    verbose: bool = True,
    testing: bool = False
) -> Tuple[JobDescription, str, CandidateEvaluation, str]:
    """
    Combined Pipeline: Generate JD from repo and evaluate candidate.

    Args:
        company_repo: Company repository (e.g., 'facebook/react')
        job_title: Job title (e.g., 'Senior Python Developer')
        resume_pdf_path: Path to candidate's resume PDF
        salary_range: Optional salary range (e.g., '$120k-$160k')
        additional_requirements: Optional additional requirements for JD
        verbose: Print detailed output
        testing: Enable caching mode for both pipelines

    Returns:
        Tuple of (JobDescription, jd_toon, CandidateEvaluation, eval_toon)
    """
    if verbose:
        print("\n" + "="*80)
        print("🎯 COMBINED PIPELINE: JD Generation + Candidate Evaluation")
        print("="*80)
        print(f"📦 Company Repo: {company_repo}")
        print(f"💼 Job Title: {job_title}")
        print(f"📄 Resume: {resume_pdf_path}")
        if salary_range:
            print(f"💰 Salary: {salary_range}")
        if additional_requirements:
            print(f"📋 Additional Requirements: {len(additional_requirements)}")
        if testing:
            print(f"🧪 Testing Mode: ENABLED (caching data for both pipelines)")
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
    # FINAL SUMMARY
    # ============================================
    if verbose:
        print("\n" + "="*80)
        print("🎉 COMBINED PIPELINE COMPLETE")
        print("="*80)

        print("\n📊 SUMMARY:")
        print("-"*80)
        print(f"Job Title: {jd.job_title}")
        print(f"Company Repo: {jd.company_repo}")
        print(f"Candidate: {evaluation.candidate_name}")

        # Decision
        fit_status = "✅ FIT" if evaluation.final_decision.is_fit else "❌ NOT FIT"
        print(f"\n{fit_status}")
        print(f"Overall Score: {evaluation.final_decision.overall_score}/100")
        print(f"Recommendation: {evaluation.final_decision.recommendation.upper()}")
        print(f"Confidence: {evaluation.final_decision.confidence_level}%")

        # Quick stats
        print(f"\nResume Score: {evaluation.final_decision.resume_score}/100")
        print(f"GitHub Score: {evaluation.final_decision.github_score}/100")
        print(f"Skill Match Score: {evaluation.final_decision.skill_match_score}/100")

        # Key insights
        print(f"\n📌 Key Strengths ({len(evaluation.strengths)}):")
        for strength in evaluation.strengths[:3]:  # Show top 3
            print(f"   • {strength}")

        if evaluation.skill_gaps:
            print(f"\n⚠️  Critical Gaps ({len([g for g in evaluation.skill_gaps if g.severity == 'critical'])}):")
            critical_gaps = [g for g in evaluation.skill_gaps if g.severity == 'critical']
            for gap in critical_gaps[:3]:  # Show top 3 critical
                print(f"   • {gap.gap_name}")

        # Files saved
        jd_file = f"{company_repo.replace('/', '_')}_jd.toon"
        eval_file = f"{evaluation.candidate_name.replace(' ', '_')}_evaluation.toon"
        print(f"\n💾 Output Files:")
        print(f"   • Job Description: {jd_file} ({len(jd_toon)} chars)")
        print(f"   • Evaluation: {eval_file} ({len(eval_toon)} chars)")

        if testing:
            print(f"\n🧪 Cache: ./cache/github_data/")
            print(f"   Subsequent runs will use cached data")

    return jd, jd_toon, evaluation, eval_toon


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
    # Example usage - Full end-to-end evaluation

    jd, jd_toon, evaluation, eval_toon = combined_pipeline(
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
        testing=True  # Enable caching for both pipelines
    )

    print("\n" + "="*80)
    print("🏁 PIPELINE EXECUTION COMPLETE")
    print("="*80)
    print(f"\n📋 Job Description:")
    print(f"   Title: {jd.job_title}")
    print(f"   Repo: {jd.company_repo}")
    print(f"   Experience: {jd.experience_requirement.level} ({jd.experience_requirement.minimum_years}+ years)")

    print(f"\n👤 Candidate Evaluation:")
    print(f"   Name: {evaluation.candidate_name}")
    print(f"   Fit: {'YES ✅' if evaluation.final_decision.is_fit else 'NO ❌'}")
    print(f"   Score: {evaluation.final_decision.overall_score}/100")
    print(f"   Recommendation: {evaluation.final_decision.recommendation.upper()}")

    print(f"\n💡 Decision Reason:")
    print(f"   {evaluation.final_decision.fit_reason}")

    print(f"\n📁 Output Files:")
    print(f"   • {jd.company_repo.replace('/', '_')}_jd.toon")
    print(f"   • {evaluation.candidate_name.replace(' ', '_')}_evaluation.toon")
