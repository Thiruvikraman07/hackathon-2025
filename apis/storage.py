"""
Simple storage layer for application persistence
Uses JSON file storage for simplicity (could be replaced with a database)
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from threading import Lock


class ApplicationStorage:
    """Thread-safe storage for candidate applications"""

    def __init__(self, storage_path: str = "./data/applications.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = Lock()
        self._ensure_storage_exists()

    def _ensure_storage_exists(self):
        """Create storage file if it doesn't exist"""
        if not self.storage_path.exists():
            self._write_data({})

    def _read_data(self) -> Dict:
        """Read data from storage file"""
        try:
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _write_data(self, data: Dict):
        """Write data to storage file"""
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)

    def create_application(self, application_data: Dict) -> str:
        """
        Create a new application and return its ID

        Args:
            application_data: Dictionary containing application information

        Returns:
            Application ID (UUID)
        """
        with self.lock:
            app_id = str(uuid.uuid4())
            application_data['id'] = app_id
            application_data['created_at'] = datetime.utcnow().isoformat()
            application_data['updated_at'] = datetime.utcnow().isoformat()

            data = self._read_data()
            data[app_id] = application_data
            self._write_data(data)

            return app_id

    def get_application(self, app_id: str) -> Optional[Dict]:
        """
        Get an application by ID

        Args:
            app_id: Application ID

        Returns:
            Application data or None if not found
        """
        with self.lock:
            data = self._read_data()
            return data.get(app_id)

    def list_applications(
        self,
        skip: int = 0,
        limit: int = 100,
        is_hire: Optional[bool] = None
    ) -> List[Dict]:
        """
        List all applications with pagination and optional filtering

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            is_hire: Filter by hire decision (None = all)

        Returns:
            List of applications sorted by creation date (newest first)
        """
        with self.lock:
            data = self._read_data()
            applications = list(data.values())

            # Filter by hire decision if specified
            if is_hire is not None:
                applications = [
                    app for app in applications
                    if app.get('is_hire') == is_hire
                ]

            # Sort by created_at descending (newest first)
            applications.sort(
                key=lambda x: x.get('created_at', ''),
                reverse=True
            )

            # Apply pagination
            return applications[skip:skip + limit]

    def count_applications(self, is_hire: Optional[bool] = None) -> int:
        """
        Count total applications

        Args:
            is_hire: Filter by hire decision (None = all)

        Returns:
            Total count
        """
        with self.lock:
            data = self._read_data()
            applications = list(data.values())

            if is_hire is not None:
                applications = [
                    app for app in applications
                    if app.get('is_hire') == is_hire
                ]

            return len(applications)

    def delete_application(self, app_id: str) -> bool:
        """
        Delete an application by ID

        Args:
            app_id: Application ID

        Returns:
            True if deleted, False if not found
        """
        with self.lock:
            data = self._read_data()
            if app_id in data:
                del data[app_id]
                self._write_data(data)
                return True
            return False


# Global storage instance
storage = ApplicationStorage()
