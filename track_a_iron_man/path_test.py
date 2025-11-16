import json
from pathlib import Path
from typing import Optional


def combine_frontend_logs(
    jd_log_file: str,
    eval_log_file: str,
    output_file: str,
    verbose: bool = False
) -> dict:
    """
    Combine three frontend JSON log files into a single output file.
    
    Args:
        jd_log_file: Path to JD Generation log file
        eval_log_file: Path to Candidate Evaluation log file
        match_log_file: Path to Resume-JD Match log file
        output_file: Path where combined output will be saved
        verbose: If True, print progress messages
        
    Returns:
        dict: Combined data structure
    """
    
    def load_json(file_path: str, pipeline_name: str) -> Optional[dict]:
        """Load and parse a JSON file with error handling."""
        try:
            if verbose:
                print(f"📋 Loading {pipeline_name}: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if verbose:
                # Extract UUID if available
                uuid_preview = "unknown"
                if isinstance(data, dict) and 'uuid' in data:
                    uuid_preview = data['uuid'][:8] + "..."
                elif isinstance(data, dict) and 'execution_id' in data:
                    uuid_preview = data['execution_id'][:8] + "..."
                    
                print(f"   ✓ Loaded successfully (UUID: {uuid_preview})")
            
            return data
            
        except FileNotFoundError:
            print(f"   ✗ Error: File not found - {file_path}")
            return None
        except json.JSONDecodeError as e:
            print(f"   ✗ Error: Invalid JSON - {e}")
            return None
        except Exception as e:
            print(f"   ✗ Error: {e}")
            return None
    
    # Load all three log files
    jd_data = load_json(jd_log_file, "Pipeline 1 (JD Generation)")
    eval_data = load_json(eval_log_file, "Pipeline 2 (Candidate Evaluation)")
    
    # Check if all files loaded successfully
    if None in [jd_data, eval_data]:
        raise ValueError("Failed to load one or more log files")
    
    # Combine the data
    combined_data = {
        "metadata": {
            "combined_at": str(Path(output_file).stem),
            "source_files": {
                "jd_generation": jd_log_file,
                "candidate_evaluation": eval_log_file
            }
        },
        "pipelines": {
            "jd_generation": jd_data,
            "candidate_evaluation": eval_data
        }
    }
    
    # Save combined output
    if verbose:
        print(f"\n💾 Saving combined output to: {output_file}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, indent=2, ensure_ascii=False)
    
    if verbose:
        print(f"   ✓ Combined logs saved successfully!")
        print(f"   📊 Total pipelines: 2")
    
    return combined_data


# Example usage
if __name__ == "__main__":
    combine_frontend_logs(
        jd_log_file="execution_logs/bd3cac1f-e1a1-4f50-8ebc-93bf2090597f_frontend.json",
        eval_log_file="execution_logs/cf269032-db97-4c89-b342-6a0695239770_frontend.json",
        output_file="execution_logs/combined_output.json",
        verbose=True
    )