"""Schedule Agent: parses load-shedding slots and returns blackout and free hours."""
import re

from .models import BlackoutSlot

_SLOT_RE = re.compile(r"^(\d{1,2})(?::\d{2})?\s*-\s*(\d{1,2})(?::\d{2})?$")


def parse_slots(text: str) -> list[BlackoutSlot]:
    """
    "14:00-16:00, 22:00-23:00" -> [BlackoutSlot(14, 16), BlackoutSlot(22, 23)]
    Note: granularity is one hour (minutes are ignored).
    """
    slots = []
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        match = _SLOT_RE.match(part)
        if not match:
            raise ValueError(f"Invalid format: '{part}'. Example: 14:00-16:00")
        start, end = int(match.group(1)), int(match.group(2))
        if not (0 <= start < end <= 24):
            raise ValueError(f"Invalid time range: '{part}'")
        slots.append(BlackoutSlot(start, end))
    return slots


def blackout_hours(slots: list[BlackoutSlot]) -> set[int]:
    hours: set[int] = set()
    for slot in slots:
        hours.update(range(slot.start, slot.end))
    return hours


def free_hours(slots: list[BlackoutSlot]) -> list[int]:
    blackout = blackout_hours(slots)
    return [h for h in range(24) if h not in blackout]