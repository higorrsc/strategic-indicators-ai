"""CLI entrypoint for seeding realistic enterprise financial data."""

from __future__ import annotations

import asyncio

from scripts.seed.runner import main
from scripts.seed.seeder import seed_data

__all__ = ["main", "seed_data"]

if __name__ == "__main__":
    asyncio.run(main())
