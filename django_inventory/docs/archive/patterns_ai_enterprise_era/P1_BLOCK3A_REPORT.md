# P1 — BLOCK 3A REPORT: Capture Foundation (2026-07-06)

**Status: ✅ BLOCK 3A COMPLETE — STOPPED. Block 3B will NOT start without
explicit owner approval.**

## Scope compliance
Capture foundation ONLY: model + media lifecycle + backend upload pipeline +
single-writer service + tests + docs. **No image processing, no OpenCV, no
CV/AI, no derived files, no Product-UI, no yield board, no geometry, no
browser workflows** (no UI exists in this block — browser smoke N/A, stated).
Pins consciously moved: exactly-9 models; the no-FileField pin became
"FileField confined to `models/capture.py`".

## Model summary — `CaptureAsset` (migration `patterns_ai.0003`)

Immutable knowledge-class original: product-homed (owner vision) · kind
(marker_photo / pattern_capture-reserved) · source (camera/gallery) ·
**hash-named storage** `media/patterns_ai/<product>/originals/<sha16>.<ext>`
(client filenames never touch paths — traversal structurally impossible) ·
sanitized display filename · verified content_type · size · **sha256 anchor** ·
status stored/corrupt/retired with **reason-required CHECKs** · optional
`mat` FK (custody chain, geometry era) · versioned metadata JSON ·
uploaded_by. **Immutability = belt and braces:** `save()` refuses changes to
identity fields (file/sha/size/type/product/kind/source), `delete()` refuses
always; DB backstops: UNIQUE(product, sha256), size>0, negative-status⇒reason.

## Service summary — `capture_service` (single writer, I-1-guarded)

- `store_capture(user, product, uploaded_file, source, kind, mat, metadata)` —
  management gate → size caps (1 KB–15 MB, deploy-overridable) → **magic-byte
  sniffing** (content decides the type; client headers/extensions are never
  trusted) → streaming SHA-256 → per-product duplicate refusal naming the
  existing asset → atomic row+file persist.
- `retire_capture(user, asset, reason)` — the only correction path (F5);
  file kept forever.
- `verify_asset(asset)` — read-only re-hash → ok/mismatch/missing.
- `mark_corrupt(asset, detail)` — sweep writer; corrupt originals stay as
  evidence.

## Media lifecycle (ADR-G, implemented)

Knowledge class = originals, forever (retire ≠ delete; files survive retire —
test-proven). Storage layout per ADR-G. **Integrity verification** =
`manage.py verify_patterns_media`: re-hashes every non-retired asset
(mismatch/missing → corrupt with recorded detail) and reports disk files
without rows as **ORPHAN WARN-with-context (readiness N-7 — rollback
leftovers are not corruption)**. No derived-file class exists yet (nothing
produces derived files in this block — documented).

## Test summary — patterns_ai suite now **57 tests, all green**

Security: EXE masquerading as .png **refused by content**; JPEG with a lying
.png name accepted AS jpeg (content wins, stored .jpg); WEBP RIFF check;
undersize/oversize caps; `../../etc/passwd`-style names neutralized in both
storage and display; management gate. Duplicates: same bytes+product refused
with the existing asset id in the message; same bytes on another product
allowed. Immutability: sha/size edits refused, delete refused, retire
requires reason, double-retire refused, file survives retirement. Integrity:
ok → tamper-on-disk → sweep flags corrupt with sha-mismatch reason; deleted
file → missing; orphan file → WARN + `orphans=1` summary, no asset flagged.
Plus all prior walls (purity, I-1 now covering CaptureAsset, pins).

## Validation
Full manufacturing suite serial ✅ · patterns_ai 57/57 ✅ ·
`makemigrations --check` clean ✅ · import-linter unchanged ✅ · docs (app
GUIDE) updated ✅ · browser smoke N/A (no UI in scope).

## Engineering review

1. **Technical debt:** no capture provenance beyond client-declared metadata —
   EXIF/device profiling is geometry-era scope (ADR-E), deliberately absent;
   upload UI does not exist yet (next block decides where captures are born).
2. **Performance:** sweep cost is O(total bytes) — fine now; at deploy it
   becomes an off-hours cron (runbook line when P1 ships operationally).
3. **Security:** originals are never served raw by anything (no view exists);
   when UI lands, renditions-only serving is the ADR-G rule to enforce +
   test. Magic-byte checks stop disguised executables; hash naming stops
   traversal by construction.
4. **Long-term maintenance:** content-hash naming gives free dedup visibility
   and stable references; retire/corrupt reasons keep the asset story
   queryable forever.
5. **Future ADR candidates:** DB-level grants/triggers hardening the
   append-only tables (events + captures) — same candidate as 2C, now
   covering two tables.

## Findings
None blocking. Foundation ready for Block 3B (wiring captures to manual
markers + the first UI, at your definition).

**Awaiting owner approval for Block 3B.**
