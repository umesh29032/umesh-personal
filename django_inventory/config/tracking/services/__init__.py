from .barcode_service import (
    get_or_create_piece, mark_status, parse_value, qr_data_uri, resolve_value,
)
from .history_service import log_roll, log_adda, log_product

# P4.2: generate_for_cutting/generate_from_breakdown moved to
# production.stages.barcode_generation.assembly (assembly = production concern).
__all__ = [
    'qr_data_uri', 'mark_status',
    'parse_value', 'resolve_value', 'get_or_create_piece',
    'log_roll', 'log_adda', 'log_product',
]
# P4.2: barcode export service moved to
# production.stages.barcode_generation.export_service (stage-gated manifest).
