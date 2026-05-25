import math


def calculate_flight_time(distance_m: float, v_max: float, acceleration: float, jerk: float) -> float:
    """
    Approximate kinematic flight time with speed, acceleration and jerk.
    This avoids assuming that the lift reaches rated speed on short hops.
    """
    if distance_m <= 0:
        return 0.0

    v_max = max(v_max, 0.1)
    acceleration = max(acceleration, 0.1)
    jerk = max(jerk, 0.1)

    distance_to_reach_speed = (v_max ** 2 / acceleration) + (v_max * (acceleration / jerk))

    if distance_m >= distance_to_reach_speed:
        return (distance_m / v_max) + (v_max / acceleration) + (acceleration / jerk)

    return 2 * math.sqrt(distance_m / acceleration) + (acceleration / jerk)