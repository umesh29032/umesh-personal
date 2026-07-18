/* Digital Cutting Table — session engine (M4: extracted from the
   template, §18-f — organization, not architecture; every frozen
   behavior preserved).

   FROZEN LAWS carried over verbatim:
   - world = MILLIMETRES forever; pixels render-only; camera ≠ world.
   - state.pieces = the single runtime truth; DOM is a render target.
   - ZERO writes before Save Draft; the session dies with the page.
   - collision pipeline: boundary → collision → spacing (ONE pipeline
     for move/import/Compact/Auto Place/AI).
   - locked = selectable but immutable; grain gates rotation; pair
     gates mirror; AI = proposals only, human accepts (R6).

   M4 additions (Manufacturing Planner): MARKER PLAN session opener ·
   IMPORT QUEUE (Blueprint × plan, placement math incl. the G3
   layer-multiplier) · size-index colors (F4: by chart ORDER, never
   name) · live estimates (R2) · nap narrows rotations (G5) ·
   "Suggest Better Layout" explained verdict (R5/R6) · keys I/G ·
   plan persists with Save Draft. All inputs are ROWS — the engine
   never knows a garment name (genericity gate). */
(function () {
  'use strict';
  var CONFIG = JSON.parse(document.getElementById('ws-config').textContent);
  var VIEW_ONLY = !!CONFIG.view_only;
  var PAYLOAD = JSON.parse(document.getElementById('ws-payload').textContent);
  var GRAIN_ROTS = { strict: [0], two_way: [0, 180],
                     free: [0, 90, 180, 270] };
  // G5: one-way nap removes the 180° family (data narrowing, no new law)
  var GRAIN_ROTS_ONE_WAY = { strict: [0], two_way: [0], free: [0, 90] };
  var FABRIC_W = CONFIG.fabric_width_mm || 1500;
  var SPACING_MM = CONFIG.spacing_mm || 0;
  var SNAP_MM = 10;
  var NUDGE_MM = 1, NUDGE_FAST_MM = 10, NUDGE_JUMP_MM = 100;
  var WORLD_H = 2200;
  var svg = document.getElementById('ws-svg');
  var layer = document.getElementById('pieces-layer');
  var state = { pieces: [], seq: 0, sel: null, group: null, snap: false,
                stage: 'draft' };
  var camera = { x: 0, y: 0, scale: 1 };
  // F4 binding: palette cycles by SIZE-CHART ORDER INDEX — never names
  var SIZE_COLORS = ['#2563eb', '#059669', '#d97706',
                     '#7c3aed', '#0d9488', '#be185d'];
  var sizeColor = {};
  (CONFIG.sizes || []).forEach(function (s, i) {
    sizeColor[s.id] = SIZE_COLORS[i % SIZE_COLORS.length];
  });
  /* THE MARKER PLAN — session state (M4). No plan writes anywhere;
     it rides Save Draft into the layout's params.
     M4.5: lay vocabulary split (three-concepts law: LAY CAPABILITY) —
     multiplier = plies/layer · foldEdges = creases this lay OFFERS. */
  var LAY_MULT = { single: 1, double: 2, double_open: 2,
                   double_folded: 2, tubular: 2 };
  var LAY_FOLD_EDGES = { single: 0, double: 0, double_open: 0,
                         double_folded: 1, tubular: 2 };
  var PLAN = { started: false, group: null, roll: null, width: FABRIC_W,
               lay: 'single', multiplier: 1, foldEdges: 0, ratio: {},
               pieceIds: [], optIn: [], recipe: '', notes: '',
               oneWay: false };
  // meta accessor: unfolded instances render the DERIVED opened piece
  // (server-shipped data — the client never computes geometry)
  function metaFor(key, unfolded) {
    var m = PAYLOAD[key];
    if (!m) return m;
    if (unfolded && m.opened) {
      return { name: m.name, size: m.size, group: m.group,
               caps: m.caps, piece_id: m.piece_id, size_id: m.size_id,
               w: m.opened.w, h: m.opened.h, area: m.opened.area,
               outline: m.opened.outline };
    }
    return m;
  }
  // M4.5 Q4: pieces each placement yields (PLACEMENT MODE concept)
  function contribution(p) {
    return p.on_fold ? Math.max(1, PLAN.multiplier / 2)
                     : PLAN.multiplier;
  }
  function foldPinX(p) {   // v1: fold placements pin to the LEFT crease.
    // If the digitized half carries its fold edge on the RIGHT side,
    // the piece is auto-MIRRORED at import (mirroring a half about its
    // fold line = the identical opened piece) — the pinned edge is then
    // at piece-local (w − fold_x).
    var m = PAYLOAD[p.design_key] || {};
    var fx = m.fold_x_mm || 0;
    var w = (p._meta && p._meta.w) || 0;
    return -(p.mirror ? (w - fx) : fx);
  }

  function applyCamera() {
    svg.setAttribute('viewBox',
      camera.x + ' ' + camera.y + ' ' +
      (FABRIC_W / camera.scale) + ' ' + (WORLD_H / camera.scale));
  }
  var undoStack = [];

  /* ── geometry helpers (mm) ─────────────────────────────────────── */
  function transformedOutline(p) {
    var m = p._meta, cx = m.w / 2, cy = m.h / 2;
    var rad = p.rotation * Math.PI / 180;
    var cos = Math.cos(rad), sin = Math.sin(rad);
    var sx = p.mirror ? -1 : 1;
    return m.outline.map(function (q) {
      var x = (q[0] - cx) * sx, y = q[1] - cy;
      return [x * cos - y * sin + cx + p.x_mm,
              x * sin + y * cos + cy + p.y_mm];
    });
  }
  function bboxOf(pts) {
    var minx = 1e9, miny = 1e9, maxx = -1e9, maxy = -1e9;
    pts.forEach(function (q) {
      if (q[0] < minx) minx = q[0]; if (q[0] > maxx) maxx = q[0];
      if (q[1] < miny) miny = q[1]; if (q[1] > maxy) maxy = q[1];
    });
    return { minx: minx, miny: miny, maxx: maxx, maxy: maxy };
  }
  function refresh(p) {
    p._outline = transformedOutline(p);
    p._bbox = bboxOf(p._outline);
  }
  function segsIntersect(a, b, c, d) {
    function ccw(p1, p2, p3) {
      return (p3[1] - p1[1]) * (p2[0] - p1[0]) >
             (p2[1] - p1[1]) * (p3[0] - p1[0]);
    }
    return ccw(a, c, d) !== ccw(b, c, d) && ccw(a, b, c) !== ccw(a, b, d);
  }
  function pointInPoly(pt, poly) {
    var inside = false;
    for (var i = 0, j = poly.length - 1; i < poly.length; j = i++) {
      if ((poly[i][1] > pt[1]) !== (poly[j][1] > pt[1]) &&
          pt[0] < (poly[j][0] - poly[i][0]) * (pt[1] - poly[i][1]) /
                  (poly[j][1] - poly[i][1]) + poly[i][0]) inside = !inside;
    }
    return inside;
  }
  function segDist(a, b, c, d) {
    function ptSeg(p, u, v) {
      var dx = v[0] - u[0], dy = v[1] - u[1];
      var L2 = dx * dx + dy * dy;
      var t = L2 ? ((p[0] - u[0]) * dx + (p[1] - u[1]) * dy) / L2 : 0;
      t = Math.max(0, Math.min(1, t));
      var X = u[0] + t * dx - p[0], Y = u[1] + t * dy - p[1];
      return Math.sqrt(X * X + Y * Y);
    }
    if (segsIntersect(a, b, c, d)) return 0;
    return Math.min(ptSeg(a, c, d), ptSeg(b, c, d),
                    ptSeg(c, a, b), ptSeg(d, a, b));
  }

  /* ── THE COLLISION PIPELINE: bbox → polygon → spacing margin ── */
  function collidePair(p, q, spacing) {
    var a = p._bbox, b = q._bbox, s = spacing || 0;
    if (a.maxx + s < b.minx || b.maxx + s < a.minx ||
        a.maxy + s < b.miny || b.maxy + s < a.miny) return 'clear';
    var A = p._outline, B = q._outline, i, j;
    for (i = 0; i < A.length; i++)
      for (j = 0; j < B.length; j++)
        if (segsIntersect(A[i], A[(i + 1) % A.length],
                          B[j], B[(j + 1) % B.length])) return 'collision';
    if (pointInPoly(A[0], B) || pointInPoly(B[0], A)) return 'collision';
    if (s > 0) {
      for (i = 0; i < A.length; i++)
        for (j = 0; j < B.length; j++)
          if (segDist(A[i], A[(i + 1) % A.length],
                      B[j], B[(j + 1) % B.length]) < s) return 'spacing';
    }
    return 'clear';
  }
  function boundaryViolation(p) {
    var b = p._bbox;
    return b.minx < 0 || b.maxx > FABRIC_W || b.miny < 0;
  }
  function placementStatus(candidate, others, spacing) {
    if (boundaryViolation(candidate)) return 'boundary';
    var worst = 'clear';
    for (var i = 0; i < others.length; i++) {
      var v = collidePair(candidate, others[i], spacing);
      if (v === 'collision') return 'collision';
      if (v === 'spacing') worst = 'spacing';
    }
    return worst;
  }
  function computeCollisions() {
    var status = {};
    var ps = state.pieces;
    ps.forEach(function (p) {
      // M4.5: fold placements live ON the crease — drift/rotation =
      // its own violation channel (col-fold). Mirror is FIXED at
      // import (auto-set when the half's fold edge sits on its right).
      if (p.on_fold && (Math.abs(p.x_mm - foldPinX(p)) > 0.5
                        || p.rotation !== 0))
        status[p.instance_id] = 'fold';
      else if (boundaryViolation(p)) status[p.instance_id] = 'boundary';
    });
    for (var i = 0; i < ps.length; i++)
      for (var j = i + 1; j < ps.length; j++) {
        var v = collidePair(ps[i], ps[j], SPACING_MM);
        if (v === 'clear') continue;
        if (v === 'collision' || status[ps[i].instance_id] !== 'collision')
          status[ps[i].instance_id] = v === 'collision' ? 'collision'
            : (status[ps[i].instance_id] || 'spacing');
        if (v === 'collision' || status[ps[j].instance_id] !== 'collision')
          status[ps[j].instance_id] = v === 'collision' ? 'collision'
            : (status[ps[j].instance_id] || 'spacing');
      }
    return status;
  }

  /* ── UTILIZATION — isolated utility; display math only ── */
  function layoutMetrics(widthMm, pieces) {
    if (!pieces.length)
      return { usedCm2: 0, lengthMm: 0, utilPct: null, freeCm2: null };
    var usedCm2 = 0, maxY = 0;
    pieces.forEach(function (p) {
      usedCm2 += (p._meta.area || 0);
      if (p._bbox.maxy > maxY) maxY = p._bbox.maxy;
    });
    var lengthMm = Math.ceil(maxY / 10) * 10;
    var fabricCm2 = widthMm * lengthMm / 100;
    return { usedCm2: usedCm2, lengthMm: lengthMm,
             utilPct: fabricCm2 ? (100 * usedCm2 / fabricCm2) : null,
             freeCm2: fabricCm2 ? (fabricCm2 - usedCm2) : null };
  }

  /* ── session ops ───────────────────────────────────────────────── */
  function snapshot() {
    undoStack.push(JSON.stringify({
      pieces: state.pieces.map(function (p) {
        return { instance_id: p.instance_id, design_key: p.design_key,
                 x_mm: p.x_mm, y_mm: p.y_mm, rotation: p.rotation,
                 mirror: p.mirror, locked: p.locked,
                 on_fold: !!p.on_fold, unfolded: !!p.unfolded };
      }), group: state.group, seq: state.seq }));
    if (undoStack.length > 60) undoStack.shift();
    document.getElementById('act-undo').removeAttribute('aria-disabled');
    state.stage = 'draft';
  }
  function reviveRuntime(rows) {
    return rows.map(function (r) {
      var p = r;
      p._meta = metaFor(p.design_key, p.unfolded);
      refresh(p); return p;
    });
  }
  function undo() {
    if (!undoStack.length) return;
    var prev = JSON.parse(undoStack.pop());
    state.pieces = reviveRuntime(prev.pieces);
    state.group = prev.group; state.seq = prev.seq; state.sel = null;
    if (!undoStack.length)
      document.getElementById('act-undo').setAttribute('aria-disabled', 'true');
    render();
  }
  function hint(msg) {
    var el = document.getElementById('ws-hint');
    el.textContent = msg;
    clearTimeout(el._t);
    el._t = setTimeout(function () { el.textContent = ''; }, 4500);
  }
  function ro() {
    if (VIEW_ONLY) { hint('read-only — approved layouts are never ' +
                          'edited. Duplicate to start a new draft.'); }
    return VIEW_ONLY;
  }
  // G5: the piece's rotation set under the CURRENT lay (one-way nap
  // removes flips — pure data narrowing of the grain machinery).
  // M4.5: a fold placement never rotates — its edge lives on the crease.
  function rotsOf(p) {
    if (p.on_fold) return [0];
    var rule = p._meta && p._meta.caps ? p._meta.caps.rotation : 'two_way';
    return (PLAN.oneWay ? GRAIN_ROTS_ONE_WAY : GRAIN_ROTS)[rule] || [0];
  }

  /* ── THE IMPORT QUEUE (M4 §5/§8 · M4.5 pieces-math) — the queue
        tracks PIECES (the factory truth); each placement CONTRIBUTES
        multiplier or multiplier÷2 (fold) pieces. ─────────────────── */
  function inPlan(key) {
    var m = PAYLOAD[key];
    if (!m || m.group !== PLAN.group) return false;
    if (m.caps.optional) return PLAN.optIn.indexOf(m.piece_id) !== -1;
    return PLAN.pieceIds.indexOf(m.piece_id) !== -1;
  }
  function requiredPieces(key) {
    var m = PAYLOAD[key];
    var garments = PLAN.ratio[m.size_id] || 0;
    return garments ? m.caps.count * garments : 0;
  }
  function cutPieces(key) {
    var total = 0;
    state.pieces.forEach(function (p) {
      if (p.design_key === key) total += contribution(p);
    });
    return total;
  }
  function queueRows() {
    var rows = [];
    Object.keys(PAYLOAD).forEach(function (key) {
      if (!inPlan(key)) return;
      var req = requiredPieces(key);
      if (!req) return;
      rows.push({ key: key, m: PAYLOAD[key], req: req,
                  cut: cutPieces(key) });
    });
    // size-first (chart order), then piece name — hierarchy law
    var order = {};
    (CONFIG.sizes || []).forEach(function (s, i) { order[s.id] = i; });
    rows.sort(function (a, b) {
      return (order[a.m.size_id] - order[b.m.size_id]) ||
             (a.m.name < b.m.name ? -1 : 1);
    });
    return rows;
  }
  function esc(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
  }
  function renderQueue() {
    var box = document.getElementById('queue-body');
    if (!box) return;
    if (!PLAN.started) {
      box.innerHTML = '<p class="notready">Open the Marker Plan to ' +
                      'build the queue.</p>';
      return;
    }
    var rows = queueRows(), html = '', lastSize = null;
    var totReq = 0, totImp = 0;
    rows.forEach(function (r) {
      totReq += r.req; totImp += Math.min(r.cut, r.req);
      if (r.m.size_id !== lastSize) {
        lastSize = r.m.size_id;
        html += '<div class="q-size"><span class="q-dot" style="background:' +
                (sizeColor[r.m.size_id] || '#999') + '"></span>' +
                esc(r.m.size) + ' · ' +
                (PLAN.ratio[r.m.size_id] || 0) + ' garment(s)</div>';
      }
      var remaining = Math.max(0, r.req - r.cut);
      var caps = r.m.caps;
      var rots = (PLAN.oneWay ? GRAIN_ROTS_ONE_WAY
                              : GRAIN_ROTS)[caps.rotation] || [0];
      // R4: the operator sees WHY — rules as chips, not just counts
      html += '<div class="q-row' + (remaining ? '' : ' done') + '">' +
        '<div class="q-main"><b>' + esc(r.m.name) + '</b>' +
        '<span class="q-chips">' +
        '<span class="q-chip">req ' + r.req + ' pc</span>' +
        '<span class="q-chip">cut ' + r.cut + '</span>' +
        (caps.mirror ? '<span class="q-chip">mirror ✓</span>' : '') +
        (caps.fold ? '<span class="q-chip q-fold">fold-capable</span>'
         : caps.fold_wished
           ? '<span class="q-chip q-warn">fold edge missing</span>' : '') +
        '<span class="q-chip">rot ' + rots.join('/') + '°</span>' +
        (PLAN.multiplier > 1
          ? '<span class="q-chip q-x2">cuts 2/placement</span>' : '') +
        '</span></div>';
      // M4.5 R2-B: PLACEMENT MODES — the operator decides HOW to place
      // this instance; the Library already decided what it CAN do.
      if (remaining) {
        if (caps.fold && PLAN.foldEdges > 0) {
          html += '<span style="display:flex;flex-direction:column;gap:3px;">' +
            '<button type="button" class="tb q-import" data-mode="fold" ' +
            'data-import-key="' + esc(r.key) + '" ' +
            'title="on the crease — opens to ' +
            Math.max(1, PLAN.multiplier / 2) + ' pc/layer, half the space">' +
            'On fold</button>' +
            '<button type="button" class="tb q-import" data-mode="normal" ' +
            'data-import-key="' + esc(r.key) + '" ' +
            'title="cuts ' + PLAN.multiplier + ' pc/placement">Normally' +
            '</button></span>';
        } else if (caps.fold && !PLAN.foldEdges) {
          html += '<button type="button" class="tb q-import" ' +
            'data-mode="unfolded" data-import-key="' + esc(r.key) + '" ' +
            'title="no folded edge on this lay — the pattern unfolds ' +
            '(opened outline)">Import (unfolded)</button>';
        } else {
          html += '<button type="button" class="tb q-import" ' +
            'data-mode="normal" data-import-key="' + esc(r.key) +
            '">Import</button>';
        }
      } else {
        html += '<span class="q-ok">✓</span>';
      }
      html += '</div>';
    });
    if (!rows.length)
      html = '<p class="notready">The plan selects no pieces for this ' +
             'group — reopen the Marker Plan.</p>';
    else
      html += '<button type="button" class="tb" id="q-import-all" ' +
              'style="width:100%;margin-top:6px;">Import all remaining (' +
              Math.max(0, totReq - totImp) + ')</button>';
    box.innerHTML = html;
    var chip = document.getElementById('plan-chips');
    if (chip) chip.innerHTML =
      '<span class="q-chip">' + esc((PLAN.group || '--').toUpperCase()) +
      '</span><span class="q-chip">' + PLAN.width + ' mm</span>' +
      '<span class="q-chip">' + esc(PLAN.lay) +
      (PLAN.multiplier > 1 ? ' ×2' : '') + '</span>' +
      (PLAN.oneWay ? '<span class="q-chip q-warn">one-way nap — flips ' +
                     'disabled</span>' : '') +
      (PLAN.recipe ? '<span class="q-chip">📋 ' + esc(PLAN.recipe) +
                     '</span>' : '') +
      '<button type="button" class="tb" id="plan-edit" ' +
      'style="margin-left:6px;">Edit plan…</button>';
  }
  function nextRemainingKey() {
    var rows = queueRows();
    for (var i = 0; i < rows.length; i++)
      if (rows[i].cut < rows[i].req)
        return { key: rows[i].key, m: rows[i].m,
                 remaining: rows[i].req - rows[i].cut };
    return null;
  }
  function defaultModeFor(m, remaining) {
    // import-all/I-key: normal while it fits; fold when only a fold
    // placement fits the remaining pieces (the real master's trick)
    if (m.caps.fold && !PLAN.foldEdges) return 'unfolded';
    if (m.caps.fold && PLAN.foldEdges > 0
        && remaining < PLAN.multiplier) return 'fold';
    return 'normal';
  }

  function importPiece(key, mode) {
    if (ro()) return;
    mode = mode || 'normal';
    var m = PAYLOAD[key];
    if (!m || !m.outline) return;
    if (state.group && m.group !== state.group) {
      hint('One layout = one fabric group (LAW 12). This table is ' +
           state.group.toUpperCase() + ' — ' + m.name +
           ' is ' + m.group.toUpperCase() + '.');
      return;
    }
    // M4.5: placement-mode legality (capability × lay capability)
    if (mode === 'fold' && (!m.caps.fold || !PLAN.foldEdges)) {
      hint(!m.caps.fold
        ? m.name + ' has no fold capability (Blueprint + fold edge).'
        : 'this lay offers no folded edge — pick a folded/tubular lay.');
      return;
    }
    if (mode === 'unfolded' && !(m.caps.fold && m.opened)) {
      hint(m.name + ' has no derived opened outline.');
      return;
    }
    var onFold = mode === 'fold';
    var unfolded = mode === 'unfolded';
    // M4: the queue is the plan — over-import refused with the count;
    // M4.5: refusal is PIECES-aware and names the fold way out
    if (PLAN.started) {
      if (!inPlan(key)) {
        hint(m.caps.optional
          ? m.name + ' is OPTIONAL and not in this plan — add it in ' +
            'the Marker Plan first.'
          : m.name + ' is not in this Marker Plan.');
        return;
      }
      var remaining = requiredPieces(key) - cutPieces(key);
      var contrib = onFold ? Math.max(1, PLAN.multiplier / 2)
                           : PLAN.multiplier;
      if (remaining <= 0) {
        hint(m.name + ' · ' + m.size + ': the plan is satisfied — no '
             + 'extra copies.');
        return;
      }
      if (contrib > remaining) {
        hint(m.name + ' · ' + m.size + ': only ' + remaining +
             ' piece(s) remaining — a normal placement cuts ' +
             PLAN.multiplier + '.' +
             (m.caps.fold && PLAN.foldEdges
               ? ' Place it ON THE FOLD instead (opens to ' +
                 Math.max(1, PLAN.multiplier / 2) + ').' : ''));
        return;
      }
    }
    snapshot();
    if (!state.group) state.group = m.group;
    var meta = metaFor(key, unfolded);
    var piece = {
      instance_id: ++state.seq,
      design_key: key,
      fabric_group: m.group,
      on_fold: onFold, unfolded: unfolded,
      x_mm: 20, y_mm: 20,
      rotation: 0, mirror: false, locked: false,
      _meta: meta
    };
    refresh(piece);
    var placed = false;
    if (onFold) {
      // fold placements PIN to the crease (x fixed) — scan y only.
      // Fold edge on the RIGHT half of the pattern ⇒ auto-mirror so
      // the body opens INTO the fabric (the physical flip).
      if ((m.fold_x_mm || 0) > (meta.w || 0) / 2) piece.mirror = true;
      piece.x_mm = foldPinX(piece);
      for (var fy = 10; fy <= WORLD_H - 10 && !placed; fy += 10) {
        piece.y_mm = fy; refresh(piece);
        if (placementStatus(piece, state.pieces, SPACING_MM) === 'clear')
          placed = true;
      }
      if (!placed) { piece.y_mm = 20; refresh(piece);
                     hint('no clear spot on the fold — stacked at top.'); }
    } else {
      for (var y = 20; y <= WORLD_H - 20 && !placed; y += 50) {
        for (var x = 20; x <= FABRIC_W - 20 && !placed; x += 50) {
          piece.x_mm = x; piece.y_mm = y; refresh(piece);
          if (placementStatus(piece, state.pieces, SPACING_MM) === 'clear')
            placed = true;
        }
      }
      if (!placed) { piece.x_mm = 20; piece.y_mm = 20; refresh(piece);
                     hint('no clear space found — placed at origin.'); }
    }
    state.pieces.push(piece);
    state.sel = piece.instance_id;
    render();
  }

  function render() {
    var collisions = computeCollisions();
    var html = '';
    state.pieces.forEach(function (p) {
      var m = p._meta, cx = m.w / 2, cy = m.h / 2;
      var pts = m.outline.map(function (q) {
        return q[0] + ',' + q[1]; }).join(' ');
      var tf = 'translate(' + p.x_mm + ' ' + p.y_mm + ') ' +
               'translate(' + cx + ' ' + cy + ') rotate(' + p.rotation +
               ') scale(' + (p.mirror ? -1 : 1) + ' 1) ' +
               'translate(' + (-cx) + ' ' + (-cy) + ')';
      var col = collisions[p.instance_id];
      var cls = 'piece' + (p.instance_id === state.sel ? ' sel' : '') +
                (p.locked ? ' locked' : '') +
                (col === 'collision' ? ' col-hard' :
                 col === 'boundary' ? ' col-bound' :
                 col === 'fold' ? ' col-fold' :
                 col === 'spacing' ? ' col-space' : '');
      // M4 size tint: only when physics has nothing to say (semantic
      // color law keeps red/amber/violet/grey authority)
      var tint = (!col && !p.locked && sizeColor[m.size_id])
        ? ' style="fill:' + sizeColor[m.size_id] + ';fill-opacity:0.22"'
        : '';
      html += '<g class="' + cls + '" data-id="' + p.instance_id +
              '" transform="' + tf + '">' +
              '<polygon points="' + pts + '"' + tint + '></polygon>' +
              '<text x="' + cx + '" y="' + cy + '">' +
              (p.locked ? '🔒 ' : '') + (p.on_fold ? '⇋ ' : '') +
              m.size + ' · ' + m.name +
              (p.on_fold ? ' (fold)' : p.unfolded ? ' (opened)' : '') +
              '</text></g>';
    });
    layer.innerHTML = html;
    document.getElementById('ws-empty').style.display =
      state.pieces.length ? 'none' : 'flex';
    var imported = state.pieces.length;
    var remaining;
    if (PLAN.started) {
      remaining = 0;
      queueRows().forEach(function (r) {
        remaining += Math.max(0, r.req - r.cut); });
    } else {
      var used = {};
      state.pieces.forEach(function (p) { used[p.design_key] = 1; });
      remaining = Object.keys(PAYLOAD).length - Object.keys(used).length;
    }
    ['imported', 'placed', 'remaining'].forEach(function (k) {
      var v = k === 'remaining' ? remaining : imported;
      Array.prototype.forEach.call(
        document.querySelectorAll('.c-' + k),
        function (el) { el.textContent = v; });
    });
    var nCol = Object.keys(collisions).length;
    document.getElementById('ws-collisions').textContent = nCol;
    var metrics = layoutMetrics(FABRIC_W, state.pieces);
    Array.prototype.forEach.call(document.querySelectorAll('.c-length'),
      function (el) { el.textContent =
        metrics.lengthMm ? metrics.lengthMm + ' mm' : '--'; });
    Array.prototype.forEach.call(document.querySelectorAll('.c-util'),
      function (el) { el.textContent =
        metrics.utilPct === null ? '--'
                                 : metrics.utilPct.toFixed(1) + '%'; });
    // R2: live estimates the cutting master cares about, BEFORE save
    Array.prototype.forEach.call(document.querySelectorAll('.c-waste'),
      function (el) { el.textContent =
        metrics.utilPct === null ? '--'
                                 : (100 - metrics.utilPct).toFixed(1) + '%'; });
    // M4.5: expected = Σ per-placement contributions (fold opens to
    // multiplier÷2) — the live number the master checks
    var expectedPieces = 0;
    state.pieces.forEach(function (p) { expectedPieces += contribution(p); });
    Array.prototype.forEach.call(document.querySelectorAll('.c-expected'),
      function (el) { el.textContent =
        imported ? expectedPieces + ' / layer' : '--'; });
    var ratioTxt = '--';
    if (PLAN.started) {
      ratioTxt = (CONFIG.sizes || []).filter(function (s) {
        return PLAN.ratio[s.id]; }).map(function (s) {
        return s.label + '×' + PLAN.ratio[s.id]; }).join(' ') || '--';
    }
    Array.prototype.forEach.call(document.querySelectorAll('.c-ratio'),
      function (el) { el.textContent = ratioTxt; });
    document.getElementById('ws-group').textContent =
      state.group ? state.group.toUpperCase() :
      (PLAN.group ? PLAN.group.toUpperCase() : '--');
    var lig = document.querySelector('.li-group');
    if (lig) lig.textContent = state.group ? state.group.toUpperCase() : '--';
    document.getElementById('ws-layout').textContent =
      !state.pieces.length ? 'Empty'
        : state.stage === 'approved' ? 'Approved (read-only)'
        : state.stage === 'saved' ? 'Saved Draft'
        : state.stage === 'optimized' ? 'Optimized (unsaved)'
        : 'Draft (unsaved)';
    renderQueue();
    updateSelbar();
  }

  function selected() {
    for (var i = 0; i < state.pieces.length; i++)
      if (state.pieces[i].instance_id === state.sel) return state.pieces[i];
    return null;
  }
  function updateSelbar() {
    var p = selected();
    document.getElementById('selbar').style.display =
      p ? 'inline-flex' : 'none';
    if (!p) return;
    var rots = rotsOf(p);
    var rule = p._meta && p._meta.caps ? p._meta.caps.rotation : 'two_way';
    var rb = document.getElementById('act-rotate');
    if (p.locked || rots.length < 2) {
      rb.setAttribute('aria-disabled', 'true');
      rb.title = p.locked ? 'locked piece'
        : p.on_fold ? 'fold placement — the edge lives on the crease'
        : PLAN.oneWay && (GRAIN_ROTS[rule] || []).length > 1
          ? 'one-way nap — flips disabled on this fabric'
          : 'grain rule "' + rule + '" — rotation locked';
    } else { rb.removeAttribute('aria-disabled'); rb.title = 'Rotate (R)'; }
    var mb = document.getElementById('act-mirror');
    var canMirror = p._meta && p._meta.caps && p._meta.caps.mirror;
    if (p.locked || p.on_fold || !canMirror) {
      mb.setAttribute('aria-disabled', 'true');
      mb.title = p.locked ? 'locked piece'
        : p.on_fold ? 'symmetric piece — the fold IS the mirror'
        : 'mirror only for pair pieces (Blueprint rule)';
    } else { mb.removeAttribute('aria-disabled'); mb.title = 'Mirror (M)'; }
    document.getElementById('act-lock').textContent =
      p.locked ? '🔓 Unlock' : '🔒 Lock';
  }

  function rotateSel() {
    if (ro()) return;
    var p = selected(); if (!p) return;
    if (p.locked) { hint('locked piece — unlock to edit'); return; }
    var rots = rotsOf(p);
    if (rots.length < 2) {
      var rrule = p._meta && p._meta.caps ? p._meta.caps.rotation
                                          : 'two_way';
      hint(p.on_fold
        ? 'fold placement — the edge lives on the crease'
        : PLAN.oneWay && (GRAIN_ROTS[rrule] || []).length > 1
          ? 'one-way nap — flips disabled on this fabric'
          : 'grain rule "' + rrule + '" — rotation locked');
      return; }
    snapshot();
    var i = rots.indexOf(p.rotation);
    p.rotation = rots[(i + 1) % rots.length];
    refresh(p); render();
  }
  function mirrorSel() {
    if (ro()) return;
    var p = selected(); if (!p) return;
    if (p.locked) { hint('locked piece — unlock to edit'); return; }
    if (p.on_fold) {
      hint('symmetric piece — the fold IS the mirror'); return; }
    if (!(p._meta && p._meta.caps && p._meta.caps.mirror)) {
      hint('mirror only for pair pieces (Blueprint rule)'); return; }
    snapshot(); p.mirror = !p.mirror; refresh(p); render();
  }
  function deleteSel() {
    if (ro()) return;
    var p = selected(); if (!p) return;
    if (p.locked) { hint('locked piece — unlock before deleting'); return; }
    snapshot();
    state.pieces = state.pieces.filter(function (q) { return q !== p; });
    state.sel = null;
    if (!state.pieces.length) state.group = null;
    render();
  }
  function lockSel() {
    if (ro()) return;
    var p = selected(); if (!p) return;
    snapshot(); p.locked = !p.locked; render();
  }

  document.addEventListener('click', function (e) {
    var b = e.target.closest('.dr-import, .q-import');
    if (b) { importPiece(b.dataset.importKey, b.dataset.mode); return; }
    if (e.target.id === 'q-import-all') {
      var nxt, guard = 0, before;
      while ((nxt = nextRemainingKey()) && guard++ < 200) {
        before = state.pieces.length;
        importPiece(nxt.key, defaultModeFor(nxt.m, nxt.remaining));
        if (state.pieces.length === before) break;   // refusal — stop
      }
      return;
    }
    if (e.target.id === 'plan-edit') openPlan();
  });
  document.getElementById('act-rotate').addEventListener('click', rotateSel);
  document.getElementById('act-mirror').addEventListener('click', mirrorSel);
  document.getElementById('act-delete').addEventListener('click', deleteSel);
  document.getElementById('act-lock').addEventListener('click', lockSel);
  document.getElementById('act-undo').addEventListener('click', undo);
  document.getElementById('tb-grid').addEventListener('click', function () {
    state.snap = !state.snap;
    this.setAttribute('aria-pressed', state.snap ? 'true' : 'false');
    hint(state.snap ? 'grid snap ON (' + SNAP_MM + ' mm)' : 'grid snap off');
  });

  /* ── ZOOM = camera only. World mm never change. ── */
  function zoomAt(factor, wx, wy) {
    var ns = Math.min(6, Math.max(0.5, camera.scale * factor));
    if (wx === undefined) {
      wx = camera.x + FABRIC_W / camera.scale / 2;
      wy = camera.y + WORLD_H / camera.scale / 2;
    }
    camera.x = wx - (wx - camera.x) * (camera.scale / ns);
    camera.y = wy - (wy - camera.y) * (camera.scale / ns);
    camera.scale = ns;
    applyCamera();
  }
  document.getElementById('tb-zoom').addEventListener('click', function (e) {
    zoomAt(e.shiftKey ? 0.8 : 1.25);
  });
  svg.addEventListener('wheel', function (e) {
    e.preventDefault();
    var pt = svgPoint(e);
    zoomAt(e.deltaY < 0 ? 1.15 : 0.87, pt.x, pt.y);
  }, { passive: false });

  /* ── COMPACT — manual ASSIST, not an optimizer ── */
  var RANK = { clear: 0, spacing: 1, boundary: 2, collision: 3 };
  function overflow(p) {
    var b = p._bbox;
    return Math.max(0, b.maxx - FABRIC_W) + Math.max(0, -b.minx) +
           Math.max(0, -b.miny);
  }
  function tryShift(p, dx, dy, others) {
    var ox = p.x_mm, oy = p.y_mm;
    var vBefore = placementStatus(p, others, SPACING_MM);
    var oBefore = overflow(p);
    p.x_mm += dx; p.y_mm += dy; refresh(p);
    var vAfter = placementStatus(p, others, SPACING_MM);
    if (RANK[vAfter] < RANK[vBefore]) return true;
    if (vAfter === 'clear' && vBefore === 'clear') return true;
    if (vAfter === 'boundary' && vBefore === 'boundary' &&
        overflow(p) < oBefore) return true;
    p.x_mm = ox; p.y_mm = oy; refresh(p);
    return false;
  }
  function compact() {
    if (ro()) return;
    if (!state.pieces.length) return;
    snapshot();
    var moved = 0, pass, guard = 0;
    do {
      pass = false; guard++;
      state.pieces.forEach(function (p) {
        if (p.locked) return;
        var others = state.pieces.filter(function (q) { return q !== p; });
        var step;
        for (step = 50; step >= 1; step = (step === 50 ? 10 : step === 10 ? 1 : 0)) {
          if (!step) break;
          // M4.5: fold placements are x-PINNED — gravity works in y only
          if (!p.on_fold)
            while (tryShift(p, -step, 0, others)) { pass = true; moved++; }
          while (tryShift(p, 0, -step, others)) { pass = true; moved++; }
        }
      });
    } while (pass && guard < 40);
    if (!moved) { undoStack.pop(); hint('already compact.'); }
    else hint('compacted — gaps removed. Undo restores.');
    render();
  }
  document.getElementById('act-compact').addEventListener('click', compact);

  /* ── AUTO PLACE — deterministic first-fit, never search, never AI ── */
  function autoPlace() {
    if (ro()) return;
    // M4.5: fold placements stay pinned — auto-place flows around them
    var movable = state.pieces.filter(function (p) {
      return !p.locked && !p.on_fold; });
    if (!movable.length) { hint('every piece is locked.'); return; }
    snapshot();
    movable.sort(function (a, b) {
      return (b._meta.area - a._meta.area) ||
             (a.design_key < b.design_key ? -1 : a.design_key > b.design_key ? 1 : 0) ||
             (a.instance_id - b.instance_id);
    });
    var placed = state.pieces.filter(function (p) {
      return p.locked || p.on_fold; });
    var stuck = 0;
    movable.forEach(function (p) {
      var ok = false;
      for (var y = 10; y <= WORLD_H - 10 && !ok; y += 10) {
        for (var x = 10; x <= FABRIC_W - 10 && !ok; x += 10) {
          p.x_mm = x; p.y_mm = y; refresh(p);
          if (placementStatus(p, placed, SPACING_MM) === 'clear') ok = true;
        }
      }
      if (!ok) stuck++;
      placed.push(p);
    });
    hint(stuck ? 'auto-placed with ' + stuck + ' piece(s) unplaceable.'
               : 'auto-placed — deterministic first-fit (not AI).');
    render();
  }
  document.getElementById('act-autoplace').addEventListener('click',
                                                            autoPlace);

  /* ── SUGGEST BETTER LAYOUT (R5/R6) — the ONE engine, stateless.
        M4 change of PRESENTATION only: the engine result becomes a
        PENDING PROPOSAL with an explained comparison (current vs
        suggested · waste saved · pieces moved) and explicit
        [Accept]/[Keep] — factories trust explanations, not magic. ── */
  function getCookie(name) {
    var m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return m ? m.pop() : '';
  }
  function toEngineRing(pts) {
    return pts.map(function (q) {
      return [Math.round(q[1] * 100) / 100, Math.round(q[0] * 100) / 100];
    });
  }
  function applyPlacement(p, plc) {
    p.rotation = ((plc.rotation_deg % 360) + 360) % 360;
    p.mirror = !!plc.mirrored;
    p.x_mm = 0; p.y_mm = 0; refresh(p);
    var minAlong = 1e9, minAcross = 1e9;
    plc.polygon_mm.forEach(function (q) {
      if (q[0] < minAlong) minAlong = q[0];
      if (q[1] < minAcross) minAcross = q[1];
    });
    p.x_mm = Math.round((minAcross - p._bbox.minx) * 100) / 100;
    p.y_mm = Math.round((minAlong - p._bbox.miny) * 100) / 100;
    refresh(p);
  }
  var pendingSuggestion = null;
  function verdictBox(html) {
    var el = document.getElementById('ai-verdict');
    el.innerHTML = html;
    el.style.display = html ? 'block' : 'none';
  }
  function suggestLayout() {
    if (!state.pieces.length) { hint('import pieces first.'); return; }
    var btn = document.getElementById('tb-ai');
    if (btn.getAttribute('aria-disabled') === 'true') return;
    btn.setAttribute('aria-disabled', 'true');
    var oldLabel = btn.textContent;
    btn.textContent = 'Searching…';
    var placements = state.pieces.map(function (p) {
      var rule = p._meta && p._meta.caps ? p._meta.caps.rotation
                                         : 'two_way';
      return { key: p.design_key, instance: p.instance_id,
               polygon_mm: toEngineRing(p._outline),
               // M4.5 Q7-1: fold placements = FIXED obstacles for the
               // engine (the existing locked mechanism — zero engine
               // changes; the crease pin survives every suggestion)
               locked: p.locked || p.on_fold,
               rotation_deg: p.rotation, mirrored: p.mirror,
               // grain law + G5: one-way nap removes flips
               allow_180: !PLAN.oneWay && rule !== 'strict' };
    });
    fetch(CONFIG.urls.optimize, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json',
                 'X-CSRFToken': getCookie('csrftoken') },
      body: JSON.stringify({ width_mm: FABRIC_W, height_mm: WORLD_H,
                             spacing_mm: SPACING_MM, effort: 'fast',
                             placements: placements })
    }).then(function (r) { return r.json(); }).then(function (res) {
      btn.removeAttribute('aria-disabled');
      btn.textContent = oldLabel;
      if (!res.ok) { hint('suggestion failed: ' + (res.error || '')); return; }
      var best = (res.options || [])[0];
      if (!best || best.worse_than_current) {
        verdictBox('');
        hint('No better layout found — yours stands.'); return;
      }
      var du = best.delta_utilization_pct;
      if (du !== null && du <= 0.05) {
        verdictBox('');
        hint('No better layout found — yours stands.'); return;
      }
      // R6: explain, then let the human decide
      var cur = layoutMetrics(FABRIC_W, state.pieces);
      var movedN = 0;
      var byId = {};
      state.pieces.forEach(function (p) { byId[p.instance_id] = p; });
      best.placements.forEach(function (plc) {
        var p = byId[plc.instance];
        if (p && !p.locked) movedN++;
      });
      pendingSuggestion = best;
      verdictBox(
        '<b>Suggested layout found.</b> ' +
        'Current: ' + (cur.utilPct === null ? '--'
                       : cur.utilPct.toFixed(1)) + '% · ' +
        cur.lengthMm + ' mm → Suggested: +' + du + '% utilization, ' +
        best.delta_length_mm + ' mm length (waste saved: ' + du + '%). ' +
        movedN + ' piece(s) would move; locked pieces stay. ' +
        '<button type="button" class="tb tb-live" id="ai-accept">' +
        'Accept suggestion</button> ' +
        '<button type="button" class="tb" id="ai-keep">Keep current' +
        '</button>');
    }).catch(function () {
      btn.removeAttribute('aria-disabled');
      btn.textContent = oldLabel;
      hint('suggestion request failed — layout unchanged.');
    });
  }
  document.getElementById('tb-ai').addEventListener('click', suggestLayout);
  document.addEventListener('click', function (e) {
    if (e.target.id === 'ai-keep') {
      pendingSuggestion = null; verdictBox('');
      hint('kept your layout — nothing changed.');
    } else if (e.target.id === 'ai-accept' && pendingSuggestion) {
      snapshot();
      var byId = {};
      state.pieces.forEach(function (p) { byId[p.instance_id] = p; });
      pendingSuggestion.placements.forEach(function (plc) {
        var p = byId[plc.instance];
        // fold placements were sent as fixed obstacles — never re-apply
        if (p && !p.locked && !p.on_fold) applyPlacement(p, plc);
      });
      pendingSuggestion = null;
      state.stage = 'optimized';   // never 'approved' — human-only
      verdictBox('');
      render();
      var tight = document.querySelectorAll('g.piece.col-space').length;
      hint('suggestion applied.' +
           (tight ? ' ' + tight + ' spot(s) tighter than the ' +
                    SPACING_MM + ' mm rule — nudge if needed.' : '') +
           ' Undo restores.');
    }
  });

  /* ── SAVE DRAFT — the ONE pipeline; the Marker Plan rides along ── */
  function saveDraft() {
    if (ro()) return;
    if (!state.pieces.length) { hint('import pieces first.'); return; }
    var hard = document.querySelectorAll(
      'g.piece.col-hard, g.piece.col-bound').length;
    if (hard) { hint('resolve ' + hard + ' collision/boundary ' +
                     'violation(s) before saving — the verifier will ' +
                     'refuse them anyway.'); return; }
    var btn = document.getElementById('act-save');
    btn.setAttribute('aria-disabled', 'true');
    var placements = state.pieces.map(function (p) {
      return { key: p.design_key, instance: p.instance_id,
               polygon_mm: toEngineRing(p._outline),
               locked: p.locked, rotation_deg: p.rotation,
               mirrored: p.mirror,
               // M4.5: the PLACEMENT MODE persists with the asset —
               // content math reads it (fold opens to multiplier÷2)
               on_fold: !!p.on_fold, unfolded: !!p.unfolded };
    });
    fetch(CONFIG.urls.save, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json',
                 'X-CSRFToken': getCookie('csrftoken') },
      body: JSON.stringify({ width_mm: FABRIC_W, height_mm: WORLD_H,
                             spacing_mm: SPACING_MM,
                             fabric_group: state.group,
                             placements: placements,
                             layering_type: PLAN.started ? PLAN.lay
                                                         : 'single',
                             ratio: PLAN.started ? PLAN.ratio : {},
                             roll_ref: PLAN.roll,
                             recipe_label: PLAN.recipe,
                             notes: PLAN.notes })
    }).then(function (r) { return r.json(); }).then(function (res) {
      btn.removeAttribute('aria-disabled');
      if (!res.ok) { hint('save refused: ' + res.error); return; }
      state.stage = 'saved';
      var ap = document.getElementById('tb-approve');
      ap.href = res.approve_url;
      ap.removeAttribute('aria-disabled');
      ap.classList.add('tb-live');
      ap.title = 'Approve this saved draft (human act — review first)';
      render();
      hint('draft #' + res.candidate_id + ' saved (immutable, verified, '
           + res.length_mm + ' mm) — Approve Layout is now available.');
    }).catch(function () {
      btn.removeAttribute('aria-disabled');
      hint('save failed — nothing stored.');
    });
  }
  document.getElementById('act-save').addEventListener('click', saveDraft);

  /* ── M4.5 Q8: the fabric SHOWS its folded edge(s) — dashed FOLD
        line(s) drawn under the pieces (double_folded: left crease;
        tubular: both sides; v1 placement pins to the LEFT crease). ── */
  function drawFoldLines() {
    svg.querySelectorAll('.fabric-fold').forEach(function (el) {
      el.remove(); });
    if (!PLAN.foldEdges) return;
    var xs = PLAN.foldEdges === 2 ? [0, FABRIC_W] : [0];
    xs.forEach(function (x) {
      var l = document.createElementNS('http://www.w3.org/2000/svg',
                                       'line');
      l.setAttribute('class', 'fabric-fold');
      l.setAttribute('x1', x); l.setAttribute('y1', 0);
      l.setAttribute('x2', x); l.setAttribute('y2', WORLD_H);
      svg.insertBefore(l, layer);
      var t = document.createElementNS('http://www.w3.org/2000/svg',
                                       'text');
      t.setAttribute('class', 'fabric-fold');
      t.setAttribute('x', x + (x ? -14 : 14));
      t.setAttribute('y', 60);
      t.setAttribute('writing-mode', 'tb');
      t.textContent = 'FOLD';
      svg.insertBefore(t, layer);
    });
  }

  /* ── THE MARKER PLAN dialog (M4 §2/§3) — session state only ── */
  function planEl(id) { return document.getElementById(id); }
  function openPlan() {
    if (VIEW_ONLY) return;
    var dlg = planEl('plan-dialog');
    if (!dlg) return;
    dlg.style.display = 'flex';
    syncPlanForm();
  }
  function closePlan() { planEl('plan-dialog').style.display = 'none'; }
  function groupsInPayload() {
    var gs = {};
    Object.keys(PAYLOAD).forEach(function (k) {
      gs[PAYLOAD[k].group] = 1; });
    return Object.keys(gs).sort();
  }
  function piecesOfGroup(g) {
    // unique piece rows of the group (from the payload — Blueprint data)
    var seen = {}, out = [];
    Object.keys(PAYLOAD).forEach(function (k) {
      var m = PAYLOAD[k];
      if (m.group !== g || seen[m.piece_id]) return;
      seen[m.piece_id] = 1;
      // M4.5 capabilities contract: plan-dialog piece facts read caps
      out.push({ id: m.piece_id, name: m.name, count: m.caps.count,
                 optional: m.caps.optional, pair: m.caps.mirror });
    });
    out.sort(function (a, b) { return a.name < b.name ? -1 : 1; });
    return out;
  }
  function syncPlanForm() {
    var g = planEl('plan-group').value || groupsInPayload()[0] || '';
    // pieces of the group: mandatory preselected, optional opt-in
    var box = planEl('plan-pieces');
    box.innerHTML = piecesOfGroup(g).map(function (p) {
      var on = PLAN.started
        ? (p.optional ? PLAN.optIn.indexOf(p.id) !== -1
                      : PLAN.pieceIds.indexOf(p.id) !== -1)
        : !p.optional;
      return '<label class="plan-piece"><input type="checkbox" ' +
        'data-piece="' + p.id + '" data-optional="' + (p.optional ? 1 : 0) +
        '"' + (on ? ' checked' : '') + '> ' + esc(p.name) +
        ' ×' + p.count + (p.pair ? ' (pair)' : '') +
        (p.optional ? ' <em>optional</em>' : '') + '</label>';
    }).join('');
  }
  function startPlan() {
    var g = planEl('plan-group').value;
    if (!g) { hint('pick a fabric group.'); return; }
    if (state.group && state.group !== g) {
      hint('this session already holds ' + state.group.toUpperCase() +
           ' pieces (LAW 12) — delete them or reload to change group.');
      return;
    }
    var w = parseInt(planEl('plan-width').value, 10);
    if (!w || w < 100) { hint('usable width in mm, please.'); return; }
    var lay = (document.querySelector('input[name="plan-lay"]:checked')
               || {}).value || 'single';
    var ratio = {}, any = false;
    (CONFIG.sizes || []).forEach(function (s) {
      var on = planEl('plan-size-' + s.id).checked;
      var n = parseInt(planEl('plan-n-' + s.id).value, 10) || 1;
      if (on) { ratio[s.id] = Math.max(1, n); any = true; }
    });
    if (!any) { hint('tick at least one size.'); return; }
    var pieceIds = [], optIn = [];
    Array.prototype.forEach.call(
      document.querySelectorAll('#plan-pieces input:checked'),
      function (c) {
        var id = parseInt(c.dataset.piece, 10);
        pieceIds.push(id);
        if (c.dataset.optional === '1') optIn.push(id);
      });
    if (!pieceIds.length) { hint('tick at least one piece.'); return; }
    var rollSel = planEl('plan-roll');
    var roll = null, oneWay = false;
    if (rollSel.value) {
      var r = (CONFIG.rolls || []).filter(function (x) {
        return String(x.id) === rollSel.value; })[0];
      if (r) { roll = { id: r.id, label: r.label };
               oneWay = !!r.one_way; }
    }
    PLAN.started = true;
    PLAN.group = g; PLAN.width = w; PLAN.lay = lay;
    PLAN.multiplier = LAY_MULT[lay] || 1;
    PLAN.foldEdges = LAY_FOLD_EDGES[lay] || 0;
    PLAN.ratio = ratio; PLAN.pieceIds = pieceIds; PLAN.optIn = optIn;
    PLAN.roll = roll; PLAN.oneWay = oneWay;
    PLAN.recipe = planEl('plan-recipe-name').dataset.loaded || '';
    PLAN.notes = planEl('plan-notes').value || '';
    // the plan's width IS the session fabric width (human-confirmed)
    FABRIC_W = w;
    applyCamera();
    drawFoldLines();
    var rl = document.getElementById('ruler-w');
    if (rl) rl.textContent = w + ' mm';
    Array.prototype.forEach.call(document.querySelectorAll('.c-fabricw'),
      function (el) { el.textContent = w + ' mm'; });
    closePlan();
    render();
    hint('Marker Plan set — the Import Queue is ready.');
  }
  function loadRecipe(id) {
    var r = (CONFIG.recipes || []).filter(function (x) {
      return String(x.id) === String(id); })[0];
    if (!r) return;
    planEl('plan-group').value = r.fabric_group;
    syncPlanForm();
    Array.prototype.forEach.call(
      document.querySelectorAll('#plan-pieces input'),
      function (c) {
        c.checked = r.piece_ids.indexOf(
          parseInt(c.dataset.piece, 10)) !== -1;
      });
    (CONFIG.sizes || []).forEach(function (s) {
      var n = r.size_ratio[String(s.id)];
      planEl('plan-size-' + s.id).checked = !!n;
      if (n) planEl('plan-n-' + s.id).value = n;
    });
    var lay = document.querySelector(
      'input[name="plan-lay"][value="' + r.layering_type + '"]');
    if (lay) lay.checked = true;
    planEl('plan-notes').value = r.notes || '';
    planEl('plan-recipe-name').value = r.name;
    planEl('plan-recipe-name').dataset.loaded = r.name;
  }
  function saveRecipe() {
    var name = planEl('plan-recipe-name').value.trim();
    if (!name) { hint('name the recipe first (e.g. "Body marker · 42″").');
                 return; }
    var pieceIds = [];
    Array.prototype.forEach.call(
      document.querySelectorAll('#plan-pieces input:checked'),
      function (c) { pieceIds.push(parseInt(c.dataset.piece, 10)); });
    var ratio = {};
    (CONFIG.sizes || []).forEach(function (s) {
      if (planEl('plan-size-' + s.id).checked)
        ratio[s.id] = parseInt(planEl('plan-n-' + s.id).value, 10) || 1;
    });
    fetch(CONFIG.urls.recipe, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json',
                 'X-CSRFToken': getCookie('csrftoken') },
      body: JSON.stringify({
        name: name, fabric_group: planEl('plan-group').value,
        layering_type: (document.querySelector(
          'input[name="plan-lay"]:checked') || {}).value || 'single',
        piece_ids: pieceIds, size_ratio: ratio,
        notes: planEl('plan-notes').value || '' })
    }).then(function (r) { return r.json(); }).then(function (res) {
      if (!res.ok) { hint('recipe refused: ' + res.error); return; }
      CONFIG.recipes = res.recipes;
      var sel = planEl('plan-recipe');
      sel.innerHTML = '<option value="">— blank session —</option>' +
        res.recipes.map(function (r2) {
          return '<option value="' + r2.id + '">' + esc(r2.name) +
                 '</option>'; }).join('');
      sel.value = String(res.recipe_id);
      planEl('plan-recipe-name').dataset.loaded = name;
      hint('recipe "' + name + '" saved — reusable manufacturing ' +
           'knowledge.');
    }).catch(function () { hint('recipe save failed.'); });
  }
  (function wirePlan() {
    var dlg = planEl('plan-dialog');
    if (!dlg) return;
    planEl('plan-group').addEventListener('change', syncPlanForm);
    planEl('plan-roll').addEventListener('change', function () {
      var r = (CONFIG.rolls || []).filter(function (x) {
        return String(x.id) === planEl('plan-roll').value; })[0];
      if (r && r.usable_width_mm)
        planEl('plan-width').value = r.usable_width_mm;
      planEl('plan-nap').textContent = (r && r.one_way)
        ? 'one-way nap — 180° flips will be disabled' : '';
    });
    planEl('plan-recipe').addEventListener('change', function () {
      if (this.value) loadRecipe(this.value);
    });
    planEl('plan-start').addEventListener('click', startPlan);
    planEl('plan-save-recipe').addEventListener('click', saveRecipe);
    planEl('plan-close').addEventListener('click', closePlan);
    // the opener: a fresh editable session begins with the plan
    if (!VIEW_ONLY) openPlan();
  })();

  /* ── load an approved layout (View / Duplicate) ── */
  (function loadInitial() {
    var el = document.getElementById('ws-initial');
    if (!el) return;
    var rows;
    try { rows = JSON.parse(el.textContent); } catch (e) { return; }
    if (!rows || !rows.length) return;
    rows.forEach(function (plc) {
      var m = PAYLOAD[plc.key];
      if (!m || !m.outline) return;
      var piece = {
        instance_id: ++state.seq, design_key: plc.key,
        fabric_group: m.group, grain_rule: m.grain, pair: m.pair,
        x_mm: 0, y_mm: 0,
        rotation: 0, mirror: false, locked: !!plc.locked, _meta: m };
      applyPlacement(piece, plc);
      if (!state.group) state.group = m.group;
      state.pieces.push(piece);
    });
    state.stage = VIEW_ONLY ? 'approved' : 'draft';
    undoStack.length = 0;
    document.getElementById('act-undo').setAttribute('aria-disabled',
                                                     'true');
    if (VIEW_ONLY) {
      document.getElementById('act-save')
        .setAttribute('aria-disabled', 'true');
    }
    // a loaded layout already fixes the group — prefill + skip the dialog
    if (!VIEW_ONLY && state.group) {
      var gsel = planEl('plan-group');
      if (gsel) { gsel.value = state.group; syncPlanForm(); }
    }
    render();
  })();

  var nudgeArmed = true, nudgeTimer = null;
  function nudgeSel(dx, dy) {
    if (ro()) return;
    var p = selected(); if (!p) return;
    if (p.locked) { hint('locked piece — unlock to move'); return; }
    if (p.on_fold && dx) {
      hint('fold placement — slides along the crease only'); return; }
    if (nudgeArmed) { snapshot(); nudgeArmed = false; }
    clearTimeout(nudgeTimer);
    nudgeTimer = setTimeout(function () { nudgeArmed = true; }, 800);
    p.x_mm += dx; p.y_mm += dy; refresh(p); render();
  }

  function svgPoint(evt) {
    var pt = svg.createSVGPoint();
    pt.x = evt.clientX; pt.y = evt.clientY;
    return pt.matrixTransform(svg.getScreenCTM().inverse());
  }
  var drag = null, pan = null;
  svg.addEventListener('pointerdown', function (e) {
    var g = e.target.closest('g.piece');
    if (!g) {
      state.sel = null; render();
      pan = { cx: e.clientX, cy: e.clientY,
              camx: camera.x, camy: camera.y,
              mmppx: (FABRIC_W / camera.scale) / svg.clientWidth };
      svg.setPointerCapture(e.pointerId);
      return;
    }
    state.sel = parseInt(g.dataset.id, 10);
    var p = selected(); var pt = svgPoint(e);
    if (VIEW_ONLY) { drag = null; render(); return; }
    if (p.locked) { drag = null; render();
      hint('locked piece — selectable, not movable'); return; }
    snapshot();
    drag = { p: p, dx: pt.x - p.x_mm, dy: pt.y - p.y_mm, moved: false };
    svg.setPointerCapture(e.pointerId);
    render();
  });
  svg.addEventListener('pointermove', function (e) {
    if (pan) {
      camera.x = pan.camx - (e.clientX - pan.cx) * pan.mmppx;
      camera.y = pan.camy - (e.clientY - pan.cy) * pan.mmppx;
      applyCamera();
      return;
    }
    if (!drag) return;
    var pt = svgPoint(e);
    var nx = pt.x - drag.dx, ny = pt.y - drag.dy;
    if (state.snap) {
      nx = Math.round(nx / SNAP_MM) * SNAP_MM;
      ny = Math.round(ny / SNAP_MM) * SNAP_MM;
    }
    // M4.5: fold placements slide along the crease only (x pinned)
    if (drag.p.on_fold) nx = foldPinX(drag.p);
    drag.p.x_mm = Math.round(nx); drag.p.y_mm = Math.round(ny);
    drag.moved = true;
    refresh(drag.p);
    render();
  });
  svg.addEventListener('pointerup', function () {
    if (drag && !drag.moved) undoStack.pop();
    drag = null; pan = null;
  });

  document.addEventListener('keydown', function (e) {
    if (/input|textarea|select/i.test(e.target.tagName)) return;
    if (e.key === 'r' || e.key === 'R') rotateSel();
    else if (e.key === 'm' || e.key === 'M') mirrorSel();
    else if (e.key === 'l' || e.key === 'L') lockSel();
    else if (e.key === 'Delete') deleteSel();
    // M4 keys: I = import next remaining · G = grid toggle
    else if (e.key === 'i' || e.key === 'I') {
      var k = nextRemainingKey();
      if (k) importPiece(k.key, defaultModeFor(k.m, k.remaining));
      else hint('queue complete — nothing left.');
    }
    else if (e.key === 'g' || e.key === 'G')
      document.getElementById('tb-grid').click();
    else if (e.key === '0') { camera = { x: 0, y: 0, scale: 1 }; applyCamera(); }
    else if (e.key.indexOf('Arrow') === 0 && selected()) {
      e.preventDefault();
      var step = e.shiftKey ? NUDGE_FAST_MM : NUDGE_MM;
      if (e.key === 'ArrowLeft') nudgeSel(-step, 0);
      else if (e.key === 'ArrowRight') nudgeSel(step, 0);
      else if (e.key === 'ArrowUp') nudgeSel(0, -step);
      else if (e.key === 'ArrowDown') nudgeSel(0, step);
    }
    else if ((e.ctrlKey || e.metaKey) && e.key === 'z') {
      e.preventDefault(); undo(); }
  });
})();
