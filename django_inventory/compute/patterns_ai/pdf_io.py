"""pdf_io — M8 pure-python PDF writer (ZERO new dependencies, plan-locked).

A PRODUCTION DOCUMENT (owner refinement 6): page 1 = the Production
Layout Summary; remaining pages = the tiled TRUE-SCALE marker (A4
portrait, numbered tiles, 10 mm overlap with dashed match lines, corner
ticks, a 100 mm scale bar on every tile so the printer's honesty is
checkable).

job:  {summary: {..str/num pairs rendered on page 1..},
       width_mm, length_mm,
       placements: [{key, instance, polygon_mm:[[x,y],..]}]}
       # marker frame: x = length direction, y = width direction (mm)
result: {ok, pdf_b64, pages, cols, rows}

Uncompressed content streams on purpose — byte-greppable in tests.
"""
import argparse
import base64
import json
import math

K = 72.0 / 25.4                 # 1 mm in PDF points (true scale)
PAGE_W, PAGE_H = 595.2756, 841.8898          # A4 portrait, points
MARGIN_MM = 10.0
WIN_W_MM, WIN_H_MM = 190.0, 277.0            # printable window per tile
OVERLAP_MM = 10.0
STEP_W_MM = WIN_W_MM - OVERLAP_MM            # 180 — tile advance across width
STEP_H_MM = WIN_H_MM - OVERLAP_MM            # 267 — tile advance along length


def _esc(s):
    return str(s).replace('\\', r'\\').replace('(', r'\(').replace(')', r'\)')


def _text(x_pt, y_pt, size, s, bold=False):
    font = '/F2' if bold else '/F1'
    return f'BT {font} {size} Tf 1 0 0 1 {x_pt:.2f} {y_pt:.2f} Tm ({_esc(s)}) Tj ET\n'


def _mm(v):
    return v * K


def _summary_page(summary):
    """Page 1 — the Production Layout Summary + assembly instructions."""
    c = []
    y = PAGE_H - _mm(22)
    c.append(_text(_mm(15), y, 18, 'Production Layout Summary', bold=True))
    y -= _mm(8)
    c.append(_text(_mm(15), y, 11,
                   f"{summary.get('product_name', '')} "
                   f"({summary.get('product_code', '')}) · "
                   f"Layout #{summary.get('layout_id', '')}"))
    y -= _mm(12)
    rows = [
        ('Fabric width', f"{summary.get('width_mm')} mm"),
        ('Required layer length', f"{summary.get('length_mm')} mm"),
        ('Utilization / waste',
         f"{summary.get('utilization_pct')}% / {summary.get('waste_pct')}%"
         ' (derived at read)'),
        ('Pattern count',
         f"{summary.get('piece_count')} pieces · "
         f"{summary.get('garments')} garment(s)"),
        ('Size ratio', summary.get('ratio', '')),
        ('Verified', 'yes — independently verified'
         if summary.get('verified') else 'NO — not verified'),
        ('Production layout',
         ('YES - approved by '
          f"{summary.get('approved_by', '')} at {summary.get('approved_at', '')}")
         if summary.get('production') else 'no (draft layout)'),
        ('Exported', f"{summary.get('generated_at', '')} by "
                     f"{summary.get('generated_by', '')}"),
        ('Tiles', f"{summary.get('cols')} column(s) x "
                  f"{summary.get('rows')} row(s) - "
                  f"{summary.get('cols') * summary.get('rows')} tile page(s)"),
    ]
    for label, value in rows:
        c.append(_text(_mm(15), y, 9, label.upper()))
        c.append(_text(_mm(75), y, 11, value, bold=True))
        y -= _mm(9)
    y -= _mm(6)
    c.append(_text(_mm(15), y, 11, 'ASSEMBLY', bold=True))
    y -= _mm(7)
    for line in (
            'Print at 100% scale - never "fit to page".',
            'Check the 100 mm scale bar on any tile with a tape.',
            'Assemble columns left-to-right (C1, C2, ...), rows '
            'top-to-bottom (R1, R2, ...).',
            'Overlap tiles to the dashed match lines (10 mm overlap).',
            'This document is derived from the immutable saved layout - '
            'regenerate the export after any new approval.'):
        c.append(_text(_mm(15), y, 10, '- ' + line))
        y -= _mm(6.5)
    return ''.join(c)


