---
id: readme-project
type: system
verified: 2026-07-19
---

# Project — the WHY layer (read this folder first, always)

*(Part of the [KOS](../README.md).)*

## Why this folder exists — a teacher's note

Every technical decision in this repo is downstream of facts about ONE
factory: workers report from phones, the owner settles batch-wise, money
disputes must die in minutes. If you skip the WHY and jump to code, every
design will look over-engineered *(bina context ke har taala paranoia
lagta hai; context ke saath har taala ek purani chori ki yaad hai)*.
Thirty minutes here makes every other page half as hard.

## Reading order (deliberate)

1. [business-story.md](business-story.md) — what this factory does; the
   cast; Adda = the central noun; the one-sentence engine.
2. [system-map.md](system-map.md) — 9 apps + core; the universal path
   every click takes; the three iron rules.
3. [money-story.md](money-story.md) — pencil vs pen: two truths, one gate.
   The single most important page for understanding this system.
4. [people-and-roles.md](people-and-roles.md) — role vs skill vs sidebar;
   the four walls.
5. [tech-stack.md](tech-stack.md) — why every boring choice beat its
   fashionable alternative (the rejected-on-purpose table is interview gold).
6. [reading-the-docs.md](reading-the-docs.md) — the human's guide to the
   1,100-file docs/ archive: the seven piles, the kos→docs→code routing
   rule, and the ~20 files actually worth a learner's time.

## The test of this folder

After these five pages you should be able to answer, out loud, without
notes: *What does this factory do? Why are there two truths? Why is
settlement the only money boundary? Who can see what? Why no
microservices?* If any answer stumbles, re-read that page — the rest of
the KOS assumes all five *(yeh paanch jawab zubaani yaad = baaki sab
aadha ho gaya)*.
