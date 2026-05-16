# Project-local skills

Drop project-scoped skills here as folders. Each skill = a directory with `SKILL.md`.

Example layout:
```
.claude/skills/
  django-migration/
    SKILL.md
  postgres-explain/
    SKILL.md
```

These skills are **only** available when Claude Code is launched from this
repo — they will NOT leak into your other projects or company work.

Skills shipped in `~/.claude/skills/` (your global home) still load too;
project-local skills take precedence when names collide.

See https://docs.claude.com/en/docs/claude-code/skills for skill schema.
