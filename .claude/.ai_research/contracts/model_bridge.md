# Model Bridge Contract

## Role Resolution

```
(backend, role) → ROLE_FILE = .claude/.ai_research/prompts/<backend>/<role>.md
```

## Handoff Request Structure

```json
{
  "run_id": "<YYYYMMDD-HHMMSS>-<short>",
  "command": "ai_research:<cmd>",
  "task": "<task description>",
  "context": {
    "kb_refs": ["kb:paper:xxx", "kb:report:yyy"],
    "files": ["relative/path.ext"]
  },
  "constraints": ["<constraint1>", "<constraint2>"],
  "output_contract": "<reference to artifacts.md section>"
}
```

## Invocation Modes

### Parallel Mode
- Used for: `analyze`, `ideate`
- Pattern: Codex ∥ Gemini → Claude synthesizes

### Sequential Mode
- Used for: `code`, `paper`, `patent`
- Pattern: MCP tools → Codex → review → Claude integrates

## Model Characteristics (Non-mandatory)

| Backend | Tendency |
|---------|----------|
| Codex | Rigorous reasoning, structured decomposition |
| Gemini | World knowledge, associative thinking |

## Output Requirements

Both models MUST:
1. Follow `output_contract` structure
2. Include `Assumptions` section
3. Include `To Verify` section

## Manifest Tracking

Every Bridge call MUST be recorded in manifest:

```json
{
  "models_used": [
    {"backend": "codex", "role": "analyze"},
    {"backend": "gemini", "role": "analyze"}
  ]
}
```

## Fact Verification Rules

1. **Gemini facts are untrusted by default**
2. Any Facts from Gemini → Claude MUST call `mcp__grok-search` before final output
3. **Code content is exempt** from fact verification
