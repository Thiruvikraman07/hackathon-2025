"""Main entry point for the hiring assessment system."""
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

from .workflows import HiringAssessmentWorkflow
from .config import logger, settings
from .api import start_server


def load_input_file(file_path: str) -> Dict[str, Any]:
    """
    Load input data from a JSON file.

    Args:
        file_path: Path to JSON file

    Returns:
        Input data dictionary
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        logger.info(f"Loaded input from: {file_path}")
        return data
    except Exception as e:
        logger.error(f"Error loading input file: {e}")
        raise


def save_output_file(output_data: Dict[str, Any], file_path: str) -> None:
    """
    Save output data to a JSON file.

    Args:
        output_data: Data to save
        file_path: Output file path
    """
    try:
        with open(file_path, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        logger.info(f"Saved output to: {file_path}")
    except Exception as e:
        logger.error(f"Error saving output file: {e}")
        raise


def run_cli_workflow(
    input_file: str,
    output_file: str,
    location: str = "Remote/Global",
    industry: str = "Technology"
) -> None:
    """
    Run the workflow from CLI.

    Args:
        input_file: Input JSON file path
        output_file: Output JSON file path
        location: Hiring location
        industry: Industry context
    """
    logger.info("=" * 80)
    logger.info("HIRING ASSESSMENT CLI")
    logger.info("=" * 80)

    # Load input
    input_data = load_input_file(input_file)

    # Create and run workflow
    workflow = HiringAssessmentWorkflow()

    results = workflow.run(
        input_data=input_data,
        location=location,
        industry=industry
    )

    # Save output
    save_output_file(results, output_file)

    logger.info("=" * 80)
    logger.info("WORKFLOW COMPLETED SUCCESSFULLY")
    logger.info(f"Results saved to: {output_file}")
    logger.info("=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Hiring Assessment Multi-Agent System"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # CLI workflow command
    cli_parser = subparsers.add_parser("run", help="Run workflow from CLI")
    cli_parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Input JSON file path"
    )
    cli_parser.add_argument(
        "--output",
        "-o",
        default="output.json",
        help="Output JSON file path (default: output.json)"
    )
    cli_parser.add_argument(
        "--location",
        default="Remote/Global",
        help="Hiring location (default: Remote/Global)"
    )
    cli_parser.add_argument(
        "--industry",
        default="Technology",
        help="Industry context (default: Technology)"
    )

    # API server command
    api_parser = subparsers.add_parser("serve", help="Start API server")
    api_parser.add_argument(
        "--host",
        default=None,
        help=f"Host to bind to (default: {settings.api_host})"
    )
    api_parser.add_argument(
        "--port",
        type=int,
        default=None,
        help=f"Port to bind to (default: {settings.api_port})"
    )
    api_parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload"
    )

    args = parser.parse_args()

    if args.command == "run":
        # Run CLI workflow
        run_cli_workflow(
            input_file=args.input,
            output_file=args.output,
            location=args.location,
            industry=args.industry
        )

    elif args.command == "serve":
        # Start API server
        logger.info("Starting API server...")
        start_server(
            host=args.host,
            port=args.port,
            reload=args.reload
        )

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
