# P5 FACTORY ROLLOUT GUIDE (2026-07-07)

## 1. Roles & permissions (existing RBAC; nothing invented)
| Role | Sees |
|---|---|
| super_admin, manager | Pattern Intelligence sidebar entry → ALL surfaces (home, library, yield, mats, pieces, generate, advisor, insights) + the Adda-detail entry links |
| worker | NOTHING (every URL 403s; sidebar rule scopes to management — test-walled) |
| accountant / listing_team | nothing (unchanged) |

Sidebar rollout = already-seeded `SidebarItemRule` (`seed_patterns_ai_sidebar`,
idempotent); menu + URL co-gated by the standing middleware (V1 rule 6).

## 2. Onboarding sequence (per manager/cutting master)
1. Tour (30 min): home → marker library → record a usage + outcome on a
   real lay → watch the Yield Board move.
2. Mat ritual (owner + master together): commission per
   [D7_VALIDATION_PROTOCOL](D7_VALIDATION_PROTOCOL.md).
3. Geometry week: register pieces, capture one product's set, confirm
   with grain + tape.
4. Advisor habit: before each cut, open Cut Advisor from the Adda page;
   record the suggestion + decision (30 seconds).

## 3. SOPs (laminate these three)
**SOP-1 Capture:** piece flat ON the mat · whole mat in frame · phone
flat · no shadows · gate refused? read the reasons, retake · accept only
what looks right in the annotator · confirm = grain + tape numbers.
**SOP-2 Outcome recording (the fuel):** after every lay: marker page →
record usage (adda, plies, repeats) → after cutting: record outcome
(metres issued, garments cut/packed, leftover). Wrong entry? VOID with
the reason and re-record — never leave silent garbage.
**SOP-3 Advisor decisions:** open from the Adda → read the evidence (n
matters; 20/100 confidence = thin evidence, not a broken tool) → record
the suggestion → record YOUR decision (reject needs the reason — that
reason is knowledge).

## 4. 4-week adoption plan
| Week | Goal | Success signal |
|---|---|---|
| 1 | outcomes habit on existing manual markers | ≥1 outcome/lay recorded |
| 2 | mat commissioned + first product's geometry confirmed | trust grades visible on version page |
| 3 | first generation run + trial of one UNTESTED promoted marker | its first real outcomes on the Yield Board |
| 4 | advisor-before-every-cut habit + weekly Insights glance | suggestion history filling; acceptance rate meaningful |

## 5. Production acceptance checklist (owner signs)
- [ ] `patterns_ai_health` HEALTHY on the production box
- [ ] media sweep clean (corrupt=0 missing=0)
- [ ] D7 protocol PASSED and results addendum filled
- [ ] one real product end-to-end: capture→confirm→generate→promote(or
      refuse honestly)→usage→outcome→advisor shows it
- [ ] backups verified by an actual restore drill
- [ ] SOPs printed; roles verified (worker sees nothing)
- [ ] checkpoint commit + tag taken by the owner

## 6. Support & escalation
Gate refusals = normal (retake). DEGRADED health = ops (runbook §5).
Numbers look wrong = they derive from rows: open the marker's biography /
candidate's run / suggestion payload — the evidence chain answers before
anyone debugs code.
