---
id: docs-campaign-contracts-phase-10-ui-component-library
type: campaign-contract
status: active
owner: frozen
scope: campaign
anchors: —
verified: 2026-07-18
---

# Phase 10 Execution Contract — UI Component Library

> Authored 2026-07-12 under the contract-first directive. Inherits U1–U14 from
> [README.md](README.md). NOT a PHASE_05 child, but Standard-bound: its library artifact obeys
> `docs/DOC_STANDARDS.md` (typology, metadata, ownership classes) and its future
> graph/generation interfaces route through PHASE_08 KG-D6 / PHASE_09 GEN-D9 extension rules.
> **This phase operates under the owner's standing UI laws, all pre-existing and binding:**
> Design System FROZEN 2026-06-18 (Auth/Forms/Inputs/Select/Date/Financial families CLOSED —
> existing owners + tokens only; no new shared component without audit) · UI Architecture
> Rules 2026-07-05 (compose-from-canon naming the reference page · rule-of-3 · tokens-only ·
> consistency re-audit before FE-done · state-what-it-reuses) · Mobile-First as FUNCTIONAL
> requirement (CLAUDE.md rule 11; verify 360/768/1280 — canonical_manifest hard_rules) · No
> Native Dropdown (FancySelect + data-fancy-date; base.html MutationObserver) · HTML template
> checklist (canonical copy in UI_COMPONENTS.md) · CLAUDE.md rules 9/10 (check
> UI_COMPONENTS.md before CSS; page-scoped CSS in `{% block extra_head %}`; base.html additions
> only at 3+ occurrences) · U9 fit-existing-architecture.
> Charter source: master index — "Consolidate UI_COMPONENTS.md vocabulary into a certified
> component library (tokens-only, design-system-frozen rules apply)."
> Evidence doc (created at UIL-0): `docs/UI_COMPONENT_LIBRARY_LOG.md`.

## 1. Phase objective

Turn the project's existing UI vocabulary into a **certified component library**: a complete
census of every component pattern and design token in use, exactly one certified canonical
owner per pattern (with its reference page named), duplicated UI consolidated behind those
owners where the rule-of-3 licenses it, and the library documented as the Standard-compliant
single source for all future UI work. **This is consolidation + certification of what exists
— NOT a redesign, NOT a new design system, NOT a component-building spree.** Visual
consistency over redesign; existing business behavior preserved byte-for-byte (the INERT
extraction precedent: commit `14b819b2` "extract shared/_export_buttons.html owner (INERT)").

## 2. Scope

### 2.1 Facts of record (authoring-time; UIL-0 re-verifies)

| Fact | Evidence |
|---|---|
| The canon today | `UI_COMPONENTS.md` (repo root) = component vocabulary + design tokens + DataTables/fancy-select usage + the HTML checklist canonical copy (CLAUDE.md rule 9/doc header) |
| Frozen reference pair | `DESIGN_SYSTEM_SPEC` + `UI_COMPONENTS_CATALOG` — "the frozen system's reference pair" (DOCUMENT_ARCHIVE_REVIEW KEEP class) |
| CSS architecture | single-CSS-source `base.html` (tokens: `--border-card`, `--shadow-card`, …; BEM-lite; two form systems `.field` + `.sf-*`; MutationObserver auto-upgrade for selects/dates) — Frontend Architecture + Design System records |
| Frontend rules of record | `FRONTEND_AUDIT_2026_07_05.md` (FE-1..FE-5 executed + 7 permanent UI-architecture rules) |
| Prior consolidation precedent | commit `14b819b2` refactor(ui): shared `_export_buttons.html` owner, explicitly INERT — the behavior-preservation template for every Phase-10 consolidation |
| Paused adjacent stream | Frontend HTML Audit (resume anchor `docs/HTML_AUDIT_MASTER.md`; Step 0 done, HTML-001 awaiting go) + `docs/HTML_CANONICAL_CANDIDATES.md` — census INPUTS here; the stream itself stays paused (UI-D9) |
| Responsive law | mobile-first = functional requirement; every table needs an explicit responsive strategy; verification widths 360/768/1280 (manifest hard_rules); production-audit lessons: dev runserver caches templates → RESTART after template edits; `data-label` inert without `.table-responsive` ancestor |
| Known UI backlog touching this phase | backlog #3 (export_list.html inline style — tokens-only candidate "next time that template is touched") |
| What does NOT exist | no Storybook, no visual-regression tooling, no JS framework components (server-rendered Django templates + vanilla JS), no accessibility standard of record → UI-D5/UI-D6 |

