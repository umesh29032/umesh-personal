# Project-local subagents

Drop `.md` files here with a YAML frontmatter to define repo-scoped subagents.
They are only loaded when Claude Code runs from this directory.

Example `django-debugger.md`:
```markdown
---
name: django-debugger
description: Django-specific bug hunter. Reads tracebacks, models, and migrations.
tools: Read, Grep, Bash
---
You are a Django 5.x expert. When invoked, find the root cause, never silence errors.
```
