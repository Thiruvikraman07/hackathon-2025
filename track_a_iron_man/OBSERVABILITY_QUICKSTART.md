# Observability Quick Start

## TL;DR

Pipeline 1 now tracks every step with LangSmith integration. Enable by default, query via API, display in frontend.

## Basic Usage

```python
from track_a_iron_man.pipeline1_jd_generator import generate_jd

# Run with observability (enabled by default)
jd, toon, execution = generate_jd(
    company_repo="fastapi/fastapi",  # or "/path/to/local/repo"
    job_title="Senior Backend Engineer",
    salary_range="$140k-$180k"
)

# Access execution data
print(f"Execution ID: {execution.execution_id}")
print(f"Duration: {execution.total_duration_ms}ms")
print(f"Steps: {len(execution.steps)}")
print(f"LangSmith: {execution.langsmith_url}")
```

## What Gets Tracked?

| Step | What | Duration |
|------|------|----------|
| **Detection** | GitHub vs Local identification | <1ms |
| **Initialization** | LLM & agent setup | ~200ms |
| **Agent Reasoning** | Repository analysis + JD generation | ~30-60s |
| **Output Generation** | TOON encoding + file save | ~2ms |

## Generated Files

```
execution_logs/
  ├── {execution_id}.json                # Detailed (for debugging)
  └── {execution_id}_frontend.json       # Frontend-ready (for UI)
```

## Query API

```python
from track_a_iron_man.observability.api import ObservabilityAPI

api = ObservabilityAPI()

# Get specific execution
execution = api.get_execution("execution-id")

# Get all executions
all_executions = api.get_all_executions(limit=50)

# Get recent (last 24 hours)
recent = api.get_recent_executions(hours=24)

# Get statistics
stats = api.get_execution_stats()
# Returns: totalExecutions, successRate, totalCost, avgDuration
```

## Frontend JSON Structure

```json
{
  "executionId": "uuid",
  "repository": {"type": "local|github", "path": "..."},
  "timeline": [
    {
      "id": "step_1",
      "name": "Detect Repository Type",
      "status": "success",
      "durationMs": 0.05,
      "input": {...},
      "output": {...},
      "reason": "Why this step happened"
    }
  ],
  "summary": {
    "totalDurationMs": 38635,
    "totalTokens": 1234,
    "totalCostUsd": 0.012,
    "filesAnalyzed": 3
  },
  "langsmith": {
    "runId": "uuid",
    "url": "https://smith.langchain.com/..."
  }
}
```

## REST API Example

```python
from fastapi import FastAPI
from track_a_iron_man.observability.api import ObservabilityAPI

app = FastAPI()
api = ObservabilityAPI()

@app.get("/api/executions")
async def list_executions():
    return api.get_all_executions(limit=50)

@app.get("/api/executions/{execution_id}")
async def get_execution(execution_id: str):
    return api.get_execution(execution_id)

@app.get("/api/stats")
async def stats():
    return api.get_execution_stats()
```

## LangSmith Setup

Add to `.env`:
```bash
LANGSMITH_API_KEY=lsv2_pt_...
LANGSMITH_PROJECT=my-project
LANGSMITH_TRACING=true
```

Get free key at: https://smith.langchain.com

## Disable Observability

```python
# For ultra-fast execution (no logging)
jd, toon, execution = generate_jd(
    company_repo="...",
    job_title="...",
    enable_observability=False  # execution will be None
)
```

## Performance

- **Overhead**: <0.02% of total execution time
- **Storage**: ~4KB per execution
- **Cost**: Free (LangSmith has generous free tier)

## Common Queries

### Get failed executions
```python
failed = api.get_executions_by_status("failed")
```

### Get local repo executions
```python
local = api.get_executions_by_repo_type("local")
```

### Calculate success rate
```python
stats = api.get_execution_stats()
print(f"Success rate: {stats['successRate']}%")
```

## Frontend Examples

### React
```tsx
function ExecutionViewer({ id }: { id: string }) {
  const [execution, setExecution] = useState(null);

  useEffect(() => {
    fetch(`/api/executions/${id}`)
      .then(r => r.json())
      .then(setExecution);
  }, [id]);

  return (
    <div>
      {execution?.timeline.map(step => (
        <div key={step.id}>
          {step.name}: {step.durationMs}ms
        </div>
      ))}
    </div>
  );
}
```

### Vue
```vue
<script setup>
const execution = ref(null);

onMounted(async () => {
  const res = await fetch(`/api/executions/${props.id}`);
  execution.value = await res.json();
});
</script>

<template>
  <div v-for="step in execution?.timeline" :key="step.id">
    {{ step.name }}: {{ step.durationMs }}ms
  </div>
</template>
```

## Debugging

### View execution summary
```python
print(execution.get_summary_text())
```

### Access specific step
```python
detection_step = execution.steps[0]
print(f"Decision: {detection_step.decision_point}")
print(f"Output: {detection_step.output_data}")
```

### Check for errors
```python
for step in execution.steps:
    if step.error:
        print(f"Step {step.name} failed: {step.error}")
```

## Key Benefits

✅ **Zero configuration** - Works out of the box
✅ **Automatic tracking** - No manual logging needed
✅ **LangSmith integration** - Deep agent insights
✅ **Frontend ready** - JSON files ready to use
✅ **Minimal overhead** - <0.02% performance impact
✅ **Production safe** - Robust error handling

## Documentation

- Full Guide: `OBSERVABILITY_GUIDE.md`
- Implementation Details: `OBSERVABILITY_IMPLEMENTATION.md`
- API Reference: `observability/api.py`
- Test Example: `test_local_repo_jd.py`

## Support

- LangSmith Docs: https://docs.smith.langchain.com
- LangGraph Tracing: https://langchain-ai.github.io/langgraph/how-tos/tracing/
