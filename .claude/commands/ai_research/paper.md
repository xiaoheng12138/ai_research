# /ai_research:paper

## Purpose

Academic paper writing with structured workflow and fact verification.

## Inputs

1. **Paper Topic** (required): What is the paper about?
2. **Target Venue** (optional): Conference/journal style?
3. **KB References** (required): Research to incorporate?
4. **Sections** (optional): Specific sections to focus on?

## Steps

1. **Generate run_id**: Call `clock` agent.
2. **Codex Outline**: Get argument chain and paper structure.
3. **Gemini Draft**: Generate initial draft following outline.
4. **Fact Extraction**: Identify factual claims in draft.
5. **Gork Verification**: Call `mcp__grok-search__web_search` for fact check.
6. **Claude Revision**: Integrate verified content, mark uncertain claims.
7. **Output Artifacts**: Write to `artifacts/paper/<run_id>.md` + manifest.

## Tools

| Tool | Purpose |
|------|---------|
| `mcp__grok-search__web_search` | Fact verification |
| `clock` agent | Generate run_id |
| Codex(analyze) | Argument chain / outline |
| Gemini(draft) | Initial draft writing |

## Outputs

- `artifacts/paper/<run_id>.md` (primary)
- `artifacts/manifest/<run_id>.json` (manifest)

## Output Structure

```markdown
# Paper: [Title]

## Run Metadata
...

## Inputs
...

## Output

### Argument Chain / Outline (Codex)
...

### Draft (Gemini)
...

### Fact Check (Gork)
| Claim | Status | Source |
...

### Revision (Claude)
...

## Assumptions
...

## To Verify
...

## Next Actions
...
```
