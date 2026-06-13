# Why verified_quantity exists

**Problem:** Worker `reported_quantity` IMMUTABLE hai (uska claim, kabhi badalna
nahi). Par worker se TYPO ho gaya (60 ki jagah 600) — settlement galat paisa
bana dega. Reported ko edit nahi kar sakte (rule). To?

**Solution:** ALAG column — `verified_quantity`. Management correction yahan
likhta hai (P1 review screen). Settlement "verified-else-reported" padhta hai.
DONO preserve hote hain — worker ne kya kaha + factory ne kya maana.

**Kyun:** dispute me teen sawaal — worker ne kya bola, factory ne kya verify
kiya, paisa kis par bana. Teeno alag columns = teeno ka permanent jawab. Ek
mutable "quantity" hota to har dispute he-said-she-said ban jaata.

**Guard:** settle ho chuki line ka verified edit REFUSE hota hai — pehle
settlement reverse karo (V2-3 armor).

P1 · [chokepoint](../CHOKEPOINTS/worker_task_service.md).
