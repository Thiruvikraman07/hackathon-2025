# Hiring Assessment Multi-Agent System

A sophisticated multi-agent system for analyzing hiring requirements based on strategic context, pain points, artifacts, and market intelligence.

## Architecture

The system uses a layered agent architecture:

### Layer 1: Data Extraction Agents (Parallel Processing)
- **Agent 1.1**: Strategic Context Extractor - Analyzes business objectives
- **Agent 1.2**: Pain Point Analyzer - Processes supervisor feedback
- **Agent 1.3**: Artifact Inspector A - Examines deliverables and codebase
- **Agent 1.4**: Artifact Inspector B - Suggests improvement areas
- **Agent 1.5**: Artifact Inspector C - Analyzes network patterns

### Layer Semi-2: Enhancement Agents
- **Agent 1.6**: Artifact Inspector B2 - Searches best practices

### Layer 2: Synthesis Agents (Convergent Processing)
- **Agent 2.1**: Requirement Synthesizer - Merges inputs from Layer 1
- **Agent 2.2**: Market Intelligence Agent - Validates against market reality

### Layer 3: Quality Assurance
- **Agent 3.1**: "BUT" Agent - Identifies conflicts and feasibility issues

## Installation

```bash
# Using pip
pip install -r requirements.txt

# Using poetry
poetry install
```

## Configuration

Create a `.env` file with the following variables:

```env
OPENAI_API_KEY=your_openai_api_key
VALYU_API_KEY=your_valyu_api_key
CHROMA_PERSIST_DIRECTORY=./chroma_db
LOG_LEVEL=INFO
```

## Usage

### CLI

```bash
python src/main.py --input data/input.json
```

### API

```bash
uvicorn src.api.fastapi_app:app --reload
```

Then access the API at `http://localhost:8000/docs`

## Project Structure

```
hiring-assessment/
├─ pyproject.toml / requirements.txt
├─ README.md
├─ .env
└─ src/
   ├─ main.py
   ├─ config/
   ├─ models/
   ├─ tools/
   ├─ memory/
   ├─ agents/
   ├─ workflows/
   └─ api/
```

## License

MIT
