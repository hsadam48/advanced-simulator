from __future__ import annotations

import math
from typing import Dict

import pandas as pd

from core.benchmark_engine import benchmark_for
from core.kinematics import calculate_flight_time
from core.models import (
    LiftBankInput,
    TRAFFIC_PROFILES,
    ZONING_OPTIONS,
    clone_bank,
)


def scenario_is_applicable(building_type: str, scenario_name: str) -> bool:
    applicable = TRAFFIC_PROFILES[scenario_name]["applicable_to"]
    if building_type == "Mixed":
        return True
    if building_type == "Hospital":
        return scenario_name in ["Hotel Two-Way Guest Movement", "Mixed-Use Balanced"]
    return applicable == building_type or applicable == "Mixed"


def control_factor(control_method: str) -> tuple[float, float]:
    return {
        "Conventional": (1.00, 0.33),
        "Hybrid": (0.93, 0.30),
        "DCS": (0.88, 0.28),
    }.get(control_method, (1.00, 0.33))


def door_efficiency_factor(bank: LiftBankInput) -> float:
    factor = 1.0

    if bank.door_clear_width_mm < 900:
        factor += 0.10
    elif bank.door_clear_width_mm < 1000:
        factor += 0.05
    elif bank.door_clear_width_mm >= 1100:
        factor -= 0.03

    if bank.door_type == "Side Opening":
        factor += 0.04
    elif bank.door_type == "Telescopic":
        factor += 0.06

    return max(0.90, factor)


def zoning_efficiency_factor(bank: LiftBankInput) -> float:
    if bank.zoning_strategy == "Single Zone":
        if bank.floors_served > 50:
            return 1.08
        if bank.floors_served > 35:
            return 1.04
        return 1.00

    return {
        "Low / High Rise Split": 0.92,
        "Express / Sky Lobby": 0.88,
        "Mixed-Use Separated Banks": 0.90,
        "Separate Service Zone": 0.95,
    }.get(bank.zoning_strategy, 1.0)


def profile_pressure_factor(scenario_name: str) -> float:
    profile = TRAFFIC_PROFILES[scenario_name]
    if float(profile["incoming"]) >= 0.80 or float(profile["outgoing"]) >= 0.60:
        return 1.08
    if float(profile["interfloor"]) >= 0.20:
        return 1.12
    return 1.0


def run_traffic(bank: LiftBankInput, control_method: str, scenario_name: str) -> Dict[str, float | str]:
    passenger_load = max(2.0, bank.car_capacity_persons * 0.80)
    floors = max(1, bank.floors_served - 1)

    stops = floors * (1 - (1 - 1 / floors) ** passenger_load)
    highest_reversal = floors - sum((i / floors) ** passenger_load for i in range(1, floors))

    avg_floor_height = (
        bank.total_travel_height_m / max(1, bank.floors_served - 1)
        if bank.total_travel_height_m > 0 and bank.floors_served > 1
        else bank.floor_height_m
    )

    tf = calculate_flight_time(
        avg_floor_height,
        bank.rated_speed_mps,
        bank.acceleration_mps2,
        bank.jerk_mps3,
    )

    rtt_base = (
        2 * highest_reversal * tf
        + stops * bank.door_time_s * door_efficiency_factor(bank)
        + 2 * passenger_load * bank.passenger_transfer_time_s
    )

    rtt_base *= profile_pressure_factor(scenario_name) * zoning_efficiency_factor(bank)

    if bank.sky_lobby_floor > 0 and bank.zoning_strategy == "Express / Sky Lobby":
        rtt_base += calculate_flight_time(
            bank.sky_lobby_floor * avg_floor_height,
            bank.rated_speed_mps,
            bank.acceleration_mps2,
            bank.jerk_mps3,
        )

    if str(bank.amenity_floor_numbers).strip():
        rtt_base *= 1.04

    rtt_factor, awt_factor = control_factor(control_method)
    rtt = rtt_base * rtt_factor

    interval = rtt / max(1, bank.number_of_lifts)
    hc_pax = (300 * passenger_load * bank.number_of_lifts) / max(1.0, rtt)
    hc_pct = hc_pax / max(1, bank.population_served) * 100
    awt = interval * awt_factor

    avg_trip_distance = (bank.total_travel_height_m or (bank.floor_height_m * floors)) * 0.55
    trip_time = calculate_flight_time(
        avg_trip_distance,
        bank.rated_speed_mps,
        bank.acceleration_mps2,
        bank.jerk_mps3,
    )

    attd = awt + trip_time + bank.door_time_s + bank.passenger_transfer_time_s * passenger_load * 0.35

    return {
        "RTT (s)": round(rtt, 1),
        "Interval (s)": round(interval, 1),
        "AWT (s)": round(awt, 1),
        "ATTD (s)": round(attd, 1),
        "5HC (%)": round(hc_pct, 2),
        "5HC (pax)": round(hc_pax, 0),
        "Car Loading Used (%)": 80,
    }


