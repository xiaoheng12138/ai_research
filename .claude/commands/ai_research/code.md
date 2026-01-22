# /ai_research:code

## Purpose

Implement code with best practices, prototyping, and multi-model review.

## Inputs

1. **Implementation Task** (required): What to implement?
2. **Target Files** (optional): Which files to modify?
3. **Libraries** (optional): Specific libraries to use?

## Steps

1. **Generate run_id**: Call `clock` agent.
2. **Context7 Lookup**: Query `mcp__context7__query-docs` for best practices.
3. **Codex Prototype**: Get Unified Diff patch from Codex(code).
4. **Claude Implementation**: Apply and refine patch to production quality.
5. **Parallel Review**: Launch Codex(review) ∥ Gemini(review).
6. **Final Decisions**: Accept/reject review findings with rationale.
7. **Output Artifacts**: Write to `artifacts/code/<run_id>.md` + `.patch` + manifest.

## Tools

| Tool | Purpose |
|------|---------|
| `mcp__context7__query-docs` | Library best practices |
| `clock` agent | Generate run_id |
| Codex(code) | Prototype generation |
| Codex(review) | Security/correctness review |
| Gemini(review) | Readability/edge case review |

## Outputs

- `artifacts/code/<run_id>.md` (primary)
- `artifacts/code/<run_id>.patch` (required - Unified Diff)
- `artifacts/manifest/<run_id>.json` (manifest)

## Output Structure

```markdown
# Code: [Task]

## Run Metadata
...

## Inputs
...

## Output

### Context7 Best Practices (Summary)
...

### Prototype Strategy (Codex)
...

### Implementation Notes (Claude)
...

### Reviews
...

### Final Decisions
| Finding | Decision | Rationale |
...

## Assumptions
...

## To Verify
...

## Next Actions
...
```
