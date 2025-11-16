"""
Example Usage of Combined Pipeline

This script shows different ways to use the combined pipeline.
"""

import sys
from pathlib import Path

# Add core to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'core'))

from combined_pipeline import combined_pipeline


def example_1_basic_usage():
    """Basic usage with minimal parameters."""
    print("\n" + "="*80)
    print("Example 1: Basic Usage")
    print("="*80)

    jd, jd_toon, evaluation, eval_toon = combined_pipeline(
        company_repo="fastapi/fastapi",
        job_title="Backend Developer",
        resume_pdf_path="Resume V20.pdf",
        testing=True  # Use caching
    )

    print(f"\nResult: {evaluation.candidate_name}")
    print(f"Fit: {'YES' if evaluation.final_decision.is_fit else 'NO'}")
    print(f"Score: {evaluation.final_decision.overall_score}/100")


def example_2_full_parameters():
    """Usage with all optional parameters."""
    print("\n" + "="*80)
    print("Example 2: Full Parameters")
    print("="*80)

    jd, jd_toon, evaluation, eval_toon = combined_pipeline(
        company_repo="fastapi/fastapi",
        job_title="Senior Python Backend Developer",
        resume_pdf_path="Resume V20.pdf",
        salary_range="$140k-$180k",
        additional_requirements=[
            "Experience with microservices architecture",
            "Strong communication skills for remote work",
            "Open source contribution experience"
        ],
        verbose=True,
        testing=True
    )

    print(f"\nGenerated JD with {len(jd.qualifications)} qualifications")
    print(f"Candidate Score: {evaluation.final_decision.overall_score}/100")


def example_3_multiple_candidates():
    """Evaluate multiple candidates against the same JD."""
    print("\n" + "="*80)
    print("Example 3: Multiple Candidates")
    print("="*80)

    candidates = [
        "candidate1_resume.pdf",
        "candidate2_resume.pdf",
        "candidate3_resume.pdf"
    ]

    results = []

    for resume in candidates:
        try:
            jd, jd_toon, evaluation, eval_toon = combined_pipeline(
                company_repo="fastapi/fastapi",
                job_title="Senior Python Backend Developer",
                resume_pdf_path=resume,
                verbose=False,  # Suppress output for batch processing
                testing=True  # Use cache
            )

            results.append({
                'name': evaluation.candidate_name,
                'score': evaluation.final_decision.overall_score,
                'fit': evaluation.final_decision.is_fit,
                'recommendation': evaluation.final_decision.recommendation
            })

        except FileNotFoundError:
            print(f"Resume not found: {resume}")
            continue

    # Print summary
    print("\nCandidate Rankings:")
    sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)
    for i, result in enumerate(sorted_results, 1):
        fit_icon = "✅" if result['fit'] else "❌"
        print(f"{i}. {result['name']}: {result['score']}/100 {fit_icon} ({result['recommendation']})")


def example_4_custom_jd_requirements():
    """Generate JD with specific custom requirements."""
    print("\n" + "="*80)
    print("Example 4: Custom JD Requirements")
    print("="*80)

    jd, jd_toon, evaluation, eval_toon = combined_pipeline(
        company_repo="django/django",
        job_title="Full Stack Developer",
        resume_pdf_path="Resume V20.pdf",
        salary_range="$120k-$150k",
        additional_requirements=[
            "Must have experience with React or Vue.js",
            "Experience with PostgreSQL required",
            "Docker and Kubernetes knowledge preferred",
            "Agile/Scrum experience",
            "Strong testing practices (TDD/BDD)"
        ],
        verbose=True,
        testing=True
    )

    print(f"\nJD Generated: {jd.job_title}")
    print(f"Additional Requirements: {len(jd.additional_requirements)}")
    print(f"\nEvaluation Complete:")
    print(f"  Skill Match Score: {evaluation.final_decision.skill_match_score}/100")
    print(f"  Number of Gaps: {len(evaluation.skill_gaps)}")


