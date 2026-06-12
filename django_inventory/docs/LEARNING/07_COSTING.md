# Costing — two measurements, one labor (NEVER add them)

## The duality (ADR-0009 — the #1 trap)
`processing_cost` = STANDARD cost: ws.cost_rate × handler quantity,
role-independent, frozen at stage advance. Settled earnings = ACTUAL pay:
role-aware frozen rate × reported/verified qty, ledger. Payable stage ke liye
yeh EK hi labor ke do measurements hain → **kabhi add mat karo.**

Full Adda cost = material (G1) + ACTUAL settled labor + processing_cost of
NON-payable stages only (+ future overhead, era-stamped).
Standard-vs-actual ka difference = future VARIANCE report — component nahi.

## Labor-source rule
Per-Adda actual labor = Σ non-voided SWA snapshots (both eras). WSC.expected_*
se nahi (era-A drop ho jata), settlement totals se nahi (partial/reversed
chains mis-sum).

## Honest-NULL
Unpriced stage / unpriced roll = NULL, kabhi 0 nahi. Dashboard banner +
per-Adda counts chillate hain "material costing incomplete". Unknown ≠ free.

## Grouped stages
`cost_billed_at` = member ka cost payer stage pe bill hota hai. C-1 guard:
grouped member kabhi earning rate nahi deta (role-rate ho tab bhi ₹0 freeze)
— warna double-pay. Era-A allocation bhi grouped stages refuse karta tha;
ab settlement side bhi.

## Material (G1 future, facts already captured)
cost_per_kg = PURCHASE fact (corrections only). Consumption = attach weight −
leftovers (mandatory weigh-ins). Leftover reuse = consume_leftover ONLY —
off-book reuse permanently understates the next Adda's cloth cost.
