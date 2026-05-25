from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class LiftBankInput:
    bank_name: str
    building_type: str
    building_grade: str
    floors_served: int
    total_travel_height_m: float
    population_served: int
    population_per_floor: int
    number_of_lifts: int
    car_capacity_persons: int
    rated_speed_mps: float
    floor_height_m: float
    door_type: str
    door_clear_width_mm: int
    door_time_s: float
    passenger_transfer_time_s: float
    acceleration_mps2: float
    jerk_mps3: float
    main_terminal_floor: int = 0
    sky_lobby_floor: int = 0
    amenity_floor_numbers: str = ""
    zoning_strategy: str = "Single Zone"
    passenger_lift_pit_depth_m: float = 2.0
    passenger_lift_overhead_m: float = 4.5
    service_lift_pit_depth_m: float = 2.2
    service_lift_overhead_m: float = 4.8
    fireman_lift_pit_depth_m: float = 3.5
    fireman_lift_overhead_m: float = 5.0
    fireman_lift_car_width_mm: int = 1400
    fireman_lift_car_depth_mm: int = 2200
    fireman_lift_door_clear_mm: int = 1100


BUILDING_TYPES = ["Office", "Residential", "Hotel", "Hospital", "Mixed"]
BUILDING_GRADES = [
    "Prestige / Corporate Office",
    "Mainstream / Speculative Office",
    "Luxury Residential",
    "Standard Residential",
    "Hotel 4-5 Star",
    "Hospital",
    "Mixed Use",
]
DOOR_TYPES = ["Center Opening", "Side Opening", "Telescopic", "Other"]
ZONING_OPTIONS = [
    "Single Zone",
    "Low / High Rise Split",
    "Express / Sky Lobby",
    "Separate Service Zone",
    "Mixed-Use Separated Banks",
]


TRAFFIC_PROFILES = {
    "Office Morning Up-Peak": {
        "incoming": 0.85,
        "outgoing": 0.10,
        "interfloor": 0.05,
        "applicable_to": "Office",
    },
    "Office Lunch / Two-Way": {
        "incoming": 0.40,
        "outgoing": 0.40,
        "interfloor": 0.20,
        "applicable_to": "Office",
    },
    "Residential Morning Down-Peak": {
        "incoming": 0.20,
        "outgoing": 0.65,
        "interfloor": 0.15,
        "applicable_to": "Residential",
    },
    "Residential Evening Up-Peak": {
        "incoming": 0.60,
        "outgoing": 0.20,
        "interfloor": 0.20,
        "applicable_to": "Residential",
    },
    "Hotel Two-Way Guest Movement": {
        "incoming": 0.45,
        "outgoing": 0.35,
        "interfloor": 0.20,
        "applicable_to": "Hotel",
    },
    "Mixed-Use Balanced": {
        "incoming": 0.45,
        "outgoing": 0.35,
        "interfloor": 0.20,
        "applicable_to": "Mixed",
    },
}


def clone_bank(bank: LiftBankInput, **changes) -> LiftBankInput:
    data = bank.__dict__.copy()
    data.update(changes)
    return LiftBankInput(**data)


def floor_labels_from_count(floors_served: int) -> List[int]:
    return list(range(max(1, floors_served)))