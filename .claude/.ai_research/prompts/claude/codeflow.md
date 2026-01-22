# Role

Codeflow Prompt: Orchestrate code implementation workflow with context7, Codex prototype, and multi-model review.

# Rules

1. Query `mcp__context7__query-docs` for library best practices first.
2. Pass context7 results to Codex for prototype design.
3. Codex produces Unified Diff patch ONLY - no direct file writes.
4. Claude applies and adapts the patch to production quality.
5. Trigger parallel review: Codex(review) + Gemini(review).
6. Merge review findings, noting conflicts.
7. Record accept/reject decisions with rationale.
8. Output MUST include `.patch` file in artifacts.
9. Patch file contains ONLY necessary changes.
10. No Gork verification for code content.
11. All file changes documented in primary artifact.
12. Output MUST include `To Verify` section.

# Output Format

```markdown
## Output

### Context7 Best Practices (Summary)
1. [Best practice 1]
2. [Best practice 2]
...

### Prototype Strategy (Codex)
- Modules: [...]
- Interfaces: [...]
- Test points: [...]

### Implementation Notes (Claude)
- Files changed: [...]
- Run command: `...`
- Risks: [...]

### Reviews
**Codex Review:**
1. [Finding 1]
...

**Gemini Review:**
1. [Finding 1]
...

### Final Decisions
| Finding | Decision | Rationale |
|---------|----------|-----------|
| ... | Accept/Reject | ... |
```

## To Verify
- [ ] Tests pass
- [ ] No regressions
