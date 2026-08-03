---
id: learning-08-adda-lifecycle
type: lesson
status: active
owner: handwritten
scope: learning — generic concept
anchors: —
verified: 2026-07-13
---

# Adda lifecycle — the factory's unit of work

## What an Adda is
EK product ka EK production batch. `3-PATTI-001` = "3 Patti ka pehla batch".
Code global-unique forever (ADR-0010). Har Adda apne product ke FLOW ko
follow karta hai (WorkflowStage rows — owner flow editor mein order, rate,
grouping, pay-eligibility set karta hai; TM-1 yahin tracking mode laayega).

## The walk
START (1 field — product) → stage records bante hain →
LAYERING: rolls attach (weight verify), complete par leftover weigh-in
MANDATORY → CUTTING-PATTERN: evidence (photos/video) →
CUTTING: size breakup, bundles, workers report color/size/qty (pehli real
quantities; durations auto from timestamps — manual duration is banned) →
BARCODE-GEN: (adda,color,size) seq ranges — printed payload PERMANENT →
COMPLETE → settlement queue → ADST → cash.

## Reopen rules
Stage reopen allowed for corrections — JAB TAK paisa na bana ho.
Settlement-credited stage: reopen refuses, names the ADST → reverse first.
Reopen voids era-A allocations (PAY-3) but NEVER settlement lines.

## Where to watch it
Adda dashboard + workspaces today; G4 Adda-360 (soak instrument) will compose
production + operations + money on one page — all the data already exists.
