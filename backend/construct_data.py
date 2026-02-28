# import pandas as pd

# def build_dataset(energy_objects):
#     method = []
#     installation_cost = []
#     npv = []
#     for energy_object in energy_objects:
#         method.append(energy_object.name)
#         installation_cost.append(energy_object.installCost())
#         npv.append(energy_object.NPV())

#     df = pd.DataFrame({
#             "Method": method,
#             "NPV": npv,
#             "Installation Cost": installation_cost,
#         })

#     return df

# def convert_dataset():
#     #df = build_dataset()
#     df = pd.DataFrame({
#         "Method": ["Solar", "Wind", "Geothermal"],
#         "NPV": [100, 300, 200],
#         "Installation Cost": [100, 200, 300],
#         }
#     )
#     df_sorted = df.sort_values(by="NPV")
#     df_json = df_sorted.to_json()
#     return df_json
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict

@dataclass
class RetrofitOption:
    name: str
    npv: float
    installation_cost: float
    annual_savings: float
    reason: str

def mock_options() -> List[RetrofitOption]:
    return [
        RetrofitOption(
            name="Air sealing + attic insulation",
            npv=2400,
            installation_cost=1800,
            annual_savings=420,
            reason="Envelope improvements reduce heating/cooling demand and are usually the best first step.",
        ),
        RetrofitOption(
            name="Smart thermostat",
            npv=650,
            installation_cost=250,
            annual_savings=90,
            reason="Low cost, quick install; savings depend on occupant behavior and schedules.",
        ),
        RetrofitOption(
            name="Heat pump water heater",
            npv=600,
            installation_cost=2400,
            annual_savings=300,
            reason="High savings if replacing electric resistance water heating; moderate payback otherwise.",
        ),
    ]

def to_ranked_json(years_in_home: float) -> List[Dict]:
    """
    Returns a list of ranked options in the exact structure the frontend expects.
    """
    options = mock_options()
    ranked = []

    years_captured = min(max(years_in_home, 1.0), 15.0)

    for opt in options:
        payback = (opt.installation_cost / opt.annual_savings) if opt.annual_savings > 0 else 999.0
        value_during_stay = opt.annual_savings * years_captured - opt.installation_cost

        # simple hackathon score
        score = int(
            max(
                1,
                min(
                    99,
                    70 + (opt.annual_savings / 75.0) - (payback * 2.5) + (10 if value_during_stay > 0 else 0),
                ),
            )
        )

        ranked.append(
            {
                "name": opt.name,
                "score": score,
                "upfront_cost": round(opt.installation_cost, 0),
                "estimated_annual_savings": round(opt.annual_savings, 0),
                "simple_payback_years": round(payback, 1),
                "estimated_value_during_stay": round(value_during_stay, 0),
                "reason": opt.reason,
            }
        )

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked