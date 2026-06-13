# Why append-only was chosen

**Problem:** Paisa ki row ko EDIT/DELETE karna = history mit jaati hai. Kal
koi pooche "yeh ₹180 kyun mile the?" to jawab badal chuka hota hai.

**Solution:** Money + history tables APPEND-ONLY. Row banti hai, kabhi badalti/
mit-ti nahi. Galti = nayi compensating row.

**Kyun:** factory me paisa = trust. "Work-that-happened is immutable history"
(owner rule). Append-only = har rupee ka permanent, auditable trail; balance =
live SUM, isliye purani rows badalne ki zaroorat hi nahi.

**Agar na ho:** ek UPDATE silently kisi worker ka paisa badal de, bina reference,
bina trail — aur append-only ki guarantee hamesha ke liye toot jaaye. Constraints
+ single-writer + append-only teeno milke money ko bug-proof banate hain.

ADR-0002/0004 · [08](08_why_reversals.md).
