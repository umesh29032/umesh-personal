# Why production truth ≠ financial truth (Option B)

> **CANONICAL** for the "two truths" concept (binding: ADR-0005). Other docs give
> a one-line summary + link here; they do not re-explain the why.

**Problem:** Agar kaam report karte hi paisa ledger me likh dein, to har choti
production galti = financial galti; aur kaam abhi "final" bhi nahi hua.

**Solution (Option B, ADR-0005):**
- **Production truth** = WST + WSC (kitna kaam hua). Yahan paisa NAHI.
 `expected_*` freeze hota hai par woh sirf VISIBILITY hai.
- **Financial truth** = WorkerLedgerEntry. Sirf settlement par likhta hai.

Do alag spine, ek dusre se bridge sirf settlement par (`verified-else-reported
× frozen rate`).

**Kyun:** kaam ka record turant chahiye (worker ne report kiya), par paisa tab
banna chahiye jab owner ne CHECK kiya. Do truths alag = production galti paisa
corrupt nahi karti, aur paisa hamesha review ke baad banta hai.

**Agar na ho:** har report ek irreversible money event ban jaaye; correction
aur audit dono toot jaayein.

ADR-0005 · [04](04_why_workerledgerentry.md) · [03](03_why_addasettlement.md).
