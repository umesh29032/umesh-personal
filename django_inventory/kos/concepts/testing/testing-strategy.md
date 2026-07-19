---
id: concept-testing-strategy
type: concept
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "How does one developer trust a 1,878-test system with real money — what do the tests actually PIN?"
related: [concept-pg-constraints, concept-query-performance, feature-settlement]
---

# Testing Strategy — pin the truth, not the coverage number

> 📂 [Testing concepts](README.md) · [All concepts](../README.md) · [KOS home](../../README.md)

## 1. The project hook

This repo runs **1,878 tests** (10-app battery 1132 + patterns_ai 528 +
devseed 140 + verification 78) — **sequentially, on a fresh database,
every time. Never `--keepdb`, never `--parallel`.** That's slower. It's
also a scar: keepdb once let cross-suite state poison results
(TransactionTestCase truncation), and the cure became LAW. This page
teaches the repo's five testing weapons and why each exists.

## 2. 💡 Samjho Aise

Sunaar sona kaise jaanchta hai? Kasauti par ghis ke — ek PAKKA nishaan
jiske aage koi bahas nahi. Tests wahi kasauti hain: ₹344.25 ka golden
nishaan, "yeh request MANA honi chahiye" ka nishaan, "yeh 2 hi query
hongi" ka nishaan. Coverage percent = kitna ghisa; kasauti = KYA saabit
hua. Repo kasauti ginta hai, ghisai nahi.

## 3. Mental Model

> A great test suite is a set of **pins** — each pin freezes ONE truth the
> system must never lose: an exact money amount, a refusal, a query count,
> a constraint's bite, a flag's both faces. Ask of every test: *"what truth
> does this pin, and would its failure NAME the betrayal?"* Coverage
> measures where you walked; pins prove what you promised.

## 4. Technical Deep Dive — the five weapons

**1. Golden journeys — byte-identical money.** Real business scenarios
replayed END-TO-END through services (never raw fixtures), asserting
EXACT decimals: **₹344.25 · ₹801 · ₹633** (+ historical ₹225). Not
`assertAlmostEqual` — byte-identical. Purpose: any change anywhere in the
money path that shifts a rupee-paisa FAILS with the amount in the diff.
This is what made the RCP-1 service extractions and every S-phase refactor
safe: rewrite, re-run goldens, byte-same = behavior-same.

**2. Refusal pinning — test the BAN itself.** The system's refusals are
features: recovery-at-payment refused (V2-2), settled-line correction
refused, double-reversal refused, monthly-advance refused. Each ban has a
test that ATTEMPTS the forbidden thing and asserts the refusal (and often
its message). Without refusal pins, a "helpful" future edit un-bans
quietly — the pin makes un-banning a visible decision.

