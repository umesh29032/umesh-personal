"""svg_render — READ-ONLY canonical-geometry -> SVG string (ADR-C §7).

Pure string building, no libraries, no persistence. Canonical is y-UP;
SVG is y-DOWN — the flip happens here and nowhere else. Sizes are real
millimetres so `width="600mm"` prints at true scale (Gate-1 overlay).
"""
import math

from .units import um_to_mm


def _xesc(s):
    """XML text escape — piece names are management-entered, but an
    '&' or '<' must never corrupt a production artifact (M9 review)."""
    return (str(s).replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;'))


def _pts(ring, h_um):
    return ' '.join(f'{x / 1000:.3f},{(h_um - y) / 1000:.3f}'
                    for x, y in ring)


def geometry_svg(payload, *, css_class='piece-svg', true_scale=False,
                 show_grain=True):
    """Render one canonical payload as a self-contained <svg> element."""
    outer = payload['outer']
    w_um = max(p[0] for p in outer)
    h_um = max(p[1] for p in outer)
    w_mm, h_mm = um_to_mm(w_um), um_to_mm(h_um)
    # true scale: the width/height attrs must span the SAME extent as the
    # viewBox (piece + 5 mm pad each side) or the print shrinks silently
    size_attr = (f'width="{w_mm + 10}mm" height="{h_mm + 10}mm"'
                 if true_scale else 'width="100%"')
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" class="{css_class}" '
        f'viewBox="-5 -5 {w_um / 1000 + 10:.1f} {h_um / 1000 + 10:.1f}" '
        f'{size_attr} preserveAspectRatio="xMidYMid meet" '
        f'data-w-mm="{w_mm}" data-h-mm="{h_mm}">',
        f'<polygon points="{_pts(outer, h_um)}" fill="#f6efe0" '
        'stroke="#7a5c2e" stroke-width="1.2" vector-effect="non-scaling-stroke"/>',
    ]
    for hole in payload.get('holes') or []:
        parts.append(f'<polygon points="{_pts(hole, h_um)}" fill="#fff" '
                     'stroke="#7a5c2e" stroke-width="1" '
                     'vector-effect="non-scaling-stroke"/>')
    feats = payload.get('features') or {}
    for line in feats.get('internal_lines') or []:
        parts.append(f'<polyline points="{_pts(line, h_um)}" fill="none" '
                     'stroke="#b08c4f" stroke-width="0.8" '
                     'stroke-dasharray="4 3" vector-effect="non-scaling-stroke"/>')
    grain = feats.get('grain')
    if show_grain and grain and grain.get('angle_cdeg') is not None:
        # svg centre == geometric centre; canonical y-up angle flips its
        # sin component when drawn in svg's y-down frame
        cx, cy = w_um / 2000.0, h_um / 2000.0
        L = max(w_um, h_um) / 5000.0
        a = math.radians(grain['angle_cdeg'] / 100.0)
        x1, y1 = cx - L * math.cos(a), cy + L * math.sin(a)
        x2, y2 = cx + L * math.cos(a), cy - L * math.sin(a)
        parts.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" '
                     f'x2="{x2:.2f}" y2="{y2:.2f}" stroke="#2e6e4e" '
                     'stroke-width="1.4" marker-end="url(#pai-grain-arrow)" '
                     'vector-effect="non-scaling-stroke"/>')
        parts.insert(1, '<defs><marker id="pai-grain-arrow" viewBox="0 0 10 10" '
                        'refX="8" refY="5" markerWidth="6" markerHeight="6" '
                        'orient="auto-start-reverse">'
                        '<path d="M0 0 L10 5 L0 10 z" fill="#2e6e4e"/>'
                        '</marker></defs>')
    parts.append('</svg>')
    return '\n'.join(parts)


