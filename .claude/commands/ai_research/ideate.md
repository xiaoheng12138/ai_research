# /ai_research:ideate

## Purpose

Generate and evaluate ideas through multi-model collaboration.

## Inputs

1. **Problem Statement** (required): What problem to solve?
2. **Constraints** (optional): Any limitations or requirements?
3. **KB References** (optional): Context from existing research?

## Steps

1. **Generate run_id**: Call `clock` agent.
2. **Problem Restatement**: Clarify the problem in 1-5 lines.
3. **Parallel Ideation**: Launch Codex(ideate) ∥ Gemini(ideate).
4. **Claude Synthesis**: Deduplicate, cluster, rank top 5 ideas.
5. **Experiment Planning**: Define 1-3 minimal validation experiments.
6. **Record Manifest**: Log models and process.
7. **Output Artifacts**: Write to `artifacts/ideate/<run_id>.md` + manifest.

## Tools

| Tool | Purpose |
|------|---------|
| `clock` agent | Generate run_id |
| Codex(ideate) | Actionable, testable ideas |
| Gemini(ideate) | Creative, divergent ideas |

## Outputs

- `artifacts/ideate/<run_id>.md` (primary)
- `artifacts/manifest/<run_id>.json` (manifest)

## Output Structure

```markdown
# Ideation: [Problem]

## Run Metadata
...

## Inputs
...

## Output

### Problem Restatement
...

### Idea Pool (Codex)
...

### Idea Pool (Gemini)
...

### Claude Synthesis (Top-N)
| # | Idea | Value | Feasibility | Experiment | Risk |
...

### Minimal Experiment Plan
...

## Assumptions
...

## To Verify
...

## Next Actions
...
```
