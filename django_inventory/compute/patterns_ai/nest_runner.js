/* nest_runner.js — PRODUCTION SVGnest-core headless runner (ADR-A primary).
 * Adapted from the P0 bake-off runner; vendored core: vendor/SVGnest @1248dc2
 * (MIT). Deterministic (seeded mulberry32, fixed trial cap + timebox).
 * Protocol: node nest_runner.js job.json out.json
 * job: {width_mm, spacing_mm, timebox_s, seed, pieces:[{key, polygon_mm
 *       (y-up, grain along +y), qty, allow_180, allow_mirror}]}
 * out: {ok, engine, trials, placements:[{key, instance,
 *       polygon_mm: ABSOLUTE ring in lay frame (x = length, y = width)}]}
 */
'use strict';
const fs = require('fs');
const vm = require('vm');
const path = require('path');

const jobPath = process.argv[2], outPath = process.argv[3];
const job = JSON.parse(fs.readFileSync(jobPath, 'utf8'));

const sandbox = { console, Math, JSON, Array, Object, Number, Boolean, Date: undefined };
sandbox.window = sandbox; sandbox.self = sandbox; sandbox.root = sandbox;
sandbox.navigator = { userAgent: 'node', appName: 'Netscape', appVersion: '5.0' };
vm.createContext(sandbox);
const VENDOR = path.join(__dirname, 'vendor', 'SVGnest');
for (const f of ['util/clipper.js', 'util/geometryutil.js', 'util/placementworker.js']) {
  vm.runInContext(fs.readFileSync(path.join(VENDOR, f), 'utf8'), sandbox, { filename: f });
}
const GU = sandbox.GeometryUtil, ClipperLib = sandbox.ClipperLib;
if (!GU || !ClipperLib || !sandbox.PlacementWorker) throw new Error('SVGnest core load failed');

const CLIPPER_SCALE = 10000000, TOL = 0.3;
const SPACING = job.spacing_mm != null ? job.spacing_mm : 2.0;
const TIMEBOX = (job.timebox_s || 20) * 1000;
const BIN_LEN = 100000;

