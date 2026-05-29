"""Health check endpoint.

GET /health returns {"status": "ok", "db": "ok"} when healthy.
If the DB is unreachable, db becomes "error" and status becomes "degraded".
Used by Kubernetes liveness and readiness probes.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db

router = APIRouter()


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict:  # noqa: B008
    """Return service health including database connectivity status.

    Returns:
        A dict with keys ``status`` (ok or degraded) and ``db`` (ok or error).
    """
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"

    overall = "ok" if db_status == "ok" else "degraded"
    return {"status": overall, "db": db_status}
