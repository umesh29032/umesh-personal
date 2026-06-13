# Why reversals exist

**Problem:** Append-only me row edit/delete nahi kar sakte. To galti kaise
sudhare?

**Solution:** REVERSAL = ulti-direction nayi row jo galat row ko net kar deti
hai. Ledger me: credit ki galti → reversal DEBIT (same amount, original
entry_date copy → mahine ka hisaab sahi). Settlement level par:
reverse_adda_settlement → compensating ledger rows + SWA void + (optional)
supersede chain (naya draft, purana SUPERSEDED).

**Kyun:** "kal ki galti aaj ke naye event se theek hoti hai, history edit karke
nahi." Yeh accountant ka real workflow hai — reverse, phir dobara sahi settle.

**Agar na ho:** galti theek karne ka ek hi tareeka bachta = history todna, jo
append-only + trust dono khatam kar de.

[journey: settlement_finalize](../REQUEST_JOURNEYS/settlement_finalize.md) ·
ADR-0007.
