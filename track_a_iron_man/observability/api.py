"""
Observability API for Frontend Integration

Provides REST API endpoints for accessing execution logs and metrics.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class ObservabilityAPI:
    """API for querying execution logs"""

    def __init__(self, log_dir: str = "execution_logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

    def get_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single execution by ID.

        Args:
            execution_id: Execution ID

        Returns:
            Frontend-ready execution data or None if not found
        """
        frontend_log_file = self.log_dir / f"{execution_id}_frontend.json"

        if not frontend_log_file.exists():
            return None

        with open(frontend_log_file, 'r') as f:
            return json.load(f)

    def get_all_executions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get all executions, sorted by most recent.

        Args:
            limit: Maximum number of executions to return

        Returns:
            List of frontend-ready execution data
        """
        executions = []

        # Get all frontend log files
        frontend_files = sorted(
            self.log_dir.glob("*_frontend.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True  # Most recent first
        )

        for file_path in frontend_files[:limit]:
            try:
                with open(file_path, 'r') as f:
                    execution = json.load(f)
                    executions.append(execution)
            except Exception:
                continue

        return executions

    def get_recent_executions(self, hours: int = 24, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get executions from the last N hours.

        Args:
            hours: Number of hours to look back
            limit: Maximum number of executions to return

        Returns:
            List of recent executions
        """
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        executions = []

        frontend_files = sorted(
            self.log_dir.glob("*_frontend.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )

        for file_path in frontend_files[:limit]:
            # Check if file is within time range
            if file_path.stat().st_mtime < cutoff_time:
                continue

            try:
                with open(file_path, 'r') as f:
                    execution = json.load(f)
                    executions.append(execution)
            except Exception:
                continue

        return executions

    def get_executions_by_status(self, status: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get executions by status.

        Args:
            status: Status to filter by (success, failed, in_progress)
            limit: Maximum number of executions to return

        Returns:
            List of matching executions
        """
        all_executions = self.get_all_executions(limit=limit * 2)  # Get more to filter
        return [
            ex for ex in all_executions
            if ex.get('summary', {}).get('status') == status
        ][:limit]

    def get_executions_by_repo_type(self, repo_type: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get executions by repository type.

        Args:
            repo_type: Repository type ('github' or 'local')
            limit: Maximum number of executions to return

        Returns:
            List of matching executions
        """
        all_executions = self.get_all_executions(limit=limit * 2)
        return [
            ex for ex in all_executions
            if ex.get('repository', {}).get('type') == repo_type
        ][:limit]

    def get_execution_stats(self) -> Dict[str, Any]:
        """
        Get overall execution statistics.

        Returns:
            Dictionary with statistics
        """
        all_executions = self.get_all_executions(limit=1000)

        total_count = len(all_executions)
        successful = sum(1 for ex in all_executions if ex.get('summary', {}).get('success'))
        failed = total_count - successful

        github_count = sum(
            1 for ex in all_executions
            if ex.get('repository', {}).get('type') == 'github'
        )
        local_count = total_count - github_count

        total_tokens = sum(
            ex.get('summary', {}).get('totalTokens', 0)
            for ex in all_executions
        )

        total_cost = sum(
            ex.get('summary', {}).get('totalCostUsd', 0)
            for ex in all_executions
        )

        avg_duration = (
            sum(
                ex.get('summary', {}).get('totalDurationMs', 0)
                for ex in all_executions
            ) / total_count
        ) if total_count > 0 else 0

        return {
            "totalExecutions": total_count,
            "successful": successful,
            "failed": failed,
            "successRate": (successful / total_count * 100) if total_count > 0 else 0,
            "repositoryTypes": {
                "github": github_count,
                "local": local_count
            },
            "metrics": {
                "totalTokens": total_tokens,
                "totalCostUsd": total_cost,
                "avgDurationMs": avg_duration
            }
        }


# Convenience functions for direct use
def get_execution(execution_id: str) -> Optional[Dict[str, Any]]:
    """Get a single execution by ID"""
    api = ObservabilityAPI()
    return api.get_execution(execution_id)


def get_all_executions(limit: int = 50) -> List[Dict[str, Any]]:
    """Get all executions"""
    api = ObservabilityAPI()
    return api.get_all_executions(limit=limit)


def get_recent_executions(hours: int = 24, limit: int = 50) -> List[Dict[str, Any]]:
    """Get recent executions"""
    api = ObservabilityAPI()
    return api.get_recent_executions(hours=hours, limit=limit)


def get_execution_stats() -> Dict[str, Any]:
    """Get execution statistics"""
    api = ObservabilityAPI()
    return api.get_execution_stats()


# Example Flask/FastAPI endpoint implementations
"""
# Flask Example
from flask import Flask, jsonify
from track_a_iron_man.observability.api import ObservabilityAPI

app = Flask(__name__)
api = ObservabilityAPI()

@app.route('/api/executions')
def list_executions():
    executions = api.get_all_executions(limit=50)
    return jsonify(executions)

@app.route('/api/executions/<execution_id>')
def get_execution(execution_id):
    execution = api.get_execution(execution_id)
    if execution is None:
        return jsonify({"error": "Execution not found"}), 404
    return jsonify(execution)

@app.route('/api/stats')
def stats():
    return jsonify(api.get_execution_stats())


# FastAPI Example
from fastapi import FastAPI, HTTPException
from track_a_iron_man.observability.api import ObservabilityAPI

app = FastAPI()
api = ObservabilityAPI()

@app.get("/api/executions")
async def list_executions(limit: int = 50):
    return api.get_all_executions(limit=limit)

@app.get("/api/executions/{execution_id}")
async def get_execution(execution_id: str):
    execution = api.get_execution(execution_id)
    if execution is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution

@app.get("/api/stats")
async def stats():
    return api.get_execution_stats()
"""
