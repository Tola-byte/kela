from __future__ import annotations

from services.app_services import compounding_service


async def run_nightly_decay(user_id: str) -> int:
    return await compounding_service.decay_stale_entries(user_id)


async def run_weekly_connections(user_id: str) -> int:
    return await compounding_service.find_new_connections(user_id)


async def run_monthly_duplicates(user_id: str) -> list[tuple[str, str]]:
    return await compounding_service.merge_near_duplicates(user_id)
