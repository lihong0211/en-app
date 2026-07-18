---
name: project-audit
description: "Systematic audit, categorization, and incremental fixing of codebase issues—bugs, hygiene, dependencies, configuration, security, and architecture. Use this skill when auditing a codebase for improvements, cleaning up technical debt, modernizing dependencies/configuration, or investigating multiple categories of issues at once."
trigger: "Use this skill when auditing a codebase for improvements, cleaning up technical debt, modernizing dependencies/configuration, or investigating multiple categories of issues at once."
author: lihong0211yao
source_sessions:
  - lihong0211yao_lihong0211yao's Organization_default_25d5b3c3-e2ac-4a31-bfe1-7b7bacfe0029
contributors:
  - lihong0211yao
version: 1
created_by_agent: claude_code
created_at: 2026-07-14T19:23:52.833Z
updated_at: 2026-07-14T19:23:52.833Z
---

# Project Audit & Modernization Workflow

When auditing a codebase for technical debt or improvements, use a systematic three-phase approach: discover and categorize issues, execute fixes incrementally with verification, and report deferred decisions.

## When to Apply

Use this skill when:
- Auditing a codebase for improvements or debt
- Cleaning up a project's technical debt
- Modernizing outdated dependencies or configuration
- Investigating multiple categories of problems at once
- Asked to "review this project" or "fix whatever's broken"

## Phase 1: Audit & Categorize

1. **Read key files** — project structure, main entry points, config files, dependencies

2. **Identify issues across categories**:
   - **Critical Bugs** — will crash/fail at runtime (e.g., missing imports, broken attribute access, double initialization)
   - **Repository Hygiene** — git-tracked build artifacts, `.venv/`, `__pycache__/`, `dist/`, `build/`
   - **Dependencies** — duplicates, unused imports, conflicting packages, version mismatches
   - **Configuration & Docs** — scripts with wrong paths, outdated setup instructions, misaligned documentation
   - **Security Policy** — CORS/auth misconfiguration, hardcoded secrets, insecure defaults
   - **Architecture** — structural redundancy, design trade-offs needing discussion

3. **Rank by severity and actionability**:
   - Must-fix bugs (cause immediate failures)
   - Hygiene issues (repo cleanliness)
   - Dependencies (prevent runtime conflicts)
   - Config/docs (align with reality)
   - Security config (needs explicit decision)
   - Structural (requires design discussion)

4. **Present findings** grouped by category, noting which can be fixed autonomously vs. which need user decision

## Phase 2: Incremental Fixing

1. **Execute in batches** — fix bugs first, then hygiene, then dependencies, then config. Never batch bugs with architecture changes.

2. **After each batch**:
   - Verify syntax (`py_compile`, JSON validation, grep for imports)
   - Check git status to confirm changes are tracked
   - Summarize what changed and why

3. **Distinguish categories when deciding what to fix**:
   - Pure bugs: fix without asking
   - Hygiene/dependencies: fix with confirmation
   - Security config: flag as policy choice, ask before changing
   - Architecture: defer entirely, discuss with user first

4. **Report secondary findings** discovered during execution. Ask user about priorities before proceeding.

## Phase 3: Summary & Deferred Items

1. **Track completions** — list what was fixed, grouped by category
2. **List deferred decisions** — flag security/architecture items that need user input
3. **Ask next steps** — offer to tackle remaining items or ask for guidance

## Anti-Patterns

- **Don't audit without categorizing.** Lumping all issues together hides priorities and risks.
- **Don't fix architecture without asking.** Only you know design intent; just flag it.
- **Don't ignore secondary findings.** Mention new issues discovered during execution and ask about priorities.
- **Don't skip verification.** Check git status and syntax after each batch of changes.
- **Don't mistake policy for bugs.** CORS config, auth strategy, and security defaults are design choices, not errors.
- **Don't batch unrelated changes.** Keep bugs separate from hygiene/config/architecture to isolate risk.

## Output Format

```
## Critical Bugs (Fix Now)
- [file:line] Issue + impact + fix

## Repository Hygiene (Fix With Confirmation)
- Artifact/cache path tracked in git
  Fix: git rm --cached, add to .gitignore

## Dependencies (Review & Fix)
- Duplicate or unused entry
  Fix: Remove/consolidate

## Configuration (Update & Verify)
- Path/script mismatch, stale docs
  Fix: Align with actual code

## Security (Needs Discussion)
- Insecure default or config combination
  Note: Flag, don't change without explicit confirmation

## Architecture (Deferred)
- Structural redundancy or design issue
  Note: Requires design decision, not autonomous fix
```

## Execution Checklist

- [ ] Audit complete; categorized and ranked
- [ ] User confirms which items to fix
- [ ] Fix bugs and verify syntax
- [ ] Clean repository (git index, .gitignore)
- [ ] Update dependencies and verify resolution
- [ ] Update config/scripts/docs and verify alignment
- [ ] Report secondary findings discovered
- [ ] Confirm deferred items for next phase
