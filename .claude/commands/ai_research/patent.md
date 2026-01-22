# /ai_research:patent

## Purpose

Patent application writing with claim structure and technical specification.

## Inputs

1. **Invention** (required): What is the invention?
2. **Technical Field** (required): Which field does it belong to?
3. **Prior Art** (optional): Known existing solutions?
4. **KB References** (optional): Research supporting the invention?

## Steps

1. **Generate run_id**: Call `clock` agent.
2. **Codex Claims**: Get claim set skeleton (independent + dependent).
3. **Gemini Draft**: Generate specification and embodiment examples.
4. **Fact Extraction**: Identify technical claims requiring verification.
5. **Gork Verification**: Check prior art risks via `mcp__grok-search__web_search`.
6. **Claude Revision**: Finalize with technical effects and feasibility.
7. **Output Artifacts**: Write to `artifacts/patent/<run_id>.md` + manifest.

## Tools

| Tool | Purpose |
|------|---------|
| `mcp__grok-search__web_search` | Prior art / fact verification |
| `clock` agent | Generate run_id |
| Codex(analyze) | Claim set skeleton |
| Gemini(draft) | Specification draft |

## Outputs

- `artifacts/patent/<run_id>.md` (primary)
- `artifacts/manifest/<run_id>.json` (manifest)

## Output Structure

```markdown
# Patent: [Invention Title]

## Run Metadata
...

## Inputs
...

## Output

### Claim Set Skeleton (Codex)
**Independent Claim 1:**
...

**Dependent Claims:**
...

### Draft (Gemini)
**Technical Field:**
...

**Background:**
...

**Detailed Description:**
...

**Embodiments:**
...

### Fact Check (Gork)
| Claim | Prior Art Risk | Source |
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
