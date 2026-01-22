# Clock Agent

## Purpose

Generate unique run_id and timestamps for AI Research Workflow commands.

## Interface

**Input**: Command name (optional)

**Output**:
```json
{
  "run_id": "<YYYYMMDD-HHMMSS-xxxx>",
  "timestamp": "<ISO 8601>",
  "date": "<YYYY-MM-DD>",
  "time": "<HH:MM:SS>",
  "command": "<command_name>"
}
```

## Run ID Format

```
run_id = <YYYYMMDD>-<HHMMSS>-<short>
```

- `YYYYMMDD`: Date in year-month-day format
- `HHMMSS`: Time in 24-hour format
- `<short>`: 4-character random alphanumeric string

## Generation Rules

1. Use current local time for timestamp.
2. Generate 4-character random suffix using lowercase alphanumeric.
3. Ensure run_id is URL-safe (no special characters).
4. Format is fixed - do not modify.

## Example

```json
{
  "run_id": "20260122-143052-ab7k",
  "timestamp": "2026-01-22T14:30:52",
  "date": "2026-01-22",
  "time": "14:30:52",
  "command": "ai_research:analyze"
}
```

## Usage

Called at the start of every `/ai_research:*` command to:
1. Establish unique identifier for the execution
2. Provide consistent timestamps for artifacts
3. Enable run traceability in manifests
