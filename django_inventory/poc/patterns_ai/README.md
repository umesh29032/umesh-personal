# patterns_ai P0 harness (feasibility — NON-production code)

Reproducible bake-off + metrology POC + yield walk for the AI Pattern
Intelligence project (ADR-A / ADR-E / master plan P0). Kept permanently as
executable documentation. **No Django app code lives here.**

## Manifest (vendored / pinned)
- `vendor/SVGnest` @ `1248dc21efd3f90d1aa52ba5785e27e5217ed2c9` (MIT) — core
  used headless: `util/clipper.js`, `util/geometryutil.js`,
  `util/placementworker.js`.
- `venv/` from `requirements.lock.txt`: numpy 2.2.6 · shapely 2.1.2 ·
  opencv-contrib-python-headless 5.0.0.93.
- Node v18.20.8 (system for POC; enters the ADR-F vendor manifest for P3).
- pynest2d: **no PyPI distribution** — eliminated (ADR-A addendum §3).

## Reproduce
```bash
cd poc/patterns_ai
python3 -m venv venv && ./venv/bin/pip install -r requirements.lock.txt
./venv/bin/python make_pieces.py            # harness geometry (mm, y-up, CCW)
./venv/bin/python blf_nest.py               # BLF floor → results/blf.json
node svgnest_runner.js pieces/tee.json 150  # SVGnest core → results/svgnest_*.json
node svgnest_runner.js pieces/patti.json 60
node svgnest_runner.js pieces/stress.json 90
./venv/bin/python metrology_poc.py          # → results/metrology.json
cd ../../config && ../env/bin/python manage.py shell < ../poc/patterns_ai/yield_walk.py
```
Everything is seeded/deterministic except noted timeboxes (trial COUNT is
fixed at ≤201, so results reproduce exactly on same hardware ordering).

## Honesty notes
- Harness pieces are hand-constructed realistic geometries (capture = P2);
  identical inputs across engines ⇒ relative numbers valid.
- SVGnest runner nests the on-fold piece UNFOLDED (no fold-pin support in the
  core); the BLF floor implements fold-pinning. P3 adapter work item.
- Metrology loop bounds ALGORITHM error only; physical tiers = P2 with the
  commissioned mat (D7).
- Yield walk reads the real DB (read-only) — its utilization estimate uses
  harness garment area and DEV-fixture lay numbers; its purpose is proving
  the MATH the P1 yield board ships.
