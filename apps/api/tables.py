"""Every database table known to the application.

The composition root is the only layer allowed to know all services, so the
complete metadata is assembled here. Alembic (``migrations/env.py``) and tests
import ``metadata`` from this module. Add new table modules to the imports.
"""

from __future__ import annotations

from libs.storage import audit as _audit
from libs.storage.base import Base
from services.market_data import tables as _market_data_tables

TABLE_MODULES = (_audit, _market_data_tables)

metadata = Base.metadata