def _tile_page(placements, width_mm, length_mm, col, row, cols, rows,
               summary):
    """One TRUE-SCALE tile: window (col,row) over the marker plane.
    Marker frame -> page: u = width coord (page x), v = length coord
    (page y, flowing DOWN the page)."""
    u0 = col * STEP_W_MM
    v0 = row * STEP_H_MM
    m = _mm(MARGIN_MM)
    c = []

    def px(u):
        return m + _mm(u - u0)

    def py(v):
        return PAGE_H - m - _mm(v - v0)

    # header + footer OUTSIDE the clip
    c.append(_text(m, PAGE_H - _mm(7), 9,
                   f"Layout #{summary.get('layout_id')} · tile "
                   f"C{col + 1}-R{row + 1} (col {col + 1}/{cols}, "
                   f"row {row + 1}/{rows}) · TRUE SCALE - print at 100%",
                   bold=True))
    # 100 mm scale bar in the footer strip
    bar_y = _mm(5.5)
    c.append(f'1.2 w 0 0 0 RG {m:.2f} {bar_y:.2f} m '
             f'{m + _mm(100):.2f} {bar_y:.2f} l S\n')
    for t in (0, 50, 100):
        c.append(f'0.8 w {m + _mm(t):.2f} {bar_y - 3:.2f} m '
                 f'{m + _mm(t):.2f} {bar_y + 3:.2f} l S\n')
    c.append(_text(m + _mm(102), bar_y - 2, 8, '100 mm scale bar'))

    # clip to the tile window
    c.append(f'q {m:.2f} {PAGE_H - m - _mm(WIN_H_MM):.2f} '
             f'{_mm(WIN_W_MM):.2f} {_mm(WIN_H_MM):.2f} re W n\n')
    # fabric boundary
    c.append(f'0.9 w 0.45 0.38 0.22 RG {px(0):.2f} {py(0):.2f} m '
             f'{px(width_mm):.2f} {py(0):.2f} l '
             f'{px(width_mm):.2f} {py(length_mm):.2f} l '
             f'{px(0):.2f} {py(length_mm):.2f} l h S\n')
    # pieces: outline + centroid label
    for p in placements:
        ring = p['polygon_mm']
        # marker (x=length, y=width) -> (u=y, v=x)
        path = []
        for i, (x, y) in enumerate(ring):
            u, v = y, x
            path.append(f'{px(u):.2f} {py(v):.2f} '
                        + ('m' if i == 0 else 'l'))
        c.append('0.6 w 0.20 0.16 0.08 RG '
                 + ' '.join(path) + ' h S\n')
        cx = sum(pt[1] for pt in ring) / len(ring)
        cy = sum(pt[0] for pt in ring) / len(ring)
        c.append(_text(px(cx) - 12, py(cy) - 3, 6,
                       f"{p.get('key', '')} #{int(p.get('instance', 0)) + 1}"))
    # dashed overlap match lines at the step boundary
    c.append('[6 4] 0 d 0.6 w 0.55 0.35 0.10 RG\n')
    c.append(f'{px(u0 + STEP_W_MM):.2f} {py(v0):.2f} m '
             f'{px(u0 + STEP_W_MM):.2f} {py(v0 + WIN_H_MM):.2f} l S\n')
    c.append(f'{px(u0):.2f} {py(v0 + STEP_H_MM):.2f} m '
             f'{px(u0 + WIN_W_MM):.2f} {py(v0 + STEP_H_MM):.2f} l S\n')
    c.append('[] 0 d\n')
    c.append('Q\n')
    # corner ticks (trim guides) at the window corners
    c.append('0.5 w 0 0 0 RG\n')
    for tx in (m, m + _mm(WIN_W_MM)):
        for ty in (PAGE_H - m, PAGE_H - m - _mm(WIN_H_MM)):
            c.append(f'{tx - 6:.2f} {ty:.2f} m {tx + 6:.2f} {ty:.2f} l S\n')
            c.append(f'{tx:.2f} {ty - 6:.2f} m {tx:.2f} {ty + 6:.2f} l S\n')
    return ''.join(c)


