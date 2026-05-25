from typing import Dict

from core.models import LiftBankInput


def benchmark_for(bank: LiftBankInput) -> Dict[str, float | str]:
    table = {
        "Prestige / Corporate Office": (25, 30, 12, 15, 90, 120),
        "Mainstream / Speculative Office": (30, 40, 11, 13, 90, 120),
        "Luxury Residential": (45, 45, 6, 7, 120, 120),
        "Standard Residential": (60, 60, 5, 7, 120, 120),
        "Hotel 4-5 Star": (30, 35, 10, 12, 120, 120),
        "Hospital": (35, 45, 10, 12, 120, 150),
        "Mixed Use": (40, 45, 9, 11, 120, 130),
    }

    awt_ex, awt_acc, hc_min, hc_target, attd_ideal, attd_max = table.get(
        bank.building_grade, table["Mixed Use"]
    )

    return {
        "awt_excellent": awt_ex,
        "awt_acceptable": awt_acc,
        "hc_min": hc_min,
        "hc_target": hc_target,
        "attd_ideal": attd_ideal,
        "attd_max": attd_max,
        "source": "CIBSE Guide D / ISO 8100-32 benchmark basis",
    }