"""Payment terms CLI toolkit.

Exposes the high-level ``run_payment_terms`` API for programmatic use.
"""

from .runner import run_chart_of_accounts  # Public API for synchronisation

__all__ = ["run_chart_of_accounts"]  # Re-exported symbol