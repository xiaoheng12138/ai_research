# /ai_research:research

## Purpose

Literature search, paper discovery, and KB ingestion guidance.

## Inputs

1. **Research Topic/Question** (required): What are you researching?
2. **Scope** (optional): Broad survey or focused search?
3. **Year Range** (optional): Filter by publication years?

## Steps

1. **Domain Scan** (optional): Use `mcp__grok-search__web_search` for keyword clustering.
2. **Build Queries**: Construct semantic scholar search queries.
3. **Search Papers**: Call `mcp__semantic-scholar__papers-search-basic`.
4. **Advanced Filter** (optional): Use `mcp__semantic-scholar__paper-search-advanced` if needed.
5. **Present Candidates**: Show top 20 papers with metadata.
6. **User Selection**: Ask user to select papers for ingestion.
7. **Generate KB Instructions**: Provide MinerU extraction steps.
8. **Output Artifacts**: Write to `artifacts/research/<run_id>.md` + manifest.

## Tools

| Tool | Purpose |
|------|---------|
| `mcp__grok-search__web_search` | Domain scan, keyword discovery |
| `mcp__semantic-scholar__papers-search-basic` | Paper search |
| `mcp__semantic-scholar__paper-search-advanced` | Filtered search |
| `clock` agent | Generate run_id |

## Outputs

- `artifacts/research/<run_id>.md` (primary)
- `artifacts/manifest/<run_id>.json` (manifest)
- `artifacts/research/<run_id>.bib` (optional, user-selected papers)

## Output Structure

```markdown
# Research: [Topic]

## Run Metadata
...

## Inputs
- Topic: ...
- Scope: ...

## Output

### Domain Scan (Optional)
...

### Search Queries
...

### Candidate Papers
| # | Paper ID | Year | Title | Citations |
...

### User Selection
...

### MinerU Ingestion Instructions
...

## Assumptions
...

## To Verify
...

## Next Actions
...
```
