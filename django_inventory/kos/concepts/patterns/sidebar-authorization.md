---
id: pattern-sidebar-authorization
type: concept
verified: 2026-07-27
knowledge_confidence: verified_against_code
answers: "The Sidebar Authorization (The Pair) pattern — where is it used across apps, and how do I reuse it instead of reinventing it?"
related: [readme-concepts-patterns]
---

# Pattern: Sidebar Authorization (The Pair)

> 📂 [Patterns](README.md) · [All concepts](../README.md) · [LOS home](../../README.md)
> Pattern cards are THIN by law: the deep teaching lives on the linked
> canonical pages; this card is the cross-app map + reuse contract.

**Purpose.** Menu visibility and URL access from ONE rule row — drift is unrepresentable.

> 💡 **Samjho aise:** Menu dikhana aur URL kholna — dono **ek hi row** se chalte hain. Isliye "menu se hata diya par page khulta hai" wali galti ho hi nahi sakti.

**Problem it solves.** Hide-only menus are security theater; separate gate configs drift from menus.

**Where it's used (the cross-app map).**
- `SidebarItemRule` + middleware + context processor ([inventory services — the trio](../../apps/inventory/services.md))
- same collapse-the-pair idea: Stage model carrying its own access rules ([production urls-core §stages](../../apps/production/urls-core.md))

**How it works (one breath).** One row read by the renderer AND the enforcer; unmanaged URLs keep view mixins (additive defense).

**Trade-offs.** Every request pays a rule lookup; exempt lanes need loop care.

**Common mistakes.** A second predicate for one surface · menu edits treated as cosmetic · forgetting the rule row for a new URL.

**The counter-intuitive one (learned 2026-07-27).** Because the pair collapses
menu + gate into one row, a rule whose menu item has been removed from the code
registry is **still enforcing**. So when a drift guard reports an "orphan rule",
*deleting the row is the dangerous repair* — the URL becomes unmanaged and loses
its gate. The safe repair is a **registry-only entry** (`hidden=True`: renders
for nobody, keeps the rule bound). Real case: `production:my-work` kept its rule
after a menu dedupe, so workers could still reach the page by URL — correctly
gated — while the invariant test failed. Fix = re-register hidden, not delete.

> 🧠 **Remember This:** ek row do kaam karti hai — menu dikhana AUR darwaza
> band rakhna. Menu se hataya, phir bhi darwaza usi row se bandh hai. Row
> delete ki to **darwaza hi gayab** — item chhupao, row mat mitao.

**Related.** [rbac-access](../../features/rbac-access.md) — canonical teaching.
