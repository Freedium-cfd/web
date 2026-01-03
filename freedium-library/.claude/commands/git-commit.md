---
allowed-tools:
  - Bash(git status:*)
  - Bash(git diff:*)
  - Bash(git log:*)
  - Bash(git add:*)
  - Bash(git commit:*)
  - Bash(git push:*)
  - Bash(git branch:*)
---

1. First, run `git diff` to see all changes (both staged and unstaged)
2. Analyze the diff to understand what changed
3. If changes cover multiple areas, split into multiple focused commits
4. Write a conventional commit message based on the diff:
  - Use format: `type(scope): description`
  - Types: feat, fix, docs, style, refactor, test, chore
  - Keep the message under 72 characters
  - Generate only a single-line commit message (no multi-line messages)
5. Stage only the relevant files with `git add <paths>`
6. Commit with the conventional commit message
7. Push to the remote branch. If the branch has no upstream, set it with `git push -u origin <branch>`
