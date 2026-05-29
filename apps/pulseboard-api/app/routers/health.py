"""Health check endpoint.

GET /health returns {"status": "ok", "db": "ok"} when healthy.
If the DB is unreachable, db becomes "error" and status becomes "degraded".
Used by Kubernetes liveness and readiness probes.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db

router = APIRouter()


@router.get("/health")
def health(db: Session = Depends(get_db)) -> JSONResponse:  # noqa: B008
    """Return service health including database connectivity status.

    Returns:
        A JSONResponse with keys ``status`` (ok or degraded) and ``db`` (ok or error).
        Returns HTTP 200 when healthy, HTTP 503 when the DB is unreachable.
    """
    try:
        db.execute(text("SELECT 1"))
        return JSONResponse(content={"status": "ok", "db": "ok"})
    except Exception:
        return JSONResponse(status_code=503, content={"status": "degraded", "db": "error"})
