# Why WorkerStageTask exists

**Problem:** Pehle ek Adda-stage ke saath bas ek "workers" list judi thi (M2M) —
naam to pata chalte the, par "kis worker ne kya kiya, kab, kis haalat me" kuch
nahi. Pay disputes me yeh kaafi nahi.

**Solution:** WorkerStageTask = ek worker ka ek stage par ASSIGNMENT + LIFECYCLE
(assigned → in_progress → completed → verified, ya cancelled). Har worker ka
apna row, apni timeline.

**Key rule:** ek (stage_record, worker) ke liye ek hi ACTIVE task (partial-unique
constraint). Worker hata diya? row CANCEL hota hai, DELETE nahi — taaki roster
hamesha "jisne sach me participate kiya" dikhaye (owner rule).

**Agar na ho:** participation ka koi sach nahi — settlement kiske kaam ka paisa
bana raha hai pata hi nahi chale; "is worker ne yeh stage kiya tha?" ka jawab
gayab. WorkerStageContribution (kaam ka maap) ko bhi t"angna" chahiye — woh WST
se hangta hai.

ADR-0005 · [chokepoint](../CHOKEPOINTS/worker_task_service.md).
