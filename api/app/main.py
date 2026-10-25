import psycopg
import redis
from fastapi import FastAPI
from qdrant_client import QdrantClient

from contract_core import SCHEMA_VERSION, Agreement

from app.config import settings

app = FastAPI(title="Agreement Intelligence API", version="0.1.0")


def _check(fn) -> str:
    try:
        fn()
        return "ok"
    except Exception as e:  # health endpoint reports, never raises
        return f"error: {e.__class__.__name__}"


@app.get("/health")
def health() -> dict:
    return {
        "postgres": _check(lambda: psycopg.connect(settings.database_url, connect_timeout=2).close()),
        "redis": _check(lambda: redis.Redis.from_url(settings.redis_url, socket_timeout=2).ping()),
        "qdrant": _check(lambda: QdrantClient(url=settings.qdrant_url, timeout=2).get_collections()),
    }


@app.get("/schema")
def schema() -> dict:
    """The extraction schema both paths share, handy for debugging prompts."""
    return {"schema_version": SCHEMA_VERSION, "json_schema": Agreement.model_json_schema()}