def example_5_access_detailed_data():
    """Access detailed evaluation data."""
    print("\n" + "="*80)
    print("Example 5: Accessing Detailed Data")
    print("="*80)

    jd, jd_toon, evaluation, eval_toon = combined_pipeline(
        company_repo="fastapi/fastapi",
        job_title="Senior Python Backend Developer",
        resume_pdf_path="Resume V20.pdf",
        verbose=False,
        testing=True
    )

    # Access JD details
    print("\nJob Description Details:")
    print(f"  Title: {jd.job_title}")
    print(f"  Repository: {jd.company_repo}")
    print(f"  Experience Level: {jd.experience_requirement.level}")
    print(f"  Minimum Years: {jd.experience_requirement.minimum_years}")

    print("\n  Primary Languages:")
    for lang in jd.technical_requirements.primary_languages:
        print(f"    • {lang.name} [{lang.importance}]")

    print("\n  Frameworks:")
    for fw in jd.technical_requirements.frameworks_libraries:
        print(f"    • {fw.name} [{fw.importance}]")

    # Access evaluation details
    print("\nCandidate Evaluation Details:")
    print(f"  Name: {evaluation.candidate_name}")
    print(f"  Years of Experience: {evaluation.resume_analysis.years_of_experience}")
    print(f"  Education Match: {evaluation.resume_analysis.education_match}")

    print("\n  Skill Matches:")
    for skill in evaluation.resume_analysis.skill_matches[:5]:  # Top 5
        status = "✓" if skill.has_skill else "✗"
        print(f"    {status} {skill.skill_name}: {skill.proficiency_score}/10")

    if evaluation.github_analysis.has_github:
        print(f"\n  GitHub Analysis:")
        print(f"    Username: {evaluation.github_analysis.github_username}")
        print(f"    Projects Found: {evaluation.github_analysis.projects_found}")
        print(f"    Relevant Projects: {len(evaluation.github_analysis.relevant_projects)}")

    print("\n  Skill Gaps:")
    for gap in evaluation.skill_gaps[:3]:  # Top 3
        severity_icon = "🔴" if gap.severity == "critical" else "🟡" if gap.severity == "moderate" else "🟢"
        print(f"    {severity_icon} {gap.gap_name} [{gap.severity}]")

    print("\n  Final Decision:")
    print(f"    Fit: {'YES' if evaluation.final_decision.is_fit else 'NO'}")
    print(f"    Overall Score: {evaluation.final_decision.overall_score}/100")
    print(f"    Resume Score: {evaluation.final_decision.resume_score}/100")
    print(f"    GitHub Score: {evaluation.final_decision.github_score}/100")
    print(f"    Skill Match Score: {evaluation.final_decision.skill_match_score}/100")
    print(f"    Recommendation: {evaluation.final_decision.recommendation}")
    print(f"    Confidence: {evaluation.final_decision.confidence_level}%")

    print("\n  Top Strengths:")
    for i, strength in enumerate(evaluation.strengths[:3], 1):
        print(f"    {i}. {strength}")


def example_6_toon_format():
    """Working with TOON format outputs."""
    print("\n" + "="*80)
    print("Example 6: TOON Format Outputs")
    print("="*80)

    jd, jd_toon, evaluation, eval_toon = combined_pipeline(
        company_repo="fastapi/fastapi",
        job_title="Backend Developer",
        resume_pdf_path="Resume V20.pdf",
        verbose=False,
        testing=True
    )

    print(f"\nTOON Output Sizes:")
    print(f"  JD TOON: {len(jd_toon)} characters")
    print(f"  Evaluation TOON: {len(eval_toon)} characters")

    # TOON data can be decoded back to dict if needed
    from toon import decode as toon_decode

    jd_dict = toon_decode(jd_toon)
    eval_dict = toon_decode(eval_toon)

    print(f"\nDecoded JD has {len(jd_dict)} top-level keys")
    print(f"Decoded Evaluation has {len(eval_dict)} top-level keys")

    # You can now send these to APIs, databases, etc.
    print("\nTOON data ready for:")
    print("  • Storage in databases")
    print("  • API transmission")
    print("  • Archive/audit trails")
    print("  • Integration with other systems")


def main():
    """Run all examples."""
    examples = [
        ("Basic Usage", example_1_basic_usage),
        ("Full Parameters", example_2_full_parameters),
        ("Multiple Candidates", example_3_multiple_candidates),
        ("Custom JD Requirements", example_4_custom_jd_requirements),
        ("Detailed Data Access", example_5_access_detailed_data),
        ("TOON Format", example_6_toon_format)
    ]

    print("\n" + "="*80)
    print("Combined Pipeline Examples")
    print("="*80)
    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")

    print("\nNote: Set HOLISTIC_AI credentials in .env to run these examples")
    print("      Or modify code to use OpenAI instead")

    # Uncomment to run a specific example:
    # example_1_basic_usage()
    # example_2_full_parameters()
    # example_3_multiple_candidates()
    # example_4_custom_jd_requirements()
    # example_5_access_detailed_data()
    # example_6_toon_format()


if __name__ == "__main__":
    main()
