# FUTURE AGENT WORKFLOW — the 7-step loop

## TL;DR
Every session, every change, runs this loop. Steps 1–3 are READ (cheap, from
docs); step 4 is the only place you touch raw code; steps 6–7 keep the system alive.

```
1. READ AI_AGENT_GUIDE/README.md (zero-context entry, never-modify list)
2. READ PROJECT_KNOWLEDGE_MAP.md (whole-system shape)
3. READ the canonical doc for the topic (AI_AGENT_GUIDE lookup table)
4. INVESTIGATE code — ONLY if the docs didn't resolve it (then you've found a drift to fix)
5. IMPLEMENT — via a SERVICE (never write a truth table from a view); add tests
6. UPDATE DOCS — run CHANGE_IMPACT_MATRIX for your changed file(s); update each
 listed doc (or state why N/A). This is part of "done."
7. VERIFY NO DRIFT — bash scripts/check.sh green; doc-accuracy guard green;
 confirm the canonical doc now matches the code.
```

If step 4 surfaced something the docs SHOULD have told you → the doc was stale =
an architecture bug → fix the doc in step 6 so the next agent pays zero tokens.
