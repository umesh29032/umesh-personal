#!/usr/bin/env python
"""calibrate.py — commissioning / recheck evidence for a CalibrationMat.

Protocol: calibrate.py --in job.json --out result.json
job: {"image_path", "board_spec", "control_distances"?}
result: {"ok", "metrics", "checks", "gate", "provenance"} — the mat check
row is written Django-side by calibration_service from this evidence.
"""
import argparse
import json
import sys

import cv2

from runtime import PIPELINE_VERSION
from runtime.detect import detect_and_fit, run_gate, self_check


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='inp', required=True)
    ap.add_argument('--out', dest='out', required=True)
    args = ap.parse_args()
    job = json.load(open(args.inp))

    img = cv2.imread(job['image_path'], cv2.IMREAD_GRAYSCALE)
    if img is None:
        json.dump({'ok': False,
                   'error': f"unreadable image {job['image_path']}"},
                  open(args.out, 'w'))
        return 0
    metrics, H = detect_and_fit(img, job['board_spec'])
    checks = (self_check(metrics, job['board_spec'],
                         job.get('control_distances'))
              if H is not None else [])
    json.dump({'ok': True, 'metrics': metrics, 'checks': checks,
               'gate': run_gate(metrics, checks),
               'provenance': {'pipeline_version': PIPELINE_VERSION}},
              open(args.out, 'w'), indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main())