### 2.2 In / out

**In:** component + token census across all app templates and base.html · taxonomy
classification (§6.2) · canon certification (one owner per pattern, reference page named) ·
duplication register + owner-gated consolidation queue · consolidation execution
(behavior-preserving template/CSS edits — the licensed build work) · responsive/mobile +
UI-D5-baseline validation · the certified library document · interfaces handoff.
**Out:** any new visual design or redesign (frozen system) · new shared components (UI-D3:
none by default; exception path = design-frozen audit + rule-of-3 evidence + owner approval)
· ANY change to the six CLOSED families without their audit+owner gate · JS framework /
build-tooling / Storybook introduction · screenshot/visual-regression TOOLING beyond the
UI-D6 method · Python/view/service/model changes (a component fix needing Python = misfiled →
Phase 4 protocol) · KOS fence-writing (library doc structured fence-READY; fences = Phase-9
GEN-D9 amendment later) · resurrecting the paused HTML audit stream (UI-D9).

## 3. Success criteria

Phase 10 is DONE when ALL hold:
1. **Census complete with arithmetic:** every template in the 9 apps + shared/ + base.html
   inventoried; every component occurrence classified into the §6.2 taxonomy; every design
   token in base.html enumerated into the token registry (UI-D7); counts reconcile against a
   mechanical template/file count.
2. **Canon certified:** every taxonomy family in use has EXACTLY ONE certified owner pattern
   with its reference page named (compose-from-canon made total); families with zero
   occurrences recorded as empty; conflicts resolved or owner-arbitrated — no pattern with
   two owners survives.
3. **Duplication resolved or registered:** every duplicate cluster either consolidated behind
   its canon (owner-selected queue, UI-D4) with INERT proof, or registered
   deferred-with-reason. Zero silent duplicates.
4. **Behavior preservation proven per consolidation:** rendered-output equivalence evidence
   (same data → same visible content/controls), browser before/after at 360/768/1280, zero
   business-logic diffs (template logic moves verbatim), battery green.
5. **Frozen families untouched** (or touched only via their recorded audit+owner gate).
6. **Validation passed:** every touched page re-verified mobile-first (responsive strategy
   stated per table — owner rule 11); UI-D5 accessibility baseline checked on touched pages;
   consistency re-audit (UI Architecture rule) run before FE-done; duplication re-census
   shows no regressions.
