"""compute/patterns_ai runtime — isolated CV/geometry engine (ADR-F).

NEVER imported by Django. Django's pattern_geometry_service invokes the
CLI scripts (calibrate.py / extract.py / dxf_io.py / synth.py) via
subprocess with JSON-file I/O. No sockets, no network, no Django.
"""
PIPELINE_VERSION = 'p2.1'
