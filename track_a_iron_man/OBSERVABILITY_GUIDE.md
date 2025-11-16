# Observability System Guide

## Overview

The Pipeline 1 JD Generator now includes a comprehensive observability system that tracks every step of execution, integrates with LangSmith for deep agent tracing, and provides frontend-ready output.

## Architecture

```
┌─────────────────────────────────────────────┐
│ Layer 1: LangSmith Auto-Tracing           │
│  - Agent reasoning & tool calls            │
│  - Token usage & latency                   │
│  - Model parameters                        │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│ Layer 2: Custom Step Tracker              │
│  - Repository type detection               │
│  - Tool initialization                     │
│  - File retrieval tracking                 │
│  - Business logic decisions                │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│ Layer 3: Frontend-Ready JSON              │
│  - Execution timeline                       │
│  - Step-by-step breakdown                   │
│  - Metrics & performance data              │
│  - LangSmith integration links             │
└─────────────────────────────────────────────┘
```

## Features

### 1. Step-by-Step Tracking

Every execution is broken down into discrete steps:

- **Detection**: Repository type identification (GitHub vs Local)
- **Initialization**: LLM and Agent setup with appropriate tools
- **Agent Reasoning**: Repository analysis and JD generation
- **Output Generation**: TOON encoding and file saving

### 2. Detailed Metrics

For each step, the system tracks:
- Input data
- Output data
- Duration (milliseconds)
- Decision points
- Errors (if any)
- Token usage
- Cost estimates
- Files processed

### 3. LangSmith Integration

Automatic integration with LangSmith provides:
- Deep agent reasoning traces
- Tool call sequences
- Model parameter tracking
- Direct links to LangSmith UI

### 4. Frontend-Ready Output

Two JSON files are generated per execution:

**Detailed Log** (`{execution_id}.json`):
- Complete execution object
- All step data
- Full error traces

**Frontend Log** (`{execution_id}_frontend.json`):
- Clean, structured format
- Ready for API consumption
- Optimized for UI rendering

## Usage

### Basic Usage

```python
from track_a_iron_man.pipeline1_jd_generator import generate_jd

# Generate JD with observability enabled (default)
jd, toon, execution = generate_jd(
    company_repo="fastapi/fastapi",
    job_title="Senior Backend Engineer",
    salary_range="$140k-$180k",
    enable_observability=True  # Default: True
)

# Access execution data
print(f"Execution ID: {execution.execution_id}")
print(f"Total Duration: {execution.total_duration_ms}ms")
print(f"Steps: {len(execution.steps)}")
print(f"LangSmith URL: {execution.langsmith_url}")
```

### Disable Observability

```python
# Disable for faster execution (no logging overhead)
jd, toon, execution = generate_jd(
    company_repo="/path/to/repo",
    job_title="Developer",
    enable_observability=False
)

# execution will be None
```

### Access Execution Logs

```python
from track_a_iron_man.observability.api import ObservabilityAPI

api = ObservabilityAPI()

# Get a specific execution
execution = api.get_execution("execution-id-here")

# Get all recent executions
recent = api.get_recent_executions(hours=24, limit=50)

# Get executions by status
successful = api.get_executions_by_status("success", limit=20)
failed = api.get_executions_by_status("failed", limit=10)

# Get statistics
stats = api.get_execution_stats()
print(f"Success Rate: {stats['successRate']}%")
print(f"Total Cost: ${stats['metrics']['totalCostUsd']}")
```

## Execution Timeline Structure

Each execution contains a timeline of steps:

```json
{
  "executionId": "uuid",
  "pipeline": "pipeline1_jd_generator",
  "repository": {
    "type": "local" | "github",
    "path": "..."
  },
  "timeline": [
    {
      "id": "step_1",
      "type": "detection",
      "name": "Detect Repository Type",
      "status": "success" | "failed" | "in_progress",
      "startTime": "ISO-8601",
      "endTime": "ISO-8601",
      "durationMs": 123.45,
      "input": {...},
      "output": {...},
      "reason": "Why this step was performed",
      "decisionPoint": "Key decision made",
      "toolUsed": "Tool name if applicable",
      "error": "Error message if failed",
      "metrics": {
        "tokens": 1234,
        "cost": 0.001,
        "filesProcessed": 3
      }
    }
  ],
  "summary": {
    "status": "success",
    "success": true,
    "totalDurationMs": 38635.52,
    "totalTokens": 1234,
    "totalCostUsd": 0.0123,
    "filesAnalyzed": 3
  },
  "langsmith": {
    "runId": "uuid",
    "url": "https://smith.langchain.com/...",
    "project": "project-name"
  }
}
```

## Step Types

| Type | Description | Typical Duration |
|------|-------------|------------------|
| `detection` | Repository type detection | <1ms |
| `initialization` | Agent & tool setup | 200-300ms |
| `agent_reasoning` | Repository analysis & JD generation | 30-60s |
| `output_generation` | TOON encoding & file save | 1-5ms |

