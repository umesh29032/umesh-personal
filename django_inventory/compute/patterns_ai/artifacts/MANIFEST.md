# compute/patterns_ai/artifacts — vendored artifact manifest (ADR-F)

Every artifact used by the compute runtime is listed here with sha256 +
license. NOTHING is fetched at runtime; a missing artifact = the feature
reports itself unavailable (see `runtime/segment.py`).

| Artifact | Status | sha256 | License | Used by |
|---|---|---|---|---|
| `mobile_sam.encoder.onnx` | **NOT VENDORED (slot reserved)** | — | Apache-2.0 (MobileSAM) | `sam` segmentation backend |
| `mobile_sam.decoder.onnx` | **NOT VENDORED (slot reserved)** | — | Apache-2.0 (MobileSAM) | `sam` segmentation backend |

Python packages are pinned in `../requirements.lock.txt` (numpy,
opencv-contrib-python-headless, shapely, ezdxf) — P0-proven versions.

## Vendored engine sources (P3)

| Artifact | Version | License | Used by |
|---|---|---|---|
| `../vendor/SVGnest/util/{clipper,geometryutil,placementworker}.js` | SVGnest @ `1248dc21` (P0 pin) | MIT | `nest_runner.js` (primary nesting engine, ADR-A) |
| Node.js runtime | v18.x (system; enters the deploy runbook) | MIT | invoked by `nest.py` as a subprocess; absence = honest `svgnest unavailable`, BLF floor still runs |

## SAM activation procedure (when the owner vendors the weights)
1. Export MobileSAM to ONNX (encoder + decoder), place both files here.
2. `./venv/bin/pip install onnxruntime==<pin>` and add the pin to
   requirements(.lock).txt.
3. Record sha256 + license rows above.
4. Implement `runtime/segment._sam()` sessions (adapter contract:
   `segment(rect_gray) -> (mask, stability)`), run the backend-parity
   golden tests.
Until then `available_backends()` returns `['classical']` — honest.
