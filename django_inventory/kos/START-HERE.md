---
id: kos-start-here
type: system
verified: 2026-07-19
---

# START HERE — productive by tomorrow

> New to this repository? This is your first day, time-boxed. Goal:
> **productive**, not expert (expert = [engineering-journey](project/engineering-journey.md),
> four weeks). *(Aaj kaam layak, mahine mein maalik.)*

## ⏱ 15 minutes — the business

Read [business-story](project/business-story.md).
You now know: it's a garment factory; **Adda** = one production batch;
workers report from phones; the owner settles money batch-wise.
One sentence to keep: *workers report → owner settles → owner pays →
everything provable forever.*

## ⏱ 45 minutes — the architecture

Read [system-map](project/system-map.md), then [money-story](project/money-story.md).
You now know: 9 apps + core; every click = middleware → view → service →
PostgreSQL; **two truths** (work = pencil, money = pen) joined at ONE gate
(settlement). The three iron rules: services own writes · one writer per
money table · nothing edits history.

## ⏱ 90 minutes — the production flow

Read [cloth-to-garment](flows/cloth-to-garment.md), then
[worker-gets-paid](flows/worker-gets-paid.md).
You now know: roll → layering → pattern → cutting (quantities born) →
barcodes → report → verify → settle → cash — and what BLOCKS each step,
on purpose.

## ⏱ 2 hours — money, properly

Read [settlement](features/settlement.md) — the deepest page, the
system's heart. Skim [ledger](features/ledger.md).
You now know: the finalize walkthrough, the lock order, why corrections
reverse instead of edit, and why balances are never stored.

## ⏱ Half a day — hands + safety rails

1. Boot dev: `env/bin/python config/manage.py runserver`
   (settings: `config.settings.local`; creds in team notes).
2. Walk one URL with [request-through-stack](flows/request-through-stack.md)
   open — the universal debug recipe.
3. Read the [debugging playbooks' README](debugging/README.md) — know
   WHERE they are before you need them.
4. Read [AI Implementation Pitfalls on settlement](features/settlement.md#ai-implementation-pitfalls)
   — the mistakes everyone (human or AI) makes here first.

## ⏱ One day in — you can contribute

Before your first change, three laws *(teen kanoon, bas)*:
1. **Writes go through services** — never `objects.create` on money/history
   tables ([single-writer](concepts/architecture/single-writer.md)).
2. **Before modifying a feature** — read its page's **Change Impact** section.
3. **kos-sync** — your change isn't DONE until its kos page is updated,
   same session.

Lost at any point? [kos/README](README.md) → *Find it by app*. Something
broken? [debugging/](debugging/README.md). Inside docs/? Each major folder
now has a 🧭 HUMAN_GUIDE.md, and the map is
[reading-the-docs](project/reading-the-docs.md).

**Welcome. Ship something small today; understand something deep every day
after** — the [journey](project/engineering-journey.md) is waiting when
you're ready.
