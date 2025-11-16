# API Endpoints Documentation

## Applications Management

The API now includes endpoints to manage and retrieve candidate applications.

### Base URL
```
http://localhost:8000
```

### Endpoints

#### 1. List All Applications
**GET** `/applications/`

List all candidate applications with pagination and optional filtering.

**Query Parameters:**
- `skip` (integer, optional): Number of records to skip for pagination (default: 0)
- `limit` (integer, optional): Maximum number of records to return (default: 100, max: 500)
- `is_hire` (boolean, optional): Filter by hire decision
  - `true` - Only hired candidates
  - `false` - Only rejected candidates
  - Omit - All applications

**Response:**
```json
{
  "total": 42,
  "skip": 0,
  "limit": 100,
  "applications": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "candidate_name": "John Doe",
      "job_title": "Senior Python Backend Developer",
      "company_repo": "fastapi/fastapi",
      "final_score": 85,
      "is_hire": true,
      "decision_category": "hire",
      "created_at": "2025-01-16T10:30:00Z",
      "updated_at": "2025-01-16T10:30:00Z"
    }
  ]
}
```

**Example Requests:**
```bash
# Get all applications
curl http://localhost:8000/applications/

# Get first 20 applications
curl http://localhost:8000/applications/?skip=0&limit=20

# Get only hired candidates
curl http://localhost:8000/applications/?is_hire=true

# Get only rejected candidates with pagination
curl http://localhost:8000/applications/?is_hire=false&skip=10&limit=10
```

---

#### 2. Get Specific Application by ID
**GET** `/applications/{application_id}`

Retrieve detailed information about a specific application.

**Path Parameters:**
- `application_id` (string, required): UUID of the application

**Response:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "candidate_name": "John Doe",
  "job_title": "Senior Python Backend Developer",
  "company_repo": "fastapi/fastapi",
  "final_score": 85,
  "is_hire": true,
  "decision_category": "hire",
  "decision_reason": "Strong technical background with extensive Python experience...",
  "top_strengths": [
    "Expert in Python and FastAPI",
    "Strong async programming skills",
    "Experience with microservices architecture"
  ],
  "critical_gaps": [],
  "jd_toon": "base64_encoded_job_description...",
  "evaluation_toon": "base64_encoded_evaluation...",
  "created_at": "2025-01-16T10:30:00Z",
  "updated_at": "2025-01-16T10:30:00Z"
}
```

**Example Request:**
```bash
curl http://localhost:8000/applications/123e4567-e89b-12d3-a456-426614174000
```

**Error Response (404):**
```json
{
  "detail": "Application with ID '123e4567-e89b-12d3-a456-426614174000' not found"
}
```

---

#### 3. Delete Application
**DELETE** `/applications/{application_id}`

Delete a specific application by ID.

**Path Parameters:**
- `application_id` (string, required): UUID of the application

**Response:**
```json
{
  "message": "Application 123e4567-e89b-12d3-a456-426614174000 deleted successfully",
  "deleted_at": "2025-01-16T11:00:00Z"
}
```

**Example Request:**
```bash
curl -X DELETE http://localhost:8000/applications/123e4567-e89b-12d3-a456-426614174000
```

---

#### 4. Submit Evaluation (Updated)
**POST** `/evaluation/`

The evaluation endpoint now returns an `application_id` along with the evaluation results.

**Form Data:**
- `resume` (file, required): Candidate's resume PDF
- `company_repo` (string, required): GitHub repository (e.g., "fastapi/fastapi")
- `job_title` (string, required): Job title
- `salary_range` (string, optional): Salary range
- `additional_requirements` (string, optional): Comma-separated requirements
- `testing` (boolean, optional): Enable caching mode (default: true)

**Response:**
```json
{
  "application_id": "123e4567-e89b-12d3-a456-426614174000",
  "candidate_name": "John Doe",
  "job_title": "Senior Python Backend Developer",
  "company_repo": "fastapi/fastapi",
  "final_score": 85,
  "is_hire": true,
  "decision_category": "hire",
  "decision_reason": "Strong technical background...",
  "top_strengths": ["..."],
  "critical_gaps": [],
  "jd_toon": "base64_encoded...",
  "evaluation_toon": "base64_encoded..."
}
```

**Example Request:**
```bash
curl -X POST http://localhost:8000/evaluation/ \
  -F "resume=@/path/to/resume.pdf" \
  -F "company_repo=fastapi/fastapi" \
  -F "job_title=Senior Python Backend Developer" \
  -F "salary_range=$140k-$180k" \
  -F "testing=true"
```

---

## Interactive API Documentation

FastAPI provides interactive API documentation at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Storage

Applications are stored in: `./data/applications.json`

This is a simple JSON file storage. For production use, consider migrating to a database like PostgreSQL or MongoDB.

## Running the Server

```bash
# Start the server
python server.py

# Or with custom host/port
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

## Example Workflow

1. **Submit a candidate evaluation:**
   ```bash
   curl -X POST http://localhost:8000/evaluation/ \
     -F "resume=@resume.pdf" \
     -F "company_repo=fastapi/fastapi" \
     -F "job_title=Senior Developer"
   ```
   Note the `application_id` from the response.

2. **List all applications:**
   ```bash
   curl http://localhost:8000/applications/
   ```

3. **Get specific application details:**
   ```bash
   curl http://localhost:8000/applications/{application_id}
   ```

4. **Filter hired candidates:**
   ```bash
   curl http://localhost:8000/applications/?is_hire=true
   ```
