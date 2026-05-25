from __future__ import annotations

import random
import statistics
from typing import Dict, Tuple

import pandas as pd

from core.kinematics import calculate_flight_time
from core.models import LiftBankInput


def run_advanced_simulation(
    bank: LiftBankInput,
    trials: int = 100,
    simulation_duration_sec: int = 4800,
    arrival_min_sec: float = 1.0,
    arrival_max_sec: float = 30.0,
    dispatch_wait_sec: float = 10.0,
    control_method: str = "Hybrid",
    seed: int = 42,
) -> Tuple[Dict[str, float | str], pd.DataFrame]:
    """
    Monte Carlo style up-peak simulation.

    This is intended as a practical engineering simulation layer:
    - Generates individual passengers.
    - Assigns random destinations.
    - Dispatches lifts based on availability and dispatch wait time.
    - Tracks waiting time, elevator time, total time, and max queue.
    """

    random.seed(seed)

    trials = int(trials)
    simulation_duration_sec = int(simulation_duration_sec)
    capacity = max(1, int(bank.car_capacity_persons))
    qty_lifts = max(1, int(bank.number_of_lifts))
    floors = max(2, int(bank.floors_served))

    avg_floor_height = (
        bank.total_travel_height_m / max(1, bank.floors_served - 1)
        if bank.total_travel_height_m > 0 and bank.floors_served > 1
        else bank.floor_height_m
    )

    transition_time = calculate_flight_time(
        avg_floor_height,
        bank.rated_speed_mps,
        bank.acceleration_mps2,
        bank.jerk_mps3,
    )

    control_stop_factor = {
        "Conventional": 1.00,
        "Hybrid": 0.90,
        "DCS": 0.65,
    }.get(control_method, 0.90)

    rows = []

    for trial in range(1, trials + 1):
        arrivals = []
        t = 0.0
        passenger_id = 0

        while t < simulation_duration_sec:
            t += random.uniform(arrival_min_sec, arrival_max_sec)
            if t > simulation_duration_sec:
                break
            passenger_id += 1
            destination_floor = random.randint(1, floors - 1)
            arrivals.append(
                {
                    "passenger_id": passenger_id,
                    "arrival_time": t,
                    "destination_floor": destination_floor,
                }
            )

        waiting_queue = list(arrivals)
        elevator_available = [0.0 for _ in range(qty_lifts)]
        waiting_times = []
        elevator_times = []
        total_times = []
        queue_sizes = []

        while waiting_queue:
            lift_idx = min(range(qty_lifts), key=lambda i: elevator_available[i])
            current_time = max(elevator_available[lift_idx], waiting_queue[0]["arrival_time"])

            dispatch_deadline = current_time + dispatch_wait_sec
            available = [p for p in waiting_queue if p["arrival_time"] <= current_time]

            while len(available) < capacity:
                future = [p for p in waiting_queue if p["arrival_time"] > current_time]
                if not future:
                    break
                if future[0]["arrival_time"] <= dispatch_deadline:
                    current_time = future[0]["arrival_time"]
                    available = [p for p in waiting_queue if p["arrival_time"] <= current_time]
                else:
                    current_time = dispatch_deadline
                    available = [p for p in waiting_queue if p["arrival_time"] <= current_time]
                    break

            load_count = min(capacity, len(available))
            trip_passengers = []
            remaining = []

            for p in waiting_queue:
                if p["arrival_time"] <= current_time and len(trip_passengers) < load_count:
                    trip_passengers.append(p)
                else:
                    remaining.append(p)

            waiting_queue = remaining
            queue_sizes.append(len(waiting_queue))

            if not trip_passengers:
                elevator_available[lift_idx] = current_time + 1
                continue

            highest_floor = max(p["destination_floor"] for p in trip_passengers)
            unique_stops = len(set(p["destination_floor"] for p in trip_passengers))
            unique_stops = max(1, int(unique_stops * control_stop_factor))

            loading_time = len(trip_passengers) * bank.passenger_transfer_time_s
            unloading_time = len(trip_passengers) * bank.passenger_transfer_time_s
            travel_time = 2 * highest_floor * transition_time
            door_time = unique_stops * bank.door_time_s

            trip_time = loading_time + unloading_time + travel_time + door_time
            elevator_available[lift_idx] = current_time + trip_time

            for p in trip_passengers:
                wait = current_time - p["arrival_time"]
                waiting_times.append(wait)
                elevator_times.append(trip_time)
                total_times.append(wait + trip_time)

        rows.append(
            {
                "Trial": trial,
                "Generated Passengers": len(arrivals),
                "Served Passengers": len(waiting_times),
                "Mean Waiting Time (s)": round(statistics.mean(waiting_times), 2) if waiting_times else 0,
                "Max Waiting Time (s)": round(max(waiting_times), 2) if waiting_times else 0,
                "Mean Elevator Time (s)": round(statistics.mean(elevator_times), 2) if elevator_times else 0,
                "Mean Total Time (s)": round(statistics.mean(total_times), 2) if total_times else 0,
                "Max Queue Size": max(queue_sizes) if queue_sizes else 0,
            }
        )

    trial_df = pd.DataFrame(rows)

    hc_percent = (
        trial_df["Served Passengers"].mean()
        * (300 / max(1, simulation_duration_sec))
        / max(1, bank.population_served)
        * 100
    )

    summary = {
        "Lift Bank": bank.bank_name,
        "Control": control_method,
        "Trials": trials,
        "Simulation Duration (s)": simulation_duration_sec,
        "Arrival Min (s)": arrival_min_sec,
        "Arrival Max (s)": arrival_max_sec,
        "Dispatch Wait (s)": dispatch_wait_sec,
        "Mean Waiting Time (s)": round(trial_df["Mean Waiting Time (s)"].mean(), 2),
        "Max Waiting Time (s)": round(trial_df["Max Waiting Time (s)"].max(), 2),
        "Mean Elevator Time (s)": round(trial_df["Mean Elevator Time (s)"].mean(), 2),
        "Mean Total Time (s)": round(trial_df["Mean Total Time (s)"].mean(), 2),
        "Max Queue Size": int(trial_df["Max Queue Size"].max()),
        "Simulation HC (%)": round(hc_percent, 2),
        "Average Served Passengers": round(trial_df["Served Passengers"].mean(), 1),
    }

    return summary, trial_df