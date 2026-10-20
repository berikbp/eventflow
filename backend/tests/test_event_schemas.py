from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.schemas.event import EventCreate, EventUpdate


def payload():
    return {
        "title": "  Meetup  ",
        "description": "  Description  ",
        "starts_at": (datetime.now(UTC) + timedelta(days=3)).isoformat(),
        "capacity": 5,
    }


def test_normalizes_text_and_timezone():
    data = payload() | {"starts_at": "2099-01-01T17:00:00+05:00"}
    event = EventCreate(**data)
    assert event.title == "Meetup"
    assert event.description == "Description"
    assert event.starts_at == datetime(2099, 1, 1, 12, tzinfo=UTC)


@pytest.mark.parametrize(
    "changes",
    [
        {"title": " "},
        {"title": "a" * 201},
        {"description": "a" * 10001},
        {"capacity": 0},
        {"capacity": -1},
        {"capacity": True},
        {"capacity": 1.5},
        {"capacity": "5"},
        {"capacity": 1000001},
        {"starts_at": "2099-01-01T12:00:00"},
        {"starts_at": "2020-01-01T12:00:00Z"},
        {"unknown": "field"},
    ],
)
def test_rejects_invalid_create(changes):
    with pytest.raises(ValidationError):
        EventCreate(**(payload() | changes))


@pytest.mark.parametrize(
    "changes", [{}, {"title": None}, {"starts_at": None}, {"capacity": 0}]
)
def test_rejects_empty_or_null_update(changes):
    with pytest.raises(ValidationError):
        EventUpdate(**changes)


def test_update_preserves_omitted_fields():
    assert EventUpdate(title="New").model_dump(exclude_unset=True) == {"title": "New"}