def pass_fail(bank: LiftBankInput, result: Dict[str, float | str]) -> str:
    bm = benchmark_for(bank)
    return (
        "PASS"
        if float(result["AWT (s)"]) <= float(bm["awt_acceptable"])
        and float(result["5HC (%)"]) >= float(bm["hc_min"])
        and float(result["ATTD (s)"]) <= float(bm["attd_max"])
        else "FAIL"
    )


def performance_comment(bank: LiftBankInput, result: Dict[str, float | str]) -> str:
    bm = benchmark_for(bank)
    comments = []

    if float(result["AWT (s)"]) > float(bm["awt_acceptable"]):
        comments.append("AWT exceeds benchmark.")
    if float(result["5HC (%)"]) < float(bm["hc_min"]):
        comments.append("5-minute handling capacity is below benchmark.")
    if float(result["ATTD (s)"]) > float(bm["attd_max"]):
        comments.append("Average time to destination exceeds benchmark.")
    if bank.door_clear_width_mm < 1000:
        comments.append("Door clear width may restrict passenger flow.")
    if bank.floors_served > 35 and bank.zoning_strategy == "Single Zone":
        comments.append("Consider zoning or split banks for this number of floors.")

    return "Acceptable for preliminary review." if not comments else " ".join(comments)


def practical_system_by_building(bank: LiftBankInput) -> str:
    floors = bank.floors_served
    pop = bank.population_served
    btype = bank.building_type

    if btype == "Office":
        if floors <= 20 and pop <= 700:
            return "Conventional"
        if floors <= 35 and pop <= 1200:
            return "Hybrid"
        return "DCS"

    if btype == "Residential":
        if floors <= 25 and pop <= 800:
            return "Conventional"
        if floors <= 45 and pop <= 1500:
            return "Hybrid"
        return "DCS"

    if btype == "Hotel":
        return "Hybrid" if floors <= 20 and pop <= 700 else "DCS"

    if btype == "Hospital":
        return "DCS"

    if btype == "Mixed":
        return "Hybrid" if floors <= 25 and pop <= 900 else "DCS"

    return "Hybrid"


