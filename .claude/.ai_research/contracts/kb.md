# Knowledge Base Contract

## Directory Layout

```
.research/kb/
  items/     # Index cards (metadata + human-readable summary)
  raw/       # MinerU extracted text (by kb_id)
  files/     # PDF and large files (optional)
```

## KB Entry Format

Path: `.research/kb/items/<kb_id>.md`

### YAML Front Matter (Required Fields)

```yaml
---
kb_id: "kb:paper:20260121-0001"    # Unique and stable (type prefix recommended)
type: "paper"                      # paper|report|patent|dataset|web|note
title: "..."
authors: ["..."]                   # Can be empty array, field MUST exist
year: 2024                         # Write null if uncertain
source:
  provider: "semantic_scholar"     # semantic_scholar|doi|arxiv|url|manual
  id: "..."                        # paperId / DOI / arXivId / url_hash
url: "..."                         # Can be empty string
tags: ["..."]                      # Can be empty array
added_at: "2026-01-21"             # YYYY-MM-DD
files:
  pdf: ".research/kb/files/....pdf"           # Can be empty string
  mineru: ".research/kb/raw/<kb_id>/mineru.md" # Can be empty string
---
```

### Body Structure (Recommended)

```markdown
## Abstract
(optional)

## Key Contributions
- ...

## Methods / Key Details
- ...

## Results (if any)
- ...

## Notes
- ...

## Quotes (Optional)
> ...
```

## Rules

1. **All metadata fields MUST be present** (even if empty)
2. Use type prefixes in kb_id: `kb:paper:`, `kb:report:`, etc.
3. MinerU output goes to `.research/kb/raw/<kb_id>/mineru.md`

## Ingestion Workflow

1. `/ai_research:research` produces candidate papers
2. User selects papers
3. User runs MinerU → outputs to `.research/kb/raw/<kb_id>/mineru.md`
4. Create `.research/kb/items/<kb_id>.md` with metadata
5. Subsequent commands reference KB entries by kb_id
