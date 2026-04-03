# Signals have been intentionally removed from this project.
#
# All stock ledger entries are now created EXPLICITLY inside service methods
# (inventory/services/) using @transaction.atomic — not via post_save signals.
#
# Why:
#   - Signals fire outside the caller's transaction, risking orphaned ledger entries.
#   - Signal execution order is undefined; multiple signals on the same model can race.
#   - Explicit service calls are easier to read, test, and trace in logs.
#
# If you need to add a new ledger-triggering operation, add it to the appropriate
# service in inventory/services/ and call StockService.log() directly.
