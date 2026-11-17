"""Intentionally small support-ticket API used only by the QA test framework."""

import os
from itertools import count
from threading import Lock
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Response, status
from pydantic import BaseModel, Field, field_validator

app = FastAPI(title="QA Demo Ticket Service", version="1.0")
API_KEY = os.environ.get("DEMO_API_KEY", "local-demo-key")  # Local demo only; not production auth.
_lock = Lock()
_tickets: dict[int, dict] = {}
_id_gen = count(1)


class TicketCreate(BaseModel):
    title: str = Field(min_length=3, max_length=100)
    priority: Literal["low", "medium", "high"] = "medium"

    @field_validator("title")
    @classmethod
    def no_whitespace_only(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 3:
            raise ValueError("Title must contain at least 3 non-space characters")
        return value


class TicketRead(TicketCreate):
    id: int
    status: Literal["open"] = "open"


def authenticate(x_api_key: str | None = Header(default=None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/_test/reset", dependencies=[Depends(authenticate)])
def reset():
    """Only enabled for test-mode; never expose this endpoint in production."""
    global _id_gen
    if os.environ.get("DEMO_TEST_MODE") != "1":
        raise HTTPException(status_code=404, detail="Not available")
    with _lock:
        _tickets.clear()
        _id_gen = count(1)
    return {"status": "reset"}


@app.get("/tickets", dependencies=[Depends(authenticate)])
def list_tickets(
    priority: Literal["low", "medium", "high"] | None = None,
    limit: int = Query(default=20, ge=1, le=100),
):
    with _lock:
        items = [dict(t) for t in sorted(_tickets.values(), key=lambda t: t["id"])]
    if priority is not None:
        items = [ticket for ticket in items if ticket["priority"] == priority]
    return {"items": items[:limit], "count": len(items)}


@app.post("/tickets", response_model=TicketRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(authenticate)])
def create_ticket(payload: TicketCreate):
    with _lock:
        ticket_id = next(_id_gen)
        ticket = {"id": ticket_id, "title": payload.title, "priority": payload.priority, "status": "open"}
        _tickets[ticket_id] = ticket
        return dict(ticket)


@app.get("/tickets/{ticket_id}", response_model=TicketRead, dependencies=[Depends(authenticate)])
def read_ticket(ticket_id: int):
    with _lock:
        ticket = _tickets.get(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return dict(ticket)


@app.delete("/tickets/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(authenticate)])
def delete_ticket(ticket_id: int):
    with _lock:
        if _tickets.pop(ticket_id, None) is None:
            raise HTTPException(status_code=404, detail="Ticket not found")
    return Response(status_code=204)
