/* SVGnest headless runner (P0 bake-off) — drives the REAL SVGnest core
 * (GeometryUtil.noFitPolygon + PlacementWorker.placePaths) from Node, no DOM.
 * Vendored source: vendor/SVGnest @ 1248dc21 (MIT).
 * Deterministic: mulberry32 seeded search over order+rotation (GA-lite),
 * time-boxed per set. Mirror pairs pre-split (SVGnest has no flip gene).
 * On-fold pieces are nested UNFOLDED (full outline) — noted in results.
 * Usage: node svgnest_runner.js pieces/tee.json [timeboxSeconds]
 */
'use strict';
const fs = require('fs');
const vm = require('vm');

// ---- load vendored core into one sandbox -------------------------------
const sandbox = { console, Math, JSON, Array, Object, Number, Boolean, Date: undefined };
sandbox.window = sandbox; sandbox.self = sandbox; sandbox.root = sandbox;
// clipper.js sniffs browsers; give it a minimal Netscape-ish environment
sandbox.navigator = { userAgent: 'node', appName: 'Netscape', appVersion: '5.0' };
vm.createContext(sandbox);
for (const f of ['util/clipper.js', 'util/geometryutil.js', 'util/placementworker.js']) {
  vm.runInContext(fs.readFileSync('vendor/SVGnest/' + f, 'utf8'), sandbox, { filename: f });
}
const GU = sandbox.GeometryUtil, ClipperLib = sandbox.ClipperLib;
if (!GU || !ClipperLib || !sandbox.PlacementWorker) { throw new Error('core load failed'); }

const CLIPPER_SCALE = 10000000, SPACING = 2.0, TOL = 0.3;

