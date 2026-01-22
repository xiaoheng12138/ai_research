# /ai_research:analyze

## Purpose

Deep analysis of materials with multi-model synthesis.

## Inputs

1. **Analysis Target** (required): What to analyze? (KB refs, files, or topic)
2. **Focus Questions** (optional): Specific questions to answer?
3. **KB References** (optional): Existing KB entries to include?

## Steps

1. **Generate run_id**: Call `clock` agent.
2. **Claude Preliminary**: Initial analysis and key questions (3-7).
3. **Parallel Analysis**: Launch Codex(analyze) ∥ Gemini(analyze).
4. **Fact Check**: Verify Gemini facts via `mcp__grok-search__web_search`.
5. **Claude Synthesis**: Integrate findings into unified output.
6. **Record Manifest**: Log models, MCP tools, verification status.
7. **Output Artifacts**: Write to `artifacts/analyze/<run_id>.md` + manifest.

## Tools

| Tool | Purpose |
|------|---------|
| `mcp__grok-search__web_search` | Fact verification (Gemini output) |
| `clock` agent | Generate run_id |
| Codex(analyze) | Structured reasoning |
| Gemini(analyze) | World knowledge enrichment |

## Outputs

- `artifacts/analyze/<run_id>.md` (primary)
- `artifacts/manifest/<run_id>.json` (manifest)

## Output Structure

```markdown
# Analysis: [Topic]

## Run Metadata
...

## Inputs
...

## Output

### Claude Preliminary Analysis
...

### Analysis (Codex)
...

### Analysis (Gemini)
...

### Claude Synthesis

#### Key Findings
...

#### Claims (fact/inference/speculation)
...

#### Evidence Links (KB)
...

#### Limitations
...

## Assumptions
...

## To Verify
...

## Next Actions
...
```
