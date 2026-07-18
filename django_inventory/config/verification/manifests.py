"""verification.manifests — seed-manifest ingestion (contract §6.3).

Dev-world verify commands REQUIRE the world's seed manifest — the engine NEVER
seeds. Manifests are the Phase-12 machine-readable records in repo-root
`var/seed_manifests/` (format of record: SEEDER_ENGINE_LOG §SEED-F.5.1). The
path constant is computed independently here (devseed is dev-only and this
module must import cleanly everywhere); the cross-pin test keeps it identical
to `devseed.core.DEFAULT_MANIFEST_DIR` forever.
"""

import glob
import json
import os

# Repo-root var/seed_manifests — cwd-independent (the devseed pattern).
MANIFEST_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "var", "seed_manifests")


class ManifestMissing(Exception):
    """No manifest for the requested world — remediation names the seeder."""


def _seed_remedy(slug):
    if slug == "demo":
        return "seed_demo"
    if slug == "factory":
        return "seed_factory"
    return f"seed_feature {slug}"


def latest_manifest(slug, manifest_dir=None):
    """Newest manifest for `slug` (filenames embed the UTC run stamp, so the
    lexicographic max IS the latest). Raises ManifestMissing with an explicit
    remediation — the engine never seeds."""
    d = manifest_dir or MANIFEST_DIR
    paths = sorted(glob.glob(os.path.join(d, f"{slug}-2*.json")))
    if not paths:
        raise ManifestMissing(
            f"MANIFEST REQUIRED: no seed manifest for '{slug}' in {d} — run "
            f"`manage.py {_seed_remedy(slug)}` against an allowlisted scratch DB "
            f"first (the verification engine never seeds).")
    with open(paths[-1], encoding="utf-8") as fh:
        return json.load(fh)