def solve_recommendation(bank: LiftBankInput, scenario_name: str) -> Dict[str, str | int | float]:
    recommended_system = practical_system_by_building(bank)
    current = run_traffic(bank, recommended_system, scenario_name)

    if pass_fail(bank, current) == "PASS":
        return {
            "Lift Bank": bank.bank_name,
            "Scenario": scenario_name,
            "Result": "PASS",
            "Recommendation": (
                f"Use {recommended_system}. Existing {bank.number_of_lifts} lifts, "
                f"{bank.car_capacity_persons} persons, {bank.rated_speed_mps} m/s are acceptable."
            ),
        }

    lift_options = range(bank.number_of_lifts, min(bank.number_of_lifts + 8, 16) + 1)
    capacity_options = sorted(set([bank.car_capacity_persons, 13, 16, 20, 21, 24, 26, 33, 40]))
    speed_options = sorted(set([bank.rated_speed_mps, 1.75, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0, 7.0, 8.0]))

    candidates = []

    for lifts in lift_options:
        for cap in capacity_options:
            if cap < bank.car_capacity_persons:
                continue
            for speed in speed_options:
                if speed < bank.rated_speed_mps:
                    continue
                for control in ["Conventional", "Hybrid", "DCS"]:
                    for zoning in ZONING_OPTIONS:
                        test_bank = clone_bank(
                            bank,
                            number_of_lifts=lifts,
                            car_capacity_persons=cap,
                            rated_speed_mps=speed,
                            zoning_strategy=zoning,
                        )
                        result = run_traffic(test_bank, control, scenario_name)
                        if pass_fail(test_bank, result) == "PASS":
                            score = (
                                (lifts - bank.number_of_lifts) * 100
                                + (cap - bank.car_capacity_persons) * 8
                                + (speed - bank.rated_speed_mps) * 15
                                + (0 if control == recommended_system else 12)
                                + (0 if zoning == bank.zoning_strategy else 20)
                            )
                            candidates.append((score, lifts, cap, speed, control, zoning))

    if not candidates:
        return {
            "Lift Bank": bank.bank_name,
            "Scenario": scenario_name,
            "Result": "FAIL",
            "Recommendation": (
                "Traffic not solved within practical search range. Use separate zoning/sectoring, "
                "split low/high-rise banks, or request specialist VT traffic study."
            ),
        }

    _, lifts, cap, speed, control, zoning = sorted(candidates, key=lambda x: x[0])[0]

    return {
        "Lift Bank": bank.bank_name,
        "Scenario": scenario_name,
        "Result": "FAIL",
        "Recommendation": f"Use {control}: {lifts} lifts, {cap} persons, {speed} m/s, zoning: {zoning}.",
    }


def build_analysis_rows(banks: list[LiftBankInput]) -> pd.DataFrame:
    rows = []
    for bank in banks:
        for scenario in TRAFFIC_PROFILES:
            if not scenario_is_applicable(bank.building_type, scenario):
                continue
            for control in ["Conventional", "Hybrid", "DCS"]:
                result = run_traffic(bank, control, scenario)
                bm = benchmark_for(bank)
                rows.append(
                    {
                        "Lift Bank": bank.bank_name,
                        "Building Type": bank.building_type,
                        "Grade": bank.building_grade,
                        "Scenario": scenario,
                        "Control": control,
                        **result,
                        "AWT Benchmark (s)": bm["awt_acceptable"],
                        "5HC Min Benchmark (%)": bm["hc_min"],
                        "ATTD Max Benchmark (s)": bm["attd_max"],
                        "Result": pass_fail(bank, result),
                        "Comment": performance_comment(bank, result),
                    }
                )

    return pd.DataFrame(rows)


def build_recommendation_rows(banks: list[LiftBankInput]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            solve_recommendation(bank, scenario)
            for bank in banks
            for scenario in TRAFFIC_PROFILES
            if scenario_is_applicable(bank.building_type, scenario)
        ]
    )


def build_benchmark_rows(banks: list[LiftBankInput]) -> pd.DataFrame:
    rows = []
    for bank in banks:
        bm = benchmark_for(bank)
        rows.append(
            {
                "Lift Bank": bank.bank_name,
                "Building Grade": bank.building_grade,
                "AWT Excellent (s)": bm["awt_excellent"],
                "AWT Acceptable (s)": bm["awt_acceptable"],
                "5HC Min (%)": bm["hc_min"],
                "5HC Target (%)": bm["hc_target"],
                "ATTD Ideal (s)": bm["attd_ideal"],
                "ATTD Max (s)": bm["attd_max"],
                "Car Loading Used": "80% of rated capacity",
                "Benchmark Basis": bm["source"],
            }
        )

    return pd.DataFrame(rows)