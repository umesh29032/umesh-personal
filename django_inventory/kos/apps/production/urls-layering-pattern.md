---
id: app-production-urls-layering-pattern
type: app
verified: 2026-07-27
knowledge_confidence: verified_against_code
answers: "Every Layering and Pattern-Design workspace URL — each action's full learning story."
related: [app-production-urls]
---

# production URLs · Part 3 — Layering (8) + Pattern Design (10)

> 📂 [URL index](urls.md) · [production app](README.md) · [LOS home](../../README.md)
> Workspace pattern: one GET workspace + focused POST actions — every
> action = one service verb (`stages/layering/service.py` ·
> `stages/cutting_pattern/service.py`). Gates: stage skill ∩ assignment via
> mixins. All under `addas/<code>/…`.

> 💡 **Samjho aise** — URLs = **address book**
>
> Yeh file batati hai kaunsa web address (jaise `/production/addas/`) kis view pe jaata hai. Jab aapko pata na ho ki koi page kis code se banta hai — **hamesha yahin se shuru karo**.
>
> *(`production` app ka kaam: **factory floor** — Adda, stages, worker ka kaam, allocation. Project ka dil yahin hai.)*

## Layering — cloth meets table

**Mental model:** loading the oven. Nothing bakes until ingredients are
weighed IN and, at the end, what's left over is weighed BACK. The weighing-
back (leftovers) is not cleanup — it's the whole point (cloth = money).

### `layering/` — `layering-workspace`
GET → `LayeringWorkspaceView`. The console: attached rolls, weights, actions. Read-only assembly; **why simple:** actions live on their own URLs below (one-verb-one-URL keeps POSTs auditable).

### `layering/start/` — `layering-start`
POST → handler start: ASR in-progress, timestamps auto. Simple by design.

### `layering/attach-roll/` — `layering-attach-roll`
POST: attach a `ClothRoll` (cross-app READ of raw_materials; the roll's adda FK binds it — 1 roll → 1 adda).
**Writes:** `LayeringRollEntry` (+ roll binding). **Failure modes:** roll already bound elsewhere → refused. **Lesson:** cross-app writes go through THIS app's stage handler; raw_materials stays master-data-only.

### `layering/use-leftover/` — `layering-use-leftover`
POST (V1.1 item-2): re-issue a tracked LEFTOVER piece into this Adda.
**Why it exists:** leftovers are wealth ([models.md](models.md) `RemainingClothOfClothRoll`) — reuse must be as easy as fresh cloth or nobody reuses.
**Writes:** consumes the leftover row into an entry (history preserved).

### `layering/quick-create-roll/` — `layering-quick-create-roll`
POST: create-and-attach a roll in one step (floor reality: cloth arrives AT the table).
**Lesson:** the quick path still runs BOTH services' validations — convenience compresses steps, never guards.

### `layering/entries/<pk>/remove/` — `layering-entry-remove`
POST: detach an entry pre-complete. **Why allowed:** production truth is correctable until consumed ([two-truths](../../concepts/architecture/two-truths.md)); after complete, the reopen gate owns corrections.

### `layering/complete/` — `layering-complete` ⭐
POST → handler complete: **LEFTOVERS MANDATORY** — every attached roll accounts its remainder before the stage closes.
```
[@atomic] validate: every roll has weights + leftover recorded → REFUSE
listing the gaps → ASR complete (duration auto) → timeline
```
**Failure modes:** missing leftover (names the roll) · mid-work C3 class.
**Why the hard gate:** unrecorded remainder = silently lost cloth; the refusal converts forgetfulness into a checklist.
**Non-payable note:** layering is a production-INPUT stage (stage-trio spec) — no pay lines originate here (misconception guard).

### `layering/reopen/` — `layering-reopen` 🔐
POST (admin): guarded unlock — refused if downstream consumed (cutting ran on this lay). Same reverse-first peel as [generic reopen](urls-adda.md).

---

## Pattern Design — verification with evidence

**Mental model:** the pre-flight WALKAROUND. The pattern master doesn't
build the plane; they verify every checklist item on the layered cloth and
PHOTOGRAPH the proof. Fixed pay (per-Adda) because the value is the
verification, not the piece count.

### `pattern/` — `pattern-workspace`
GET → `PatternWorkspaceView` (`views/pattern_stage_views.py`). The checklist console: ProductPatternAssignments to verify, photos, video, sizes. Read-only assembly.

### `pattern/start/` — `pattern-start`
POST: begin. Simple.

### `pattern/save/` — `pattern-save`
POST: save the walkthrough VIDEO evidence. **Why video:** disputes about "was it checked" die against footage.

### `pattern/photos/add/` — `pattern-photos-add` · `pattern/photos/<pk>/remove/` — `pattern-photo-remove`
POST pair: photo evidence in/out (remove = pre-complete correction lane).
**Why individually documented though tiny:** you'll SEARCH for exactly one of them; each is one service verb writing/removing a `CuttingPatternPhoto`.

### `pattern/verify/` — `pattern-verify` · `pattern/unverify/` — `pattern-unverify`
POST pair: tick/untick a checklist item (`CuttingPatternVerification`).
**Lesson:** verification is per-COMPONENT rows, not a boolean on the record — granular truth survives partial redo (unverify exists because walkarounds find problems).

### `pattern/sizes/` — `pattern-set-sizes`
POST: per-size proportions (`CuttingPatternSizeAllocation`) — the size math cutting will consume.

### `pattern/complete/` — `pattern-complete` ⭐
POST → handler complete: checklist satisfied? evidence present? → ASR complete.
**FIXED-pay interaction (the money edge):** this stage's pay = rate × 1 exactly ONCE — a second worker's completed report is refused NAMING the first ([stage-tracking §guards](../../features/stage-tracking.md), R8 WP-4).
**Failure modes:** unverified components (named) · missing evidence.

### `pattern/reopen/` — `pattern-reopen` 🔐
POST (admin): mirror of layering-reopen — same guard walk.

## Learning Graph (this file)
**Before:** [urls-adda.md](urls-adda.md) (how stages start/complete generically — these workspaces specialize it).
**After:** [urls-cutting-barcode.md](urls-cutting-barcode.md) — where the verified lay becomes counted pieces.