## Frontend Integration

### React Example

```typescript
interface ExecutionTimeline {
  executionId: string;
  timeline: Step[];
  summary: Summary;
}

function ExecutionViewer({ executionId }: { executionId: string }) {
  const [execution, setExecution] = useState<ExecutionTimeline | null>(null);

  useEffect(() => {
    fetch(`/api/executions/${executionId}`)
      .then(res => res.json())
      .then(setExecution);
  }, [executionId]);

  if (!execution) return <div>Loading...</div>;

  return (
    <div>
      <h2>Execution {execution.executionId}</h2>
      <ExecutionSummary summary={execution.summary} />
      <Timeline steps={execution.timeline} />
    </div>
  );
}
```

### Vue Example

```vue
<template>
  <div v-if="execution">
    <h2>Execution {{ execution.executionId }}</h2>
    <div class="timeline">
      <div v-for="step in execution.timeline" :key="step.id" class="step">
        <div class="step-header">
          <span class="step-name">{{ step.name }}</span>
          <span class="step-duration">{{ step.durationMs }}ms</span>
        </div>
        <div class="step-details">
          <p>{{ step.reason }}</p>
          <div v-if="step.error" class="error">{{ step.error }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';

const props = defineProps<{ executionId: string }>();
const execution = ref(null);

onMounted(async () => {
  const response = await fetch(`/api/executions/${props.executionId}`);
  execution.value = await response.json();
});
</script>
```

## API Endpoints (Example Implementation)

```python
# FastAPI
from fastapi import FastAPI, HTTPException
from track_a_iron_man.observability.api import ObservabilityAPI

app = FastAPI()
api = ObservabilityAPI()

@app.get("/api/executions")
async def list_executions(limit: int = 50):
    """Get all executions"""
    return api.get_all_executions(limit=limit)

@app.get("/api/executions/{execution_id}")
async def get_execution(execution_id: str):
    """Get a specific execution"""
    execution = api.get_execution(execution_id)
    if execution is None:
        raise HTTPException(status_code=404, detail="Not found")
    return execution

@app.get("/api/executions/recent/{hours}")
async def get_recent(hours: int = 24):
    """Get executions from last N hours"""
    return api.get_recent_executions(hours=hours)

@app.get("/api/stats")
async def get_stats():
    """Get execution statistics"""
    return api.get_execution_stats()
```

## Configuration

### Environment Variables

Required for LangSmith integration:
```bash
LANGSMITH_API_KEY=lsv2_pt_...
LANGSMITH_PROJECT=my-project
LANGSMITH_TRACING=true
```

### Storage Location

Execution logs are stored in:
```
execution_logs/
  ├── {execution_id}.json                 # Detailed log
  └── {execution_id}_frontend.json        # Frontend-ready log
```

## Best Practices

1. **Always Enable Observability in Production**
   - Minimal overhead (~1-2ms per step)
   - Invaluable for debugging
   - Critical for monitoring

2. **Monitor Key Metrics**
   - Success rate
   - Average duration
   - Token usage & costs
   - Error patterns

3. **Use LangSmith for Deep Debugging**
   - Agent reasoning analysis
   - Tool call inspection
   - Performance optimization

4. **Clean Up Old Logs**
   - Implement log rotation
   - Archive old executions
   - Set retention policies

5. **Add Custom Metadata**
   - User IDs
   - Session IDs
   - Feature flags
   - A/B test variants

## Troubleshooting

### Issue: No LangSmith URL

**Cause**: LangSmith API key not configured

**Solution**:
```bash
export LANGSMITH_API_KEY=your-key-here
export LANGSMITH_TRACING=true
```

### Issue: Logs Not Saving

**Cause**: Permission issues or disk space

**Solution**:
```bash
mkdir -p execution_logs
chmod 755 execution_logs
```

### Issue: High Overhead

**Cause**: Verbose logging enabled

**Solution**:
```python
generate_jd(..., verbose=False)  # Reduces console output
```

## Performance Impact

| Feature | Overhead | When to Disable |
|---------|----------|-----------------|
| Step tracking | ~1-2ms per step | Never (minimal) |
| JSON logging | ~1-5ms total | High-frequency calls |
| Verbose output | ~10-50ms total | Production (keep tracking on) |
| LangSmith tracing | ~0ms (async) | Never (free & valuable) |

## Examples

See:
- `track_a_iron_man/test_local_repo_jd.py` - Full example with observability
- `track_a_iron_man/observability/api.py` - API usage examples
- `execution_logs/` - Sample output files

## Benefits

1. **Complete Transparency**: See exactly what the pipeline did
2. **Easy Debugging**: Trace failures to specific steps
3. **Performance Monitoring**: Identify bottlenecks
4. **Cost Tracking**: Monitor token usage and costs
5. **Frontend Ready**: No additional processing needed
6. **LangSmith Integration**: Deep agent-level insights
7. **Production Safe**: Minimal overhead, robust error handling
