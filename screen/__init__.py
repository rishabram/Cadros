"""NERON mass screener package.

See :mod:`screen.screener` for the harness and ``parcels_schema.md`` for the
parcel-input contract. Synthetic fixtures live in ``synthetic_parcels/``.
"""
from .screener import (CSV_COLUMNS, CSV_FILENAME, SUMMARY_FILENAME,
                       screen_manifest)

__all__ = ["CSV_COLUMNS", "CSV_FILENAME", "SUMMARY_FILENAME",
           "screen_manifest"]