def build_pdf(job):
    placements = job['placements']
    width_mm = float(job['width_mm'])
    length_mm = float(job['length_mm'])
    cols = max(1, math.ceil(width_mm / STEP_W_MM))
    rows = max(1, math.ceil(length_mm / STEP_H_MM))
    summary = dict(job.get('summary') or {})
    summary.setdefault('width_mm', width_mm)
    summary.setdefault('length_mm', length_mm)
    summary['cols'], summary['rows'] = cols, rows

    streams = [_summary_page(summary)]
    for row in range(rows):
        for col in range(cols):
            streams.append(_tile_page(placements, width_mm, length_mm,
                                      col, row, cols, rows, summary))

    # ---- assemble the PDF (objects -> xref -> trailer) ----
    objects = []                                     # 1-indexed bodies
    page_ids = []
    font1 = len(objects) + 1
    objects.append('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica '
                   '/Encoding /WinAnsiEncoding >>')
    font2 = len(objects) + 1
    objects.append('<< /Type /Font /Subtype /Type1 '
                   '/BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>')
    pages_id_placeholder = None
    content_ids = []
    for s in streams:
        data = s.encode('cp1252', 'replace')
        content_ids.append(len(objects) + 1)
        objects.append(f'<< /Length {len(data)} >>\nstream\n'
                       + data.decode('cp1252') + '\nendstream')
    pages_id = len(objects) + 1 + len(streams)       # after page objs
    for cid in content_ids:
        page_ids.append(len(objects) + 1)
        objects.append(
            f'<< /Type /Page /Parent {pages_id} 0 R '
            f'/MediaBox [0 0 {PAGE_W:.4f} {PAGE_H:.4f}] '
            f'/Resources << /Font << /F1 {font1} 0 R /F2 {font2} 0 R >> >> '
            f'/Contents {cid} 0 R >>')
    assert len(objects) + 1 == pages_id
    kids = ' '.join(f'{pid} 0 R' for pid in page_ids)
    objects.append(f'<< /Type /Pages /Kids [{kids}] '
                   f'/Count {len(page_ids)} >>')
    catalog_id = len(objects) + 1
    objects.append(f'<< /Type /Catalog /Pages {pages_id} 0 R >>')

    out = ['%PDF-1.4\n']
    offsets = [0]
    pos = len(out[0].encode('cp1252'))
    for i, body in enumerate(objects, start=1):
        offsets.append(pos)
        chunk = f'{i} 0 obj\n{body}\nendobj\n'
        out.append(chunk)
        pos += len(chunk.encode('cp1252'))
    xref_pos = pos
    n = len(objects) + 1
    xref = [f'xref\n0 {n}\n', '0000000000 65535 f \n']
    for off in offsets[1:]:
        xref.append(f'{off:010d} 00000 n \n')
    out.append(''.join(xref))
    out.append(f'trailer\n<< /Size {n} /Root {catalog_id} 0 R >>\n'
               f'startxref\n{xref_pos}\n%%EOF\n')
    return ''.join(out).encode('cp1252', 'replace'), len(streams), cols, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='inp', required=True)
    ap.add_argument('--out', dest='out', required=True)
    args = ap.parse_args()
    job = json.load(open(args.inp))
    try:
        pdf, pages, cols, rows = build_pdf(job)
    except Exception as exc:                        # honest failure
        json.dump({'ok': False, 'error': f'pdf build failed: {exc}'},
                  open(args.out, 'w'))
        return 0
    json.dump({'ok': True,
               'pdf_b64': base64.b64encode(pdf).decode('ascii'),
               'pages': pages, 'cols': cols, 'rows': rows},
              open(args.out, 'w'))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
