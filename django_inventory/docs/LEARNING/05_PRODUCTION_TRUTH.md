# Production truth — "kitna kaam hua" ka permanent sach

## The two tables
WorkerStageTask = WHO was on a stage (participation; cancel-not-delete —
roster jhooth nahi bolta). WorkerStageContribution = WHAT they made
(color/size/qty lines).

## The three quantities (never confuse)
- `reported_quantity` — worker ka claim. IMMUTABLE forever (owner §6).
- `verified_quantity` — management ki correction (P1 review page). Reported
  ko kabhi touch nahi karta — dono history mein rehte hain.
- frozen `expected_rate/earning` — complete par freeze hota hai. SIRF
  visibility (Expected strip); paisa NAHI (ADR-0005 Option B).

## Lifecycle
assign → (draft saves allowed) → SUBMIT (lines lock, expected freezes) →
stage complete (unreported tasks AUTO-CANCEL — F3; P2 dialog pehle warn karta
hai, naam le ke). Settlement-credited line? verified edit REFUSES — pehle
settlement reverse karo (V2-3 armor ka extension).

## Why this shape
Pay disputes mein teen sawaal hote hain: worker ne kya bola, factory ne kya
maana, paisa kis number pe bana. Teeno alag columns = teeno ka permanent
jawab. Single mutable "quantity" hota to har dispute he-said-she-said hota.