function offsetPoly(poly, delta) {
  const co = new ClipperLib.ClipperOffset(2, TOL * CLIPPER_SCALE);
  const path = poly.map(p => ({ X: Math.round(p.x * CLIPPER_SCALE), Y: Math.round(p.y * CLIPPER_SCALE) }));
  co.AddPath(path, ClipperLib.JoinType.jtRound, ClipperLib.EndType.etClosedPolygon);
  const out = new ClipperLib.Paths();
  co.Execute(out, delta * CLIPPER_SCALE);
  if (!out.length) return null;
  out.sort((a, b) => Math.abs(ClipperLib.Clipper.Area(b)) - Math.abs(ClipperLib.Clipper.Area(a)));
  return out[0].map(p => ({ x: p.X / CLIPPER_SCALE, y: p.Y / CLIPPER_SCALE }));
}
function mulberry32(a) { return function () { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const rotP = (poly, deg) => { const a = deg * Math.PI / 180, out = poly.map(p => ({ x: p.x * Math.cos(a) - p.y * Math.sin(a), y: p.x * Math.sin(a) + p.y * Math.cos(a) })); return out; };

// ---- build instances -----------------------------------------------------
const specPath = process.argv[2] || 'pieces/tee.json';
const TIMEBOX = (parseFloat(process.argv[3]) || 90) * 1000;
const spec = JSON.parse(fs.readFileSync(specPath, 'utf8'));
const BIN_LEN = 20000;
let unfoldNote = false;
const parts = [];
let idc = 0;
for (const pc of spec.pieces) {
  // pieces are authored grain-along-y; this runner's lay runs along x —
  // pre-rotate 90° so grain lies along the lay (0/180 constraint unchanged)
  let base = pc.polygon.map(([x, y]) => ({ x: y, y: -x }));
  if (pc.on_fold) {           // unfold: mirror about x=0 fold edge, join
    unfoldNote = true;
    const mir = base.map(p => ({ x: -p.x, y: p.y })).reverse();
    base = base.concat(mir);
  }
  for (let q = 0; q < pc.qty; q++) {
    let poly = base;
    if (pc.allow_mirror && q % 2 === 1) poly = base.map(p => ({ x: -p.x, y: p.y })).reverse();
    const off = offsetPoly(poly, SPACING / 2) || poly;
    const inst = off.map(p => ({ x: p.x, y: p.y }));
    inst.id = idc++; inst.source = pc.id;
    inst.rotationsAllowed = pc.allow_180 && !pc.on_fold ? [0, 180] : [0];
    inst.area = Math.abs(GU.polygonArea(inst));
    inst.trueArea = pc.area_mm2;
    parts.push(inst);
  }
}
// bin: length along x, width along y (rectangle, id -1), shrunk by spacing/2
const W = spec.width_mm - SPACING;
const bin = [{ x: 0, y: 0 }, { x: BIN_LEN, y: 0 }, { x: BIN_LEN, y: W }, { x: 0, y: W }];
bin.id = -1; bin.width = BIN_LEN; bin.height = W;

// ---- NFP cache -----------------------------------------------------------
const nfpCache = {};
function binNfp(part, rot) {
  const key = JSON.stringify({ A: -1, B: part.id, inside: true, Arotation: 0, Brotation: rot });
  if (nfpCache[key]) return;
  const nfp = GU.noFitPolygonRectangle(bin, rotP(part, rot));
  nfpCache[key] = nfp;
}
function minkowskiNfp(A, B) {           // svgnest's clipper path, verbatim math
  const S = 10000000;
  const Ac = A.map(p => ({ X: Math.round(p.x * S), Y: Math.round(p.y * S) }));
  const Bc = B.map(p => ({ X: -Math.round(p.x * S), Y: -Math.round(p.y * S) }));
  const sol = ClipperLib.Clipper.MinkowskiSum(Ac, Bc, true);
  let nfp = null, largest = null;
  for (const s of sol) {
    const n = s.map(p => ({ x: p.X / S, y: p.Y / S }));
    const a = GU.polygonArea(n);
    if (largest === null || largest > a) { largest = a; nfp = n; }
  }
  if (!nfp) return null;
  for (const p of nfp) { p.x += B[0].x; p.y += B[0].y; }
  return [nfp];
}
function pairNfp(a, ra, b, rb) {
  const key = JSON.stringify({ A: a.id, B: b.id, inside: false, Arotation: ra, Brotation: rb });
  if (nfpCache[key]) return;
  const nfp = minkowskiNfp(rotP(a, ra), rotP(b, rb));
  if (nfp) nfpCache[key] = nfp;
}

// ---- search --------------------------------------------------------------
function extent(placementSheets) {
  let maxx = 0, area = 0, placed = 0;
  for (const sheet of placementSheets) {
    for (const pl of sheet) {
      const part = parts.find(p => p.id === pl.id);
      const rp = rotP(part, pl.rotation);
      for (const p of rp) maxx = Math.max(maxx, p.x + pl.x);
      area += part.trueArea; placed++;
    }
  }
  return { maxx, area, placed };
}

function tryOrder(order, rots) {
  for (let i = 0; i < order.length; i++) binNfp(order[i], rots[order[i].id]);
  for (let i = 0; i < order.length; i++) for (let j = 0; j < i; j++)
    pairNfp(order[j], rots[order[j].id], order[i], rots[order[i].id]);
  const paths = order.map(p => { const c = p.map(q => ({ x: q.x, y: q.y })); c.id = p.id; c.source = p.source; c.rotation = rots[p.id]; return c; });
  const selfCtx = { binPolygon: bin, nfpCache, config: { clipperScale: CLIPPER_SCALE, curveTolerance: TOL, spacing: SPACING } };
  sandbox.global = { env: { self: selfCtx } };
  const pw = new sandbox.PlacementWorker(bin, paths.map(p => p.slice()), paths.map(p => p.id), paths.map(p => p.rotation), selfCtx.config, nfpCache);
  const res = pw.placePaths(paths);
  if (!res) return null;
  const e = extent(res.placements);
  return { fitness: res.fitness, ...e, placements: res.placements };
}

const t0 = Date.now();
const rand = mulberry32(42);
let best = null, trials = 0;
const byArea = parts.slice().sort((a, b) => b.area - a.area || a.id - b.id);
const orders = [byArea];
while (Date.now() - t0 < TIMEBOX) {
  let order;
  if (trials < orders.length) order = orders[trials];
  else { order = byArea.slice(); for (let i = order.length - 1; i > 0; i--) { const j = Math.floor(rand() * (i + 1));[order[i], order[j]] = [order[j], order[i]]; } }
  const rots = {};
  for (const p of parts) rots[p.id] = trials === 0 ? 0 : p.rotationsAllowed[Math.floor(rand() * p.rotationsAllowed.length)];
  const r = tryOrder(order, rots);
  trials++;
  if (r && r.placed === parts.length && (!best || r.maxx < best.maxx)) best = { ...r, trial: trials };
  if (trials > 200) break;
}

const out = {
  set: spec.name, engine: 'SVGnest-core-headless@1248dc2', spacing_mm: SPACING,
  trials, timebox_s: TIMEBOX / 1000, unfolded_onfold_note: unfoldNote,
  pieces_placed: best ? best.placed : 0, pieces_total: parts.length,
  marker_length_mm: best ? Math.round(best.maxx * 10) / 10 : null,
  utilization_pct: best ? Math.round(best.area / (spec.width_mm * best.maxx) * 10000) / 100 : null,
  wall_clock_s: Math.round((Date.now() - t0) / 100) / 10,
};
console.log(JSON.stringify(out));
fs.mkdirSync('results', { recursive: true });
const tag = specPath.split('/').pop().replace('.json', '');
fs.writeFileSync(`results/svgnest_${tag}.json`, JSON.stringify({ ...out, placements: best ? best.placements : null }, null, 1));
