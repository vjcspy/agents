---
description: Tool behavior when `projects/` is gitignored (multi-project workspace)
alwaysApply: true
---

`projects/**` is ignored in `.gitignore` (except `projects/.gitkeep`). Some Trae tools may therefore miss code in `projects/` even though it exists on disk.

## What to trust in `projects/`

| Capability | Reliable? | Notes |
|---|---:|---|
| Read a file by explicit path | Yes | Prefer when user provides a path |
| Glob (file discovery) | Usually | Keep patterns narrow to avoid huge trees / nested `.git/` |
| Directory listing | Often no | May show only `projects/.gitkeep` |
| Semantic/codebase search | Often no | Index may exclude gitignored folders |
| Built-in grep/content search | Often no | May skip ignored paths |

## Operating rules

- If the user provides a path under `projects/`, read it directly. Do not “verify existence” via index-based search.
- If you must discover files, use narrow globs like `projects/<project>/<domain>/<repo>/src/**/*.ts` or `projects/**/package.json`. Avoid `projects/**`.
- Avoid index-based tools for `projects/` (semantic/codebase search, built-in grep). Prefer “glob + read”, or default shell for discovery/search.
- If you must search content, prefer default shell (filesystem search). Example:

```bash
rg --no-ignore --hidden -g '!**/.git/**' -g '!**/node_modules/**' <pattern> projects/
```

## Heuristic: detect “hidden by .gitignore”

If glob finds files under `projects/` but listing/search returns nothing, assume `.gitignore`/index exclusion and switch to “glob + read” and/or default shell.
