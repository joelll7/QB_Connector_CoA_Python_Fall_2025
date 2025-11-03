"""Chart of Accounts CLI toolkit.

Exposes the high-level ``run_account`` API for programmatic use.
"""

from .runner import run_accounts  # Public API for synchronisation

__all__ = ["run_accounts"]  # Re-exported symbol
