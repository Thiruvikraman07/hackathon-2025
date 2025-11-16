"""
Demo script comparing GitHub vs Local repository analysis.

This script demonstrates the flexibility of Pipeline 1 to work with
both GitHub repositories and local file system repositories.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from track_a_iron_man.pipeline1_jd_generator import generate_jd


def demo_comparison():
    """Run comparison demo between GitHub and Local repos."""

    print("\n" + "="*80)
    print("PIPELINE 1 JD GENERATOR - REPOSITORY TYPE COMPARISON")
    print("="*80)
    print("\nThis demo shows how Pipeline 1 works with BOTH GitHub and Local repositories")
    print()

    # Example 1: Local Repository
    print("\n" + "─"*80)
    print("EXAMPLE 1: LOCAL REPOSITORY")
    print("─"*80)
    print("\nScenario: Company wants to analyze their private codebase")
    print("Solution: Use local file path instead of GitHub repo\n")

    local_repo_path = str(Path(__file__).parent.parent / "test_local_repo")

    print(f"📁 Input: company_repo = '{local_repo_path}'")
    print("🔍 Detection: System recognizes this as a local directory path")
    print("🛠️  Tools Used: fetch_local_repo_metadata, get_local_repo_file_structure, fetch_local_code_files")
    print("\nPress Enter to continue with local repo analysis (or Ctrl+C to skip)...")

    try:
        input()

        jd_local, toon_local = generate_jd(
            company_repo=local_repo_path,
            job_title="Backend Engineer",
            salary_range="$120k-$160k",
            additional_requirements=["Python expertise", "FastAPI experience"],
            verbose=True,
            testing=False
        )

        print(f"\n✅ Local Analysis Complete!")
        print(f"   - Files Analyzed: {jd_local.total_files_analyzed}")
        print(f"   - Primary Languages: {[lang.name for lang in jd_local.technical_requirements.primary_languages]}")
        print(f"   - Output File: local_test_local_repo_jd.toon")

    except KeyboardInterrupt:
        print("\n⏭️  Skipped local repo demo")

    # Example 2: GitHub Repository
    print("\n\n" + "─"*80)
    print("EXAMPLE 2: GITHUB REPOSITORY")
    print("─"*80)
    print("\nScenario: Company wants to analyze a public GitHub project")
    print("Solution: Use GitHub repo in 'owner/repo' format\n")

    github_repo = "fastapi/fastapi"

    print(f"🐙 Input: company_repo = '{github_repo}'")
    print("🔍 Detection: System recognizes this as a GitHub repository")
    print("🛠️  Tools Used: fetch_repo_metadata, get_repo_file_structure, fetch_code_files")
    print("\nPress Enter to continue with GitHub repo analysis (or Ctrl+C to skip)...")

    try:
        input()

        jd_github, toon_github = generate_jd(
            company_repo=github_repo,
            job_title="Backend Engineer",
            salary_range="$120k-$160k",
            additional_requirements=["Python expertise", "FastAPI experience"],
            verbose=True,
            testing=True  # Cache GitHub data for faster subsequent runs
        )

        print(f"\n✅ GitHub Analysis Complete!")
        print(f"   - Files Analyzed: {jd_github.total_files_analyzed}")
        print(f"   - Primary Languages: {[lang.name for lang in jd_github.technical_requirements.primary_languages]}")
        print(f"   - Output File: fastapi_fastapi_jd.toon")

    except KeyboardInterrupt:
        print("\n⏭️  Skipped GitHub repo demo")

    # Summary
    print("\n\n" + "="*80)
    print("SUMMARY: KEY DIFFERENCES")
    print("="*80)

    print("\n📊 Comparison Table:")
    print(f"{'Feature':<30} {'Local Repository':<25} {'GitHub Repository':<25}")
    print("─"*80)
    print(f"{'Input Format':<30} {'File path':<25} {'owner/repo':<25}")
    print(f"{'Network Required':<30} {'No (except LLM)':<25} {'Yes (API calls)':<25}")
    print(f"{'Rate Limits':<30} {'None':<25} {'GitHub API limits':<25}")
    print(f"{'Privacy':<30} {'Full (private code)':<25} {'Public repos only':<25}")
    print(f"{'Speed':<30} {'Fast (local I/O)':<25} {'Slower (network)':<25}")
    print(f"{'Caching':<30} {'N/A':<25} {'Supported':<25}")
    print(f"{'Repository Metadata':<30} {'Limited':<25} {'Rich (stars, etc.)':<25}")

    print("\n\n💡 USE CASES:")
    print("\n  Local Repository:")
    print("    ✓ Private company codebases")
    print("    ✓ Testing and development")
    print("    ✓ Offline analysis")
    print("    ✓ No GitHub account needed")

    print("\n  GitHub Repository:")
    print("    ✓ Public open-source projects")
    print("    ✓ Rich metadata (stars, forks)")
    print("    ✓ Company with public repos")
    print("    ✓ Benchmarking against popular projects")

    print("\n" + "="*80)
    print("✨ CONCLUSION")
    print("="*80)
    print("\nPipeline 1 JD Generator is flexible and works seamlessly with BOTH:")
    print("  • Local file system repositories (any directory path)")
    print("  • GitHub repositories (owner/repo format)")
    print("\nThe system automatically detects the type and uses the right tools!")
    print("="*80 + "\n")


if __name__ == "__main__":
    try:
        demo_comparison()
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
        sys.exit(0)
