"""patterns_ai models — Digital Memory (Blocks 2A-3E) + Geometry era (P2).

Constitution reminders (V3 §5): every row here is KNOWLEDGE — append-only,
superseded/retired/rejected with reasons, never edited-in-place or deleted
(service-enforced; schema carries the states + constraints). All FKs point
INTO production (string refs). JSON payloads carry a schema_version KEY
inside the payload (F3 convention).
"""
from .capture import CaptureAsset
from .events import MarkerTransitionEvent
from .generation import GeneratedMarkerCandidate, MarkerGenerationRun
from .geometry import (EvidenceItem, GeometryExtraction, PatternSetLabel,
                       PieceSizeGeometry)
from .mats import CalibrationMat, CalibrationMatCheck
from .pieces import PatternPiece, PatternPieceVersion
from .layouts import ApprovedLayout, ApprovedLayoutUsage
from .profile import ProductFabricProfile, ProductionLayout
from .markers import Marker, MarkerOutcome, MarkerUsage
from .strategy import ManufacturingStrategy
from .suggestions import SuggestionEvent

__all__ = [
    'CalibrationMat', 'CalibrationMatCheck', 'CaptureAsset',
    'PatternPiece', 'PatternPieceVersion', 'PieceSizeGeometry',
    'GeometryExtraction', 'PatternSetLabel', 'EvidenceItem',
    'MarkerGenerationRun', 'GeneratedMarkerCandidate',
    'ProductFabricProfile', 'ProductionLayout',
    'Marker', 'MarkerUsage', 'MarkerOutcome', 'MarkerTransitionEvent',
    'SuggestionEvent',
    'ApprovedLayout', 'ApprovedLayoutUsage', 'ManufacturingStrategy',
]
