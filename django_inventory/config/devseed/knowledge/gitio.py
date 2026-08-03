"""devseed.knowledge.gitio — READ-ONLY git plumbing for `--diff` mode (U2:
no staging, no checkout, nothing that touches the index; the purity suite
statically pins the verb allow-list)."""

import os
import subprocess

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

# The complete read-only verb allow-list (statically pinned by the purity test).
READ_ONLY_GIT_VERBS = ("diff", "status", "log", "rev-parse", "ls-files", "show")


def _git(*args):
    """Run one read-only git command from the repo root; returns stdout lines."""
    if args[0] not in READ_ONLY_GIT_VERBS:
        raise ValueError(f"git verb '{args[0]}' is not read-only — refused")
    out = subprocess.run(("git",) + args, cwd=REPO_ROOT, capture_output=True,
                         text=True, check=True)
    return [l for l in out.stdout.splitlines() if l.strip()]


def changed_files():
    """Working-tree changed paths (diff vs HEAD + untracked) — the `--diff`
    scope. Repo-root-relative."""
    diffed = _git("diff", "--name-only", "HEAD")
    untracked = [l[3:] for l in _git("status", "--porcelain") if l.startswith("?? ")]
    return sorted(set(diffed) | set(untracked))


def porcelain_hash():
    """The tree-state fingerprint (the Phase-0 porcelain-proof pattern) — used
    by the runtime identity proof: a sweep must never move this."""
    import hashlib
    text = "\n".join(_git("status", "--porcelain"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
