"""Pydantic request/response schemas for the events API."""

from datetime import datetime

from pydantic import BaseModel, Field


class EmitRequest(BaseModel):
    """Request body for POST /events."""

    event_name: str
    metadata: dict = Field(default_factory=dict)


class EmitResponse(BaseModel):
    """Response body for POST /events."""

    published: bool
    message_id: str


class DataPoint(BaseModel):
    """A single time-bucketed event count."""

    time_bucket: datetime
    event_name: str
    count: int


class EventDataResponse(BaseModel):
    """Response body for GET /events."""

    event_name: str | None
    since: datetime
    bucket: str
    data: list[DataPoint]
