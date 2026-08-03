---
id: readme-features
type: system
verified: 2026-07-19
---

# Features — one canonical page per thing the factory does

*(Part of the [KOS](../README.md). Har feature-page yahin backlink karti hai.)*

## Why this folder exists — a teacher's note

A feature page answers the question you actually ask while working:
*"I have to touch settlement/payroll/cutting — what MUST I understand
before I change anything?"* Each page is that feature's ONE canonical
home *(ek feature = ek hi ghar — dobara kahin nahi likha jaata)*: its
business purpose, its architecture and the alternatives that were
REJECTED, its models/URLs/permissions, how to debug it, what to review
before modifying it (**Change Impact**), and what AI agents get wrong in
it (**AI Implementation Pitfalls**).

Read a feature page BEFORE reading that feature's code — the code then
reads like an implementation of a story you already know, instead of a
puzzle.

## The pages — grouped by which app owns them

**Money (expense app — URLs under `/expense/…`):**

| Page | Real question it answers |
|---|---|
| [settlement.md](settlement.md) — **the depth benchmark** | How does work become owed money? (`/expense/settlements/…`) |
| [ledger.md](ledger.md) | Where does every rupee live? (the book behind every money screen) |
| [payroll.md](payroll.md) | How does cash leave, what's still owed? (`/expense/payroll/`, `/my/`, `/workers/<id>/settle/`) |
| [advances.md](advances.md) | How do loans work without corrupting earnings? (`/expense/advances/add/`) |

**Production (production app — stage/Adda screens):**

| Page | Real question it answers |
|---|---|
| [stage-tracking.md](stage-tracking.md) | How is who-did-what recorded and corrected? (worker report + Report Review screens) |
| [allocation.md](allocation.md) | How is over-claiming impossible? (stage panel "Split the work") |
| [cutting.md](cutting.md) | Where do countable pieces come from? (cutting/stream screens) |
| [machines.md](machines.md) | Who holds which machine, now and last Tuesday? (machines app) |

**Access (accounts + inventory apps):**

| Page | Real question it answers |
|---|---|
| [rbac-access.md](rbac-access.md) | What machinery decides what each user sees/reaches? (every URL, every menu) |
| [learning-courses.md](learning-courses.md) | Where do I actually READ the courses, and how does `/learn/` work without storing any content? |

**How work enters the repo:**

| Page | Real question it answers |
|---|---|
| [engineering-workflow.md](engineering-workflow.md) | How does code get INTO this repo — and how is `main` protected when GitHub's branch protection is a paid feature? |

*(URL dhoondh rahe ho? Feature page ke "Related URLs" section mein exact
routes + unke WHY milte hain; structural chain generated cards mein hai.)*

## How to use these pages

- **Before modifying** a feature: read its Change Impact section FIRST —
  it lists what to review so you don't learn dependencies from a bug.
- **While debugging**: jump straight to the Debugging Guide table —
  symptom → where to start.
- **Reviewing AI-written code** in a feature: open AI Implementation
  Pitfalls — it's the checklist of known agent mistakes there.
- **Interview prep**: each page's Interview Notes = design questions
  answered through THIS feature's real story.
