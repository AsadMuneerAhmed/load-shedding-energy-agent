"""Data models shared by all agents."""
from dataclasses import dataclass

PRIORITIES = ("high", "medium", "low")
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


@dataclass
class BlackoutSlot:
    """One load-shedding window. start and end are hours (0-24), end is exclusive."""
    start: int
    end: int


@dataclass
class Appliance:
    name: str
    watts: float
    hours_per_day: float
    priority: str = "medium"
    shiftable: bool = True  # True = can run at any free time

    def __post_init__(self):
        if self.priority not in PRIORITIES:
            raise ValueError(f"Priority must be one of: {PRIORITIES}")
        if self.watts < 0 or self.hours_per_day < 0:
            raise ValueError(f"{self.name}: watts and hours cannot be negative")
        if self.hours_per_day > 24:
            raise ValueError(f"{self.name}: hours per day cannot exceed 24")


@dataclass
class Battery:
    capacity_wh: float
    charge_percent: float
    max_charge_w: float = 500.0
    efficiency: float = 0.85

    def __post_init__(self):
        if not 0 <= self.charge_percent <= 100:
            raise ValueError("charge_percent must be between 0 and 100")
        if self.capacity_wh <= 0 or self.max_charge_w <= 0:
            raise ValueError("Battery capacity and charging power must be greater than zero")
        if not 0 < self.efficiency <= 1:
            raise ValueError("Efficiency must be between 0 and 1")

    @property
    def stored_wh(self) -> float:
        return self.capacity_wh * self.charge_percent / 100

    @property
    def usable_wh(self) -> float:
        return self.stored_wh * self.efficiency