**3. Negative DB probes — prove the wall bites.** For constraints:
attempt the bad INSERT, assert `IntegrityError`
([pg/constraints §6](../postgresql/constraints.md) — "a constraint without
a refusal test is a rumor"; 10/10 probes at certification).

**4. Count pins — performance as a property**
([query-performance §4](../postgresql/query-performance.md) — 12
`assertNumQueries`, named constants, "update CONSCIOUSLY").

**5. Both-states flag testing.** Every enforcement lever ships with tests
for OFF (goldens identical — the flag is truly inert) and ON (the refusal
fires). `ENFORCE_ALLOCATION_BOUND` / `ENFORCE_SETTLEMENT_RECONCILIATION`
both landed this way — which is what makes deploy-OFF→soak→enable a safe
runbook instead of a hope.

**+ The field weapon — verification engines.** Tests prove the CODE on a
fresh DB; a verification engine is a READ-ONLY command suite that proves
the WORLD — "yeh database, yeh settings, yeh deployment — sahi hai?":
named checks with per-check PASS/FAIL (no fail-fast — collect everything),
a JSON report with a `body_hash` for determinism (same world → same hash),
environment polarity (dev checks refuse to run on prod; `verify_production`
runs the prod subset: DEBUG off, migrations consistent, zero `dev.*`
contamination, money spot-identities), and read-only proven by row-count
identity around the run. It's the post-deploy gate
([production-and-docker §4](../deployment/production-and-docker.md)) —
because "tests green" and "prod correct" are different sentences.

**The infrastructure laws underneath:**
- **Fixtures through services only** — test data is built by the same
  chokepoints production uses (devseed's 140-test suite exists to prove
  the seeder engine obeys single-writer). Raw `objects.create` on guarded
  tables in a test = the test passes while smuggling a guard-bypass.
- **Sequential fresh-DB** — every run replays every migration from zero
  ([migrations §4](../django/migrations.md)) and shares nothing between
  suites. Cost: minutes. Buys: zero state-leak class of flake.
- **Count as pin:** the battery TOTAL (1878) is itself tracked — a
  disappearing test is a visible event, not silent decay.

## 5. Engineering Thinking

*Why byte-identical instead of tolerances?* Money has no tolerance; a
1-paisa drift is a rounding-path change someone must EXPLAIN. Exactness
converts "probably fine" into a forced conversation. *Why test through
services instead of unit-testing internals?* The service IS the contract
([service-layer](../architecture/service-layer.md)); internals may churn
freely as long as the verbs and goldens hold — that's what makes refactors
cheap. *What this strategy trades away:* speed (sequential) and unit-level
pinpointing (an end-to-end golden failing says WHAT broke, not always
WHERE) — accepted, because the failure modes that matter here are truth
drift and guard erosion, not localization. *The certification layer on
top:* the battery re-proves at every release wave, and results land in an
evidence log — tests as auditable artifacts, not just CI noise.

## 6. How THIS project uses it

A worked example of the culture: when S3 added good/alter/missing, the
change shipped with (a) the golden ₹225 still byte-identical (old money
untouched), (b) a NEW golden with non-zero alter/missing (new math
pinned), (c) the constraint's negative probe, (d) the refusal pin on the
old `reported_quantity_positive` path's replacement. Four pins, one
feature — the template for every money-adjacent change since.

## 7. What breaks without it

Each weapon maps to a real failure class: no goldens → refactors freeze
(fear) or drift (courage); no refusal pins → bans erode invisibly; no
negative probes → armor becomes rumor; keepdb → flakes that train people
to re-run until green; raw fixtures → tests that certify a world
production can't produce.

## 8. Common mistakes (humans)

- Asserting `success == True` instead of the exact outcome — a golden that
  pins nothing.
- Fixing a red refusal test by weakening the refusal (the test was the spec).
- Sharing state via module-level objects — invisible until sequential
  becomes parallel; this repo forbids parallel partly for this.
- Testing the flag ON only — the OFF face (inertness) is half the contract.

## 9. AI Implementation Pitfalls

- ❌ Updating a golden amount to make a red test pass — the golden IS the
  spec; a changed amount is an owner decision with a receipt.
- ❌ Building test data with `objects.create` on guarded tables — services
  only, even in tests (the census treats tests as write-sites).
- ❌ Adding `--keepdb`/`--parallel` to "speed up CI" — LAW, learned twice.
- ❌ Deleting a "redundant" refusal test — refusals without pins un-ban
  themselves.
- ✅ Always verify: money change ⇒ the S3-style four-pin set; battery count
  moves only with an explanation.

## 10. DSA & Complexity

Golden tests are **property checks over a composed pipeline** — instead of
n unit assertions along the path, one end-state equality catches any
interior mutation (like verifying a checksum instead of every byte-copy
step). Refusal pins are testing the COMPLEMENT set — most suites only
sample the accept-region; sampling the reject-region is what proves
boundaries exist at all.

## 11. Interview corner

*Interview Signal: 🟠 Senior — testing money systems = senior.*

**Q. "How do you test financial code?"**
- *Short:* End-to-end golden scenarios with exact-decimal assertions, refusal tests for every ban, DB-level negative probes, all data built through the production write paths.
- *Senior:* Pin truths, not lines: exact outputs (drift detection), refusals (guard erosion detection), query counts (perf regression), both flag states (rollout safety). Keep the suite deterministic even at speed cost — flaky money tests train dangerous habits. Treat test results as release EVIDENCE, logged, not just a green dot.
- *Project example:* ₹344.25 byte-identical across every refactor since; the S3 four-pin template; 10/10 negative probes at certification; sequential-fresh-DB law with the keepdb scar behind it.
- *Follow-ups:* "Goldens too rigid?" (that's the point — changing money math should hurt exactly once, visibly) · "Speed?" (parallelize NON-money suites first if ever; never share DB state) · "Flaky test policy?" (fix or delete same day — a tolerated flake is a disabled alarm).

## 12. 🧠 Remember This

Test = keel (pin). Har keel EK sach jakadti hai: exact paisa, pakka
inkaar, gini hui queries, kaat'ti deewar, flag ke dono chehre. Data
hamesha asli raste se banao (services), zameen har baar nayi (fresh-DB),
aur golden badalna = malik ka faisla, test ki haar nahi.

## 13. 30-Second Revision

- 1878 tests, SEQUENTIAL FRESH-DB (never keepdb/parallel — scar-law)
- Weapon 1: goldens ₹344.25/₹801/₹633/₹225 byte-identical, via services
- Weapon 2: refusal pins (test the ban) · 3: negative DB probes · 4: count pins · 5: both-flag-states
- Fixtures through chokepoints ONLY; devseed suite proves the seeder obeys
- Money change template = S3's four pins; battery count itself is a pin

## 14. What You Should Now Understand

Why pins beat coverage, what each weapon detects, why determinism outranks
speed here, and the four-pin template for money changes. Shaky? Grep one
golden test and read it end-to-end — it's the whole philosophy in one file.

**Recommended next topic:** [security/auth-hardening](../security/auth-hardening.md)
— refusal-pinning applied to the front door.

## Implementation References

- Battery facts: [docs/DEPLOYMENT_CAMPAIGN_STATUS.md](../../../docs/DEPLOYMENT_CAMPAIGN_STATUS.md) · goldens: [docs/FACTORY_OPERATIONS_MASTER.md](../../../docs/FACTORY_OPERATIONS_MASTER.md)
- Evidence culture: [docs/RELEASE_CERTIFICATION_LOG.md](../../../docs/RELEASE_CERTIFICATION_LOG.md)

## Code References
- Suites: `config/expense/tests/` (V2-3 guards, reopen-voids-pay, S5 block) · `config/production/tests/` (S3, perf baseline) · `config/devseed/tests/`

## Further Reading

- One essay: Kent Beck, *"Test Desiderata"* — map each desideratum to
  which of the five weapons serves it (good exercise).

## Related

[pg/constraints](../postgresql/constraints.md) · [query-performance](../postgresql/query-performance.md) ·
[migrations](../django/migrations.md) · [settlement](../../features/settlement.md)
