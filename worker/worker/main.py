"""arq worker: one job per uploaded PDF.

Phase 4 replaces process_agreement's body with the LangGraph ingestion
graph (parse -> extract -> validate -> retry -> save).
"""

import os

from arq.connections import RedisSettings

from contract_core import SCHEMA_VERSION


async def process_agreement(ctx: dict, agreement_id: str) -> dict:
    return {"agreement_id": agreement_id, "schema_version": SCHEMA_VERSION, "status": "stub"}


class WorkerSettings:
    functions = [process_agreement]
    redis_settings = RedisSettings.from_dsn(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