def marker_svg(placements, width_mm, length_mm, css_class='marker-svg',
               summary=None):
    """Render a generated-marker layout (READ-ONLY, pure strings).
    Placements are absolute lay-frame rings (x = length, y = width, mm);
    svg y-down flip about the fabric width happens here only.
    summary (M8, §3f): optional dict stamped as <metadata>/<desc> so the
    exported artifact carries the Production Layout Summary."""
    import json as _json
    w = float(width_mm)
    L = float(length_mm)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" class="{css_class}" '
        f'viewBox="-5 -5 {L + 10:.1f} {w + 10:.1f}" width="100%" '
        'preserveAspectRatio="xMidYMid meet">',]
    if summary:
        blob = _json.dumps(summary, ensure_ascii=False, sort_keys=True)
        blob = blob.replace('&', '&amp;').replace('<', '&lt;')
        desc = _xesc('Production Layout Summary - '
                f"{summary.get('product_code', '')} layout "
                f"#{summary.get('layout_id', '')}: width "
                f"{summary.get('width_mm', '')} mm, length "
                f"{summary.get('length_mm', '')} mm, utilization "
                f"{summary.get('utilization_pct', '')}%, ratio "
                f"{summary.get('ratio', '')}")
        parts.append(f'<desc>{desc}</desc>')
        parts.append('<metadata id="production-layout-summary">'
                     f'{blob}</metadata>')
    parts += [
        f'<rect x="0" y="0" width="{L:.1f}" height="{w:.1f}" fill="#fbf8f0" '
        'stroke="#b7a87f" stroke-width="1" vector-effect="non-scaling-stroke"/>',
    ]
    palette = ['#e8d9b8', '#d9e4d0', '#d7dceb', '#ecd9d5', '#e4d5ec', '#d5ecea']
    color_of = {}
    for p in placements:
        c = color_of.setdefault(p['key'], palette[len(color_of) % len(palette)])
        pts = ' '.join(f'{x:.2f},{w - y:.2f}' for x, y in p['polygon_mm'])
        parts.append(f'<polygon points="{pts}" fill="{c}" stroke="#6d5a33" '
                     'stroke-width="0.8" vector-effect="non-scaling-stroke">'
                     f'<title>{_xesc(p["key"])} #{p["instance"] + 1}'
                     f'{" (mirrored)" if p.get("mirrored") else ""} '
                     f'rot {p.get("rotation_deg", 0)}&#176;</title></polygon>')
    parts.append('</svg>')
    return '\n'.join(parts)


def marker_tile_svg(placements, width_mm, length_mm, u0, v0,
                    win_w, win_h, css_class='tile-svg'):
    """M8 print tiles (READ-ONLY, pure strings): one TRUE-SCALE window
    over the marker plane. Mapping matches the PDF exactly so tile
    numbering agrees: u = width coord (page x), v = length coord
    (page y, flowing down)."""
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" class="{css_class}" '
        f'viewBox="{u0:.1f} {v0:.1f} {win_w:.1f} {win_h:.1f}" '
        f'width="{win_w}mm" height="{win_h}mm" '
        'preserveAspectRatio="xMinYMin meet">',
        # fabric boundary in the (u, v) frame
        f'<rect x="0" y="0" width="{float(width_mm):.1f}" '
        f'height="{float(length_mm):.1f}" fill="none" '
        'stroke="#b7a87f" stroke-width="0.9"/>',
    ]
    for p in placements:
        pts = ' '.join(f'{y:.2f},{x:.2f}' for x, y in p['polygon_mm'])
        parts.append(f'<polygon points="{pts}" fill="none" '
                     'stroke="#4d3f22" stroke-width="0.6"/>')
        ring = p['polygon_mm']
        cu = sum(pt[1] for pt in ring) / len(ring)
        cv = sum(pt[0] for pt in ring) / len(ring)
        parts.append(f'<text x="{cu:.1f}" y="{cv:.1f}" font-size="4" '
                     'text-anchor="middle" fill="#4d3f22">'
                     f'{_xesc(p.get("key", ""))} '
                     f'#{int(p.get("instance", 0)) + 1}</text>')
    # dashed overlap match lines (10 mm overlap; step = window − overlap)
    su, sv = u0 + (win_w - 10.0), v0 + (win_h - 10.0)
    parts.append(f'<line x1="{su:.1f}" y1="{v0:.1f}" x2="{su:.1f}" '
                 f'y2="{v0 + win_h:.1f}" stroke="#a5702a" '
                 'stroke-width="0.5" stroke-dasharray="6 4"/>')
    parts.append(f'<line x1="{u0:.1f}" y1="{sv:.1f}" x2="{u0 + win_w:.1f}" '
                 f'y2="{sv:.1f}" stroke="#a5702a" stroke-width="0.5" '
                 'stroke-dasharray="6 4"/>')
    parts.append('</svg>')
    return '\n'.join(parts)


def outline_preview_svg(outline_mm, css_class='design-preview'):
    """PDM W2 (READ-ONLY, pure strings): mini shape preview of ONE
    Design Row's outline_mm — the reusable atom's visual. Fill+outline
    only; y-flip here (canonical y-up -> svg y-down), 4% padding."""
    if not outline_mm:
        return ''
    xs = [p[0] for p in outline_mm]; ys = [p[1] for p in outline_mm]
    w = max(xs) - min(xs) or 1.0
    h = max(ys) - min(ys) or 1.0
    pad = 0.04 * max(w, h)
    pts = ' '.join(f'{x - min(xs):.1f},{max(ys) - y:.1f}'
                   for x, y in outline_mm)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'class="{css_class}" viewBox="{-pad:.1f} {-pad:.1f} '
            f'{w + 2 * pad:.1f} {h + 2 * pad:.1f}" '
            'preserveAspectRatio="xMidYMid meet">'
            f'<polygon points="{pts}" fill="#efe6d2" stroke="#6d5a33" '
            'stroke-width="1.5" vector-effect="non-scaling-stroke"/></svg>')
