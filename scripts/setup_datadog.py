from __future__ import annotations

#!/usr/bin/env python3
"""One-shot script to create Datadog dashboard and monitors for ShieldOps."""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Config
from src.observability.dashboard import DashboardBuilder
from src.observability.monitors import MonitorBuilder


async def main():
    config = Config.from_env()

    if not config.datadog.api_key or not config.datadog.app_key:
        print("❌ DD_API_KEY and DD_APP_KEY must be set")
        sys.exit(1)

    print("🛡️ ShieldOps — Datadog Setup")
    print("=" * 40)

    # Create dashboard
    print("\n📊 Creating dashboard...")
    db = DashboardBuilder(config.datadog)
    url = await db.create_or_update()
    if url:
        print(f"   ✅ Dashboard: {url}")
    else:
        print("   ❌ Dashboard creation failed")

    # Create monitors
    print("\n🚨 Creating monitors...")
    mb = MonitorBuilder(config.datadog)
    monitors = await mb.create_all()
    for m in monitors:
        print(f"   ✅ {m['name']} (ID: {m['id']})")

    print(f"\n✅ Setup complete: 1 dashboard, {len(monitors)} monitors")


if __name__ == "__main__":
    asyncio.run(main())