function offsetPoly(poly, delta) {
  const co = new ClipperLib.ClipperOffset(2, TOL * CLIPPER_SCALE);
  const p = poly.map(q => ({ X: Math.round(q.x * CLIPPER_SCALE), Y: Math.round(q.y * CLIPPER_SCALE) }));
  co.AddPath(p, ClipperLib.JoinType.jtRound, ClipperLib.EndType.etClosedPolygon);
  const out = new ClipperLib.Paths();
  co.Execute(out, delta * CLIPPER_SCALE);
  if (!out.length) return null;
  out.sort((a, b) => Math.abs(ClipperLib.Clipper.Area(b)) - Math.abs(ClipperLib.Clipper.Area(a)));
  return out[0].map(q => ({ x: q.X / CLIPPER_SCALE, y: q.Y / CLIPPER_SCALE }));
}
function mulberry32(a) { return function () { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const rotP = (poly, deg) => { const a = deg * Math.PI / 180; return poly.map(p => ({ x: p.x * Math.cos(a) - p.y * Math.sin(a), y: p.x * Math.sin(a) + p.y * Math.cos(a) })); };

// build instances: canonical pieces are grain-along-Y; the lay runs along X
// -> pre-rotate 90 (x,y)->(y,-x) so grain lies along the lay axis.
const parts = [];
const raw = [];                       // untransformed (pre-rotated, unoffset)
let idc = 0;
for (const pc of job.pieces) {
  const base = pc.polygon_mm.map(([x, y]) => ({ x: y, y: -x }));
  for (let q = 0; q < pc.qty; q++) {
    let poly = base, mirrored = false;
    if (pc.allow_mirror && q % 2 === 1) {
      poly = base.map(p => ({ x: -p.x, y: p.y })).reverse();
      mirrored = true;
    }
    const off = offsetPoly(poly, SPACING / 2) || poly;
    const inst = off.map(p => ({ x: p.x, y: p.y }));
    inst.id = idc; inst.source = pc.key;
    inst.rotationsAllowed = pc.allow_180 ? [0, 180] : [0];
    inst.area = Math.abs(GU.polygonArea(inst));
    raw[idc] = { key: pc.key, instance: q, poly, mirrored };
    idc++;
    parts.push(inst);
  }
}
const W = job.width_mm - SPACING;
const bin = [{ x: 0, y: 0 }, { x: BIN_LEN, y: 0 }, { x: BIN_LEN, y: W }, { x: 0, y: W }];
bin.id = -1; bin.width = BIN_LEN; bin.height = W;

const nfpCache = {};
function binNfp(part, rot) {
  const key = JSON.stringify({ A: -1, B: part.id, inside: true, Arotation: 0, Brotation: rot });
  if (!nfpCache[key]) nfpCache[key] = GU.noFitPolygonRectangle(bin, rotP(part, rot));
}
function minkowskiNfp(A, B) {
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
  if (!nfpCache[key]) {
    const nfp = minkowskiNfp(rotP(a, ra), rotP(b, rb));
    if (nfp) nfpCache[key] = nfp;
  }
}
function tryOrder(order, rots) {
  for (const p of order) binNfp(p, rots[p.id]);
  for (let i = 0; i < order.length; i++) for (let j = 0; j < i; j++)
    pairNfp(order[j], rots[order[j].id], order[i], rots[order[i].id]);
  const paths = order.map(p => { const c = p.map(q => ({ x: q.x, y: q.y })); c.id = p.id; c.source = p.source; c.rotation = rots[p.id]; return c; });
  const cfg = { clipperScale: CLIPPER_SCALE, curveTolerance: TOL, spacing: SPACING };
  sandbox.global = { env: { self: { binPolygon: bin, nfpCache, config: cfg } } };
  const pw = new sandbox.PlacementWorker(bin, paths.map(p => p.slice()), paths.map(p => p.id), paths.map(p => p.rotation), cfg, nfpCache);
  const res = pw.placePaths(paths);
  if (!res) return null;
  let maxx = 0, placed = 0;
  for (const sheet of res.placements) for (const pl of sheet) {
    const part = parts.find(p => p.id === pl.id);
    for (const p of rotP(part, pl.rotation)) maxx = Math.max(maxx, p.x + pl.x);
    placed++;
  }
  return { maxx, placed, placements: res.placements };
}

const t0 = Date.now();
const rand = mulberry32(job.seed || 42);
const byArea = parts.slice().sort((a, b) => b.area - a.area || a.id - b.id);
let best = null, trials = 0;
while (Date.now() - t0 < TIMEBOX && trials <= 200) {
  let order;
  if (trials === 0) order = byArea;
  else { order = byArea.slice(); for (let i = order.length - 1; i > 0; i--) { const j = Math.floor(rand() * (i + 1)); [order[i], order[j]] = [order[j], order[i]]; } }
  const rots = {};
  for (const p of parts) rots[p.id] = trials === 0 ? 0 : p.rotationsAllowed[Math.floor(rand() * p.rotationsAllowed.length)];
  const r = tryOrder(order, rots);
  trials++;
  if (r && r.placed === parts.length && (!best || r.maxx < best.maxx)) best = { ...r, trial: trials };
}

if (!best) {
  fs.writeFileSync(outPath, JSON.stringify({ ok: false, engine: 'svgnest', trials,
    error: 'no complete placement found (width too small or timebox too tight)' }));
  process.exit(0);
}
// ABSOLUTE polygons in the lay frame from the RAW (unoffset) outlines —
// spacing came from the offset used during nesting; the true outline is
// what the marker stores/draws/cuts.
const placements = [];
for (const sheet of best.placements) for (const pl of sheet) {
  const r = raw[pl.id];
  const a = pl.rotation * Math.PI / 180;
  const ring = r.poly.map(p => [
    Math.round((p.x * Math.cos(a) - p.y * Math.sin(a) + pl.x) * 1000) / 1000,
    Math.round((p.x * Math.sin(a) + p.y * Math.cos(a) + pl.y) * 1000) / 1000,
  ]);
  placements.push({ key: r.key, instance: r.instance, mirrored: r.mirrored,
                    rotation_deg: pl.rotation, polygon_mm: ring });
}
fs.writeFileSync(outPath, JSON.stringify({ ok: true, engine: 'svgnest',
  core: 'SVGnest-core-headless@1248dc2', trials, seed: job.seed || 42,
  timebox_s: TIMEBOX / 1000, placements }));
