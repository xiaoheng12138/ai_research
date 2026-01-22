# Artifacts Contract

## Run ID Format

```
run_id = <YYYYMMDD-HHMMSS>-<short>
```

- `YYYYMMDD-HHMMSS`: Provided by `clock` agent
- `<short>`: 4~8 character random string

## Directory Structure

Each command execution MUST generate:

1. **Primary Artifact**: `artifacts/<command>/<run_id>.md`
2. **Manifest**: `artifacts/manifest/<run_id>.json`
3. (code only) **Patch**: `artifacts/code/<run_id>.patch`

## Primary Artifact Structure (Required)

All `<run_id>.md` files MUST contain these sections in order:

```markdown
# Title

## Run Metadata
- run_id: ...
- created_at: ...
- command: ...
- kb_refs: [...]
- mcp_used: [...]
- models_used: [...]

## Inputs
(User request summary + KB references)

## Output
(Core results - command-specific subsections)

## Assumptions
(Premises and assumptions made)

## To Verify
(Points requiring verification; write "None" if empty)

## Next Actions
(<= 5 recommended next steps)
```

## Command-Specific Output Sections

### research
- `### Domain Scan (Optional)`
- `### Search Queries`
- `### Candidate Papers`
- `### User Selection`
- `### MinerU Ingestion Instructions`

### analyze
- `### Claude Preliminary Analysis`
- `### Analysis (Codex)`
- `### Analysis (Gemini)`
- `### Claude Synthesis`
  - `#### Key Findings`
  - `#### Claims (fact/inference/speculation)`
  - `#### Evidence Links (KB)`
  - `#### Limitations`

### ideate
- `### Problem Restatement`
- `### Idea Pool (Codex)`
- `### Idea Pool (Gemini)`
- `### Claude Synthesis (Top-N)`
- `### Minimal Experiment Plan`

### code
- `### Context7 Best Practices (Summary)`
- `### Prototype Strategy (Codex)`
- `### Implementation Notes (Claude)`
- `### Reviews`
- `### Final Decisions`

### paper
- `### Argument Chain / Outline (Codex)`
- `### Draft (Gemini)`
- `### Fact Check (Gork)`
- `### Revision (Claude)`

### patent
- `### Claim Set Skeleton (Codex)`
- `### Draft (Gemini)`
- `### Fact Check (Gork)`
- `### Revision (Claude)`
