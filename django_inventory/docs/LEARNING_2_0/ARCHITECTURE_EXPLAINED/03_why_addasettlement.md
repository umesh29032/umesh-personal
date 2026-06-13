# Why AddaSettlement exists

**Problem:** Paisa kab "ban" jaata hai? Pehle allocation ke waqt guess hota tha
(kaam measure hone se PEHLE) — galat numbers, no review, no clean correction.

**Solution:** AddaSettlement = ek EXPLICIT event jab owner ek Adda ka kaam
check karke earnings BOOK karta hai (+ advances recover karta hai). Draft
(scratchpad, no money) → finalize (money writes + frozen snapshots) →
reverse/supersede (correction).

**Yeh Adda-centric hai** (worker-centric nahi) — kyunki kaam Adda me hota hai;
ek settlement event me uss Adda ke saare workers ek saath settle hote hain.

**Agar na ho:** paisa galat waqt par (kaam se pehle) banega; "kya approve hua,
kisne, kab" ka koi frozen record nahi; correction = row edit karke history
todna. AddaSettlement hi woh jagah hai jahan production truth → financial truth
banta hai, audit ke saath.

ADR-0005/0007 · [chokepoint](../CHOKEPOINTS/adda_settlement_service.md) ·
[journey](../REQUEST_JOURNEYS/settlement_finalize.md).
