import pandas as pd

from core.models import BUILDING_TYPES, BUILDING_GRADES, DOOR_TYPES, ZONING_OPTIONS


def clean_input_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(subset=["bank_name"]).copy()

    for col, default, opts in [
        ("building_type", "Office", BUILDING_TYPES),
        ("building_grade", "Mainstream / Speculative Office", BUILDING_GRADES),
        ("door_type", "Center Opening", DOOR_TYPES),
        ("zoning_strategy", "Single Zone", ZONING_OPTIONS),
    ]:
        df[col] = df[col].fillna(default)
        df[col] = df[col].where(df[col].isin(opts), default)

    int_cols = [
        "floors_served",
        "population_served",
        "population_per_floor",
        "number_of_lifts",
        "car_capacity_persons",
        "door_clear_width_mm",
        "main_terminal_floor",
        "sky_lobby_floor",
        "fireman_lift_car_width_mm",
        "fireman_lift_car_depth_mm",
        "fireman_lift_door_clear_mm",
    ]

    float_cols = [
        "total_travel_height_m",
        "rated_speed_mps",
        "floor_height_m",
        "door_time_s",
        "passenger_transfer_time_s",
        "acceleration_mps2",
        "jerk_mps3",
        "passenger_lift_pit_depth_m",
        "passenger_lift_overhead_m",
        "service_lift_pit_depth_m",
        "service_lift_overhead_m",
        "fireman_lift_pit_depth_m",
        "fireman_lift_overhead_m",
    ]

    for col in int_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    for col in float_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0).astype(float)

    df["amenity_floor_numbers"] = df["amenity_floor_numbers"].fillna("").astype(str)

    return df