# Why WorkerStageContribution exists

**Problem:** Sirf "worker ne stage kiya" kaafi nahi — kitna banaya? kaunse
colour/size me? Paisa isi par banta hai.

**Solution:** WorkerStageContribution (WSC) = ek dimensional LINE under a task —
colour + size + `reported_quantity`. Ek task ke kai lines ho sakti hain
(Red S=100, Red M=150…).

**3 alag quantity (kabhi confuse mat karna):**
- `reported_quantity` — worker ka claim. IMMUTABLE, hamesha (owner §6).
- `verified_quantity` — management ki correction (galti theek karne ko).
- frozen `expected_rate`/`expected_earning` — complete par freeze; sirf
 DIKHANE ko (Expected strip), paisa NAHI (Option B, ADR-0005).

**Agar na ho:** production truth ka koi granular record nahi → settlement
"verified-else-reported × rate" compute hi nahi kar paaye; missing/variance
ka base gayab; G3 (variance valuation) ki neev hi nahi.

[chokepoint](../CHOKEPOINTS/worker_task_service.md) · [05](05_why_settlement_not_payment.md).
