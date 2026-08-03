---
id: human-guide-features
type: entry-index
status: active
owner: handwritten
scope: human navigation — museum guide for this folder (kos-owned satellite; see kos/project/reading-the-docs.md)
anchors: —
verified: 2026-07-19
---

# 🧭 Human Guide — docs/features/ — the generated URL cards

> Museum guide, not an exhibit: navigation only, no content lives here.
> The full map of docs/: [kos/project/reading-the-docs.md](../../kos/project/reading-the-docs.md)

**Why does this folder exist?**
Machine-generated structural reference: one card per URL (route → view → services → models), rebuilt from the knowledge graph. An index, not truth.

**What kinds of documents live here?**
**285** generated cards + generated per-feature READMEs. DO NOT hand-edit — regeneration overwrites.

**Why only 276 and not ~560?** (2026-08-03 audit) Django-admin and allauth routes get
**no card**. They are framework CRUD — auto-generated one per model × action, carrying
zero business meaning — and they were **314 of 538** cards here (58%), drowning the 224
real app URLs. One was actively misleading: a card titled
`admin_expense_workerledgerentry_delete` presented "delete a ledger entry" as a feature
when the ledger is **append-only** by design. The exclusion lives in
`scripts/generate_docs.py` (`_CARDLESS_NAMESPACES`). Nothing is lost — the URL nodes stay
in the graph (INV-8 floor url = 559, unchanged) and the admin still works; it simply is
not documented as a product feature.

**How cards get filed** (2026-08-03): a card lands under a feature folder only when
`docs/LEARNING_2_0/PROJECT_BRAIN/FEATURE_INDEX.md` lists its **exact** url token
(`ns:name`). Rows that describe URLs in prose (`patterns_ai:*`) match nothing — the
builder **refuses to guess**, by design.

That file now carries real tokens, so **`_unassigned/` holds 3 cards instead of 224**
and there are **38 named feature folders**. Grouping follows the codebase's own view
modules (`adda_views`, `master_views`, `access_views`, …), because the app already
organises views by concern — that is the most honest grouping signal available.

**The 3 that stay unassigned, by construction:** `public_home`, `media-public`,
`media-protected` have **no url namespace** (their node id is `url:public_home`, not
`url:ns:name`), and the builder's token regex requires `ns:name`. They cannot be filed
from that file without loosening the regex — which would let prose words create false
feature edges. Left honest rather than force-fitted.

**Read first:**
Nothing linearly — LOOK UP one URL when you need its exact structural chain.

**Usually ignorable:**
Everything except the one card you came for; browsing this folder is a category error.

**Which KOS pages explain these documents?**
The WHY of any URL: its kos feature page's Related URLs table ([find-by-app](../../kos/README.md)); cards give the structural HOW.

**Engineering topics that belong here:** URL→code structure lookups
