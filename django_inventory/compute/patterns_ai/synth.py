#!/usr/bin/env python
"""synth.py — deterministic synthetic golden captures (tests + drills).

Renders the spec'd ChArUco mat, optionally draws a known piece polygon
(mm coords, mid-grey like cardboard), applies a valid plane homography
(phone tilt) + blur/noise, writes a PNG + ground truth JSON.

Protocol: synth.py --in job.json --out result.json
job: {"board_spec", "out_image", "piece_polygon_mm"?, "tilt"?, "yaw"?,
      "noise"?, "blur"?, "px_per_mm"?}
"""
import argparse
import json
import sys

import cv2
import numpy as np

from runtime.board import board_size_mm, build_board


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='inp', required=True)
    ap.add_argument('--out', dest='out', required=True)
    args = ap.parse_args()
    job = json.load(open(args.inp))
    spec = job['board_spec']
    px_per_mm = float(job.get('px_per_mm', 2.0))
    mat_w, mat_h = board_size_mm(spec)
    w, h = int(mat_w * px_per_mm), int(mat_h * px_per_mm)

    board = build_board(spec)
    img = board.generateImage((w, h), marginSize=0)

    piece = job.get('piece_polygon_mm')
    if piece:
        pts = np.array([[x * px_per_mm, y * px_per_mm] for x, y in piece],
                       np.int32)
        cv2.fillPoly(img, [pts], 85)          # cardboard mid-grey

    tilt = float(job.get('tilt', 0)); yaw = float(job.get('yaw', 0))
    if tilt or yaw:
        src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
        dx, dy = w * yaw / 2, h * tilt / 2
        dst = np.float32([[dx, dy], [w - dx, dy * 0.6],
                          [w - dx * 0.3, h - dy * 0.2], [dx * 0.5, h]])
        H = cv2.getPerspectiveTransform(src, dst)
        img = cv2.warpPerspective(img, H, (w, h), borderValue=200)
    blur = int(job.get('blur', 0))
    if blur:
        img = cv2.GaussianBlur(img, (blur * 2 + 1, blur * 2 + 1), 0)
    noise = int(job.get('noise', 0))
    if noise:
        img = np.clip(img.astype(np.int16)
                      + np.random.default_rng(7).integers(
                          -noise, noise, img.shape),
                      0, 255).astype(np.uint8)

    cv2.imwrite(job['out_image'], img)
    gt = None
    if piece:
        xs = [p[0] for p in piece]; ys = [p[1] for p in piece]
        gt = {'polygon_mm': piece,
              'width_mm': max(xs) - min(xs), 'height_mm': max(ys) - min(ys)}
    json.dump({'ok': True, 'image_path': job['out_image'],
               'mat_mm': [mat_w, mat_h], 'ground_truth': gt},
              open(args.out, 'w'), indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main())