7. **The library document exists** (UI-D1 form): Standard-compliant (frontmatter, ownership
   class, tier), per-component entries (owner pattern · reference page · tokens used ·
   variants · responsive strategy · do/don't), token registry, extension + deprecation rules
   (§6.3) — and DOCUMENTATION_INDEX/START_HERE route to it.
8. Battery green at final state (entry baseline + any pins from confirmed fixes; template
   changes count as code — every consolidation wave runs it).
9. Interfaces handoff written (§6.6); status file + backlog (#3 disposition) + memory synced
   every sub-phase.

## 4. Rules of engagement (deltas beyond U1–U14)

- **Consolidation license is the charter, but each consolidation is owner-selected** (UI-D4
  queue at UIL-C) — the census never auto-becomes a build list.
- **INERT rule (normative):** a consolidation changes WHERE markup lives, never WHAT renders
  or does. Template logic moves verbatim; context variables unchanged; no view/form/service
  edits. A consolidation that needs Python is misfiled (stop §16.4).
- **Rule-of-3 gate:** shared extraction only at 3+ genuinely-identical occurrences (existing
  owner rule); 2 occurrences = registered, not extracted.
- **Tokens-only:** no new CSS values where a token exists; new token = UI-D7 owner gate;
  page-specific CSS stays in `extra_head` under a page class (CLAUDE.md rule 10).
- **Frozen-family firewall:** Auth/Forms/Inputs/Select/Date/Financial component families are
  read-only; a duplicate cluster inside them is REGISTERED with the audit-required flag, not
  consolidated, unless the owner grants the design-frozen audit gate per cluster.
- **One consolidation at a time** (PHASE_04 serial discipline): extract → verify (browser
  360/768/1280 after dev-server RESTART — template-cache lesson) → log → next.
- **Battery per wave:** template/CSS edits count as code (PHASE_04 FIX-C precedent) — full
  sequential battery at every UIL-D session close; pins only for confirmed FIXES discovered
  and fixed under the Phase-4 lifecycle (a rendering 500 found here = confirmed bug → fix +
  pin per PHASE_04 rules, logged in both records).
- Evidence pages use DEV-marked data only; identities per the certification cast lists.

## 5. Evidence standard

- Census numbers: commands + raw counts (template count, occurrence counts per family, token
  list extracted from base.html — quoted).
- Canon certifications: per family — the owner pattern (file/section anchor in base.html or
  shared/), the named reference page (URL + template path), and the occurrence list it now
  governs.
- Per consolidation: pre/post template diff summary · rendered-equivalence proof (same
  context → same output, method stated) · browser screenshots/notes at 360/768/1280 (after
  restart) · battery arithmetic · the INERT declaration with what-it-reuses stated
  (state-what-it-reuses rule).
- Validation: per-touched-page responsive section (owner rule 11 format) + UI-D5 checklist
  results.
- Sub-agent census sweeps supplemental (U7): canon decisions, INERT verdicts, frozen-family
  judgments, certification = main-thread.

## 6. Methodology

### 6.1 Philosophy (normative; owner-listed 2026-07-12 + standing rules, reconciled)

Component-first: every UI need answers "which certified owner do I compose from?" before any
new markup (compose-from-canon) · design-token driven (tokens-only; the UI-D7 registry is the
closed set) · mobile-first as FUNCTIONAL requirement (owner rule 11 — summary-first for
management surfaces per U9) · accessibility per the UI-D5 ratified baseline (no invented
WCAG claims) · deterministic reusable components (same include + same context ⇒ same markup;
no environment-dependent rendering) · zero duplicated UI as the end-state, reached only
through owner-gated INERT consolidations · existing business behavior preserved absolutely ·
**visual consistency over redesign** — the frozen system is the look; this phase makes usage
consistent with it, never evolves it.

### 6.2 Component taxonomy (census classes — UI-D2)

Families (a census classification, NOT a build list): **layout** (page shell, hero strip,
numbered panels, sticky CTA bar — Form Shell pattern) · **navigation** (sidebar, tabs,
breadcrumbs) · **forms** (field systems `.field`/`.sf-*`, fieldsets, validation display —
FROZEN family) · **inputs/select/date** (FancySelect, data-fancy-date — FROZEN) ·
**tables** (DataTables usage, responsive strategies: stack/cards/data-label/scroll/summary) ·
**cards** (KPI/stat/summary cards) · **badges + chips** (status, counts, zero-chip triage) ·
**dialogs/modals/confirmations** (delete-confirm pages, inline dialogs) · **notifications**
(flash/messages rendering) · **filters** (filter-inside-card pattern) · **pagination** ·
**search** · **dashboards** (dashboard tiles/sections) · **domain widgets:** production
(stage panels, console widgets, allocation rows), financial (money-family canon,
Expected→Earned→Paid ladders, ledger strips — FROZEN family), stage (trio/checklist widgets),
inventory (roll/stock cards, history timelines) · **export/print controls**
(`shared/_export_buttons.html` — the existing certified owner) · **auth** (FROZEN family).
Unlisted patterns found in census → new family rows via a dated UI-D2 amendment, never
silently binned.

### 6.3 Ownership, extension, deprecation (single source of truth)

Every certified pattern gets exactly one OWNER (a base.html block, a `shared/` include, or a
named reference implementation on its reference page) — single-writer discipline applied to
markup. **Shared vs app-specific:** shared = 3+ apps/pages use it (rule-of-3); app-specific
patterns stay in their app's templates and are documented as local variants of a canon.
**Extension rule:** need ≥80% of an existing owner → extend with a modifier class (CLAUDE.md
rule 9); less → page-scoped CSS; a genuinely new shared component = UI-D3 gate (design-frozen
audit + rule-of-3 evidence + owner approval, recorded in the Design Record). **Deprecation:**
a superseded pattern is never deleted while referenced — occurrences migrate (INERT), then
the pattern is marked deprecated in the library doc with its successor named
(supersession-names-successor, parent-Standard lifecycle applied to components); dead CSS
removal only after zero occurrences proven by re-census.

### 6.4 Design tokens (UI-D7)

The token registry = every custom property + shared value family in base.html (spacing ·
typography · colors incl. state colors · icon conventions · borders · radius ·
elevation/shadows · breakpoints [360/768/1280 verification widths vs CSS breakpoints —
enumerate BOTH, they are not the same thing] · animation/transition values). Census extracts
the ACTUAL set; the registry documents it as CLOSED; hard-coded values in templates that
shadow a token = findings (backlog #3 class — fixed only when their template is touched by a
queue item, per that row's own rule). New tokens = owner-gated (frozen system).

### 6.5 Validation (UI-D5/UI-D6)

Per touched page: responsive re-verification at 360/768/1280 (browser, after dev-server
restart) with the explicit table strategy stated · UI-D5 accessibility baseline (default
checklist: every input labelled · touch targets ≥ the baseline the owner ratifies · contrast
spot-check on state colors · keyboard operability of FancySelect/dialogs noted as
observed-behavior, not asserted) · consistency re-audit against the certified canon ·
duplication re-census over touched families · **visual regression per UI-D6 default:**
before/after screenshot pairs at the three widths, archived with the log (no new tooling; the
browser evidence pattern already used by every certification phase). Deterministic rendering:
spot-proof that the same include with the same context renders identical markup (template
render in shell, diffed).

### 6.6 Future interfaces

| Interface | Contract |
|---|---|
| Documentation Generation (Phase 9) | The library doc is authored fence-READY (structural sections isolatable); component entries become a GEN-D9 target only via a dated GEN-D2 amendment; component nodes/edges in the graph = a KG-D6 minor-version extension proposal recorded in the handoff — neither built here |
| Knowledge Sync (Phase 14) | Duplication re-census + token-shadowing detection are candidate sync checks — handed off as detector specs (detect-and-notify law), not built here |
| Deployment (phases 19–21) | The library doc joins the T2 canon the runbook references; zero deploy-time behavior (server-rendered templates only — no build step introduced, ADR-0008-adjacent simplicity preserved) |
| Future features (15–18) | New feature UI composes from certified owners (compose-from-canon made enforceable by the library doc); PDD/freeze rules unchanged — this phase adds no product behavior |

## 7. Sub-phase breakdown

Every sub-phase: one session, STOP after (U3); evidence into the library log.

| # | Scope · Inputs · Outputs · Evidence · Battery · Stop deltas |
|---|---|
| **UIL-0** — Charter + gate + ratification | Gate: Phase 9 closed (master-index order; Standard + pipeline live). Owner ratifies UI-D1..UI-D9. Verify census sources exist (UI_COMPONENTS.md, DESIGN_SYSTEM_SPEC/CATALOG, FRONTEND_AUDIT, HTML_AUDIT_MASTER, base.html). Log skeleton. **Battery:** never. **Stop:** gate fails; any UI-D unanswered. |
| **UIL-A** — Component + token census | Mechanical + judgment inventory: all templates across 9 apps + shared/ + base.html; occurrences classified per §6.2; token registry extracted (§6.4); hard-coded-value findings; frozen-family occurrence map. **Evidence:** counts + per-family occurrence tables. **Battery:** never (read-only). **Stop:** unclassifiable pattern volume suggests taxonomy gap (→ UI-D2 amendment). |
| **UIL-B** — Canon certification | Per family: certify THE owner pattern + reference page; conflict resolution (two competing patterns → owner arbitrates which is canon); duplicate clusters registered with rule-of-3 counts + frozen-family flags. **Evidence:** certification table per family. **Battery:** never (no edits — certification is documentation). **Stop:** a canon choice would require redesign (frozen system — owner). |
| **UIL-C** — Consolidation queue (owner-gated) | Build the duplication-resolution plan: per cluster — proposed owner, affected templates, INERT feasibility, risk; owner SELECTS the execution queue (UI-D4); frozen-family clusters need their per-cluster audit gate here or stay registered. **Evidence:** the queue with owner dispositions verbatim. **Battery:** never. **Stop:** owner absent for queue selection. |
| **UIL-D** — Consolidation execution (BATTERY-BEARING; repeatable — one wave per session) | Execute queue items serially per §4 INERT rule: extract/re-point → rendered-equivalence proof → browser 360/768/1280 after restart → log; backlog #3 executed iff its template is in the queue (its fix-when-touched trigger). **Full sequential battery at every wave close** (templates = code, U5); pins only for confirmed fixes (Phase-4 lifecycle, cross-logged). **Stop:** INERT proof fails (revert the item); a consolidation wants Python; frozen family without gate; battery red beyond any just-added pins. |
| **UIL-E** — Validation | §6.5 full pass over every touched page + duplication re-census + consistency re-audit + UI-D5 baseline + deterministic-render spot-proofs. Findings = fixes only via the queue (back to UIL-D wave) or registered. **Battery:** only if a fix wave ran inside it (then per UIL-D rules). **Stop:** unexplained visual/behavioral delta (revert + report). |
| **UIL-F** — Library doc + certification + handoff | Author/upgrade the UI-D1 library artifact (Standard-compliant; per-component entries; token registry; extension/deprecation rules; frozen-family register); route DOCUMENTATION_INDEX/START_HERE; reconcile UI_COMPONENTS.md/DESIGN_SYSTEM_SPEC/CATALOG roles (UI-D1 — no duplicate canon); §6.6 handoffs; queue arithmetic (selected = done + deferred-with-reason); PHASE-10 VERDICT. **Battery:** not re-run (no code since last wave). **Stop:** unaccounted queue item; library doc would fork the canon instead of unifying it. |

## 8. Deliverables

- The certified component library document (UI-D1 form) + token registry.
- Canon certification tables (one owner per family, reference pages named).
- Executed consolidations (INERT-proven, battery-green) + the deferred register.
- `docs/UI_COMPONENT_LIBRARY_LOG.md`: census · certifications · queue + dispositions ·
  per-consolidation evidence · validation results · certification + handoffs.
- Filled Design Record (UI-D1..UI-D9) + per-cluster frozen-family gates.
- Updated backlog (#3 disposition), status file, memory per sub-phase.

## 9. Files expected to change

**Docs:** `docs/UI_COMPONENT_LIBRARY_LOG.md` (new) · the library artifact per UI-D1
(UI_COMPONENTS.md upgraded in place by default) · `docs/DOCUMENTATION_INDEX.md` +
`docs/START_HERE.md` (routing rows) · `docs/DEPLOYMENT_CAMPAIGN_STATUS.md` ·
`docs/DEPLOYMENT_BACKLOG.md` (#3 if touched) · this file (Design Record + amendments) ·
memory files. **Templates/CSS (UIL-D waves ONLY, queue-scoped):** the queue items' templates ·
`shared/` includes (new owners extracted under rule-of-3) · `base.html` (only for 3+-occurrence
promotions or dead-CSS removal after zero-occurrence proof) · app GUIDE rows for new template
files (U6). **Scratchpad:** census scripts, screenshots, render-diff outputs.

## 10. Files that must never change (touching one = STOP + report)

- ANY Python: views, forms, services, models, migrations, settings, tests (pins excepted via
  the Phase-4 lifecycle for confirmed fixes) — this phase is markup/CSS only.
- The six FROZEN families' owner implementations without their per-cluster audit+owner gate.
- JS behavior contracts: the base.html MutationObserver / FancySelect / DataTables
  initialization patterns (their USAGE is census subject; their implementation is frozen-
  system — changes = owner-gated design-system work, not consolidation).
- `knowledge_graph.json` + schema + generators (KG/GEN artifacts; extensions via their own
  amendment rules) · `canonical_manifest.json` · `docs/DOC_STANDARDS.md` · T1 truth-locks ·
  closed phase logs (dated amendments only).
- `docs/HTML_AUDIT_MASTER.md` beyond a consumed-as-input note (UI-D9 — the paused stream is
  not silently resurrected or closed).
- Non-DEV data · the 2 stashes · `.git` state (U2).

## 11. Documentation update rules

At every sub-phase close, same session: (a) library-log section appended (closed sections
append-only, corrections dated); (b) status-file Phase-10 row + dashboard (battery row updates
at each UIL-D wave) + "Next action"; (c) DOCUMENTATION_INDEX: log row at UIL-0, library-doc
row at UIL-F; (d) **U6 fully applies in UIL-D** (template changes = code changes): app
GUIDE/README rows for moved/new template files + CHANGE_IMPACT_MATRIX consultation per
changed file; (e) backlog #3 struck-with-pointer iff executed.

## 12. Memory update rules

Agents with persistent memory: update `project_deployment_campaign_2026_07_12.md` (Phase-10
bullet: sub-phase closed, consolidations done/deferred, battery number, log pointer) +
MEMORY.md index line at each sub-phase close. Agents without memory: skip — the library log +
status file are the complete binding record.

## 13. Battery policy

Sequential fresh-DB canonical (U5). **Battery-bearing: every UIL-D wave** (and any UIL-E fix
wave) — template/CSS edits count as code (PHASE_04 FIX-C precedent). Expected = entry
baseline (status dashboard at UIL-0) + any pins from confirmed fixes; arithmetic recorded per
wave. UIL-0/A/B/C/F: battery never runs (read-only/docs-only). Dev-server restart before any
browser evidence after template edits (production-audit lesson — a stale render invalidates
the evidence, not just the fix).

## 14. Regression policy

- Per consolidation: rendered-equivalence + three-width browser proof + battery = the
  regression instruments; the INERT declaration is falsifiable evidence, not a promise.
- Prior-fix guard: any touched template that hosts a prior certification fix (#5
  delete-confirm class, MGT-B-1 flash class) gets that behavior re-proven in the wave's
  browser pass.
- Certified canons from UIL-B are not re-litigated in later waves; a canon found wrong =
  dated UIL-B amendment (owner), not a silent switch.
- Duplication re-census at UIL-E guards against consolidations quietly introducing NEW
  variants.
- Pins only for confirmed fixes (U4); consolidations themselves add no pins (they change no
  behavior — the battery + equivalence proofs guard them).

## 15. Rollback policy

- Per consolidation item: revert = restore the original template bytes + remove the extracted
  include if nothing else references it (both sides logged); serial discipline keeps items
  independently revertable.
- A red battery or failed equivalence proof reverts the ITEM (not the wave) first; wave-level
  revert only if the item revert doesn't restore green.
- CSS promotions to base.html revert cleanly (additive blocks); dead-CSS removals are staged
  LAST in a wave and only after the zero-occurrence re-census (so their revert is never
  entangled with extractions).
- The library log + Design Record are append-only (dated amendments).
- Session crash mid-wave: next session re-runs the touched-file render/browser checks FIRST,
  reconciles the log, completes or reverts the half-done item before new work.

## 16. Stop conditions (end session immediately, report, await owner)

1. Sub-phase complete (normal stop, U3).
2. UIL-0 gate fails or any UI-D1..D9 unanswered; UIL-C owner queue selection missing at
   UIL-D start.
3. A frozen-family cluster would be touched without its per-cluster audit+owner gate.
4. A consolidation needs Python/view/form/service changes, or its INERT proof fails after one
   revert-and-retry (misfiled work → Phase-4 protocol or owner).
5. Redesign pressure: a canon decision or consolidation "improves" visuals beyond the frozen
   system (visual-consistency-over-redesign breached).
6. Battery red beyond any just-added pins' target behavior; or a browser pass reveals a
   behavioral delta on a DEV workflow.
7. A new-shared-component urge without the UI-D3 gate (rule-of-3 evidence + audit + owner).
8. Token registry conflict: a needed value has no token and the owner gate for a new one is
   absent.
9. Evidence contradicts a CLOSED certification (a consolidation exposes a permission/render
   defect) — record per U12, report; money-adjacent ⇒ U8.
10. Corpus/template drift from non-campaign activity mid-phase.

## 17. Resume instructions (zero chat history assumed)

1. Read `docs/DEPLOYMENT_CAMPAIGN_STATUS.md` → Phase-10 row: which UIL-* is next; battery
   baseline.
2. Read `docs/campaign_contracts/README.md` (U1–U14 + environment) → this contract FULLY →
   `UI_COMPONENTS.md` + `FRONTEND_AUDIT_2026_07_05.md` (the standing UI laws) →
   `docs/UI_COMPONENT_LIBRARY_LOG.md` if it exists (absent ⇒ next = UIL-0): closed sections,
   Design Record, the UIL-C queue dispositions.
3. Verify read-only: census-source files present; if mid-UIL-D, the queue's next item's
   templates unchanged since UIL-C (drift → re-census that cluster before touching it);
   git HEAD vs status file.
4. Browser evidence requires the dev server on :8003 (restart after template edits —
   framework env facts + the template-cache lesson); DEV data + cast-list identities only.
5. Battery environment per framework env facts for UIL-D waves.
6. Execute exactly ONE sub-phase per §7 (UIL-D: one wave, items strictly serial). STOP per
   §16.
7. Anything inconsistent across status file / library log / queue / this contract / the
   standing UI rules → report before working (framework conflict rule).

---

# Appendix A — Design Record (the ONLY sections of this frozen contract filled in later, plus dated amendments)

## Decision half (UIL-0)

| # | Item | Default (binding unless overridden) | Owner answer |
|---|---|---|---|
| UI-D1 | Library artifact form | `UI_COMPONENTS.md` upgraded IN PLACE to the Standard-compliant certified library (it is already the canon per CLAUDE.md rule 9 — no parallel doc, no fork); DESIGN_SYSTEM_SPEC + UI_COMPONENTS_CATALOG remain the frozen reference pair, cross-linked with roles stated; no Storybook/new tooling | **ACCEPT** (owner 2026-07-16, verbatim "UI-D1 — ACCEPT"; no override) |
| UI-D2 | Taxonomy | §6.2 families as the census classes; domain widgets (production/financial/stage/inventory) included; new families only via dated amendment | **ACCEPT** |
| UI-D3 | New-component policy | ZERO new shared components in Phase 10 by default; exception = design-frozen audit + rule-of-3 evidence + owner approval, recorded here per component | **ACCEPT** |
| UI-D4 | Consolidation scope | Owner selects the execution queue at UIL-C from the duplication register; rule-of-3 threshold binding; frozen-family clusters excluded unless per-cluster gated | **ACCEPT** |
| UI-D5 | Accessibility baseline | Pragmatic checklist (labelled inputs · touch-target floor · state-color contrast spot-checks · observed keyboard behavior recorded) — NO WCAG-level conformance claim (no repo standard exists to certify against; adopting one = owner decision) | **ACCEPT** |
| UI-D6 | Visual-regression method | Before/after screenshot pairs at 360/768/1280 per touched page, dev-server restarted, archived with the log; no new tooling | **ACCEPT** |
| UI-D7 | Token registry | Extracted from base.html as the CLOSED set (spacing/typography/colors+state/icons/borders/radius/elevation/breakpoints/animation); CSS breakpoints and the 3 verification widths enumerated separately; new token = owner-gated | **ACCEPT** |
| UI-D8 | Graph/generation interface | Component nodes/edges = KG-D6 minor-extension PROPOSAL + library-doc entries as GEN-D9 target candidate — both written into the UIL-F handoff, neither built in Phase 10 | **ACCEPT** (also the Phase-10 KOS-compat venue per the owner's 2026-07-16 permanent guidance — record-only) |
| UI-D9 | Paused HTML-audit stream | `HTML_AUDIT_MASTER.md` + `HTML_CANONICAL_CANDIDATES.md` consumed as census INPUTS; the stream stays paused (not resurrected, not closed); its disposition = owner decision at a later docs phase | **ACCEPT** |

Date · answered by: **2026-07-16 · owner, verbatim ("I accept all default decisions. UI-D1 — ACCEPT … UI-D9 — ACCEPT. No overrides.") — UIL-0 CLOSED; UIL-A authorized by the same order.**

## Per-cluster frozen-family gates

_(added as rows if/when the owner grants any)_

## Dated amendments

- **A1 (2026-07-16, UIL-B — §6.2 taxonomy, minimal per the owner's OD-UIL-1 subtype-first
  ruling):** the **domain widgets** family's enumerated domain list gains **patterns**
  (patterns_ai SVG workspaces, `_design_row` atom, readiness matrices — a real product domain
  with 37 templates whose absence from the production/financial/stage/inventory enumeration
  was an authoring-time gap). **NO new top-level families** — the owner-ordered
  classification review (log §UIL-B.1) resolved every other census residue as a SUBTYPE of
  an existing family (icon-dispatch→navigation · behavior-partials→their owning family ·
  embed-shells→domain:production · print-documents→export-print · standalone
  documents→layout · input/feedback widgets→forms · disclosure→dialogs · temporal
  pager→pagination · vendor pins→tables). Taxonomy stays at 17 families. Owner rulings of
  record same session: UIL-A ACCEPTED · OD-UIL-2 ACCEPT (styleguide exemption) · OD-UIL-3
  ACCEPT (dormant auth pair register-only).

# Evidence note

All census, certification, consolidation, and validation evidence lives in
`docs/UI_COMPONENT_LIBRARY_LOG.md` (created at UIL-0) — contract = procedure, log = what was
certified and consolidated (framework hierarchy rule). The certified library document is the
phase's lasting canon; the log is its proof.
