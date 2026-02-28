from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict
from analysis_core import build_analysis_result
from Models import *

@dataclass
class RetrofitOption:
    name: str
    npv: float
    installation_cost: float
    annual_savings: float
    reason: str

def get_objects():
    params = build_analysis_result
    normalized_payload = params['received_fields']
    zipcode = normalized_payload['zip']
    costperkWh = normalized_payload['cost_per_kwh']
    kWhperyear = normalized_payload['yearly_kwh_usage']
    costperBTU = normalized_payload['cost_per_btu']
    BTUperyear = normalized_payload['yearly_btu_usage']
    sqfeet = normalized_payload['average_sq_ft']
    years = normalized_payload['years_in_home']

    inputs = [
        zipcode,
        costperkWh,
        kWhperyear,
        costperBTU,
        BTUperyear,
        sqfeet,
        years,
    ]

    solar = Solar(*inputs)
    wind = Wind(*inputs)
    geo = Geo(*inputs)
    dummy = Dummy(*inputs)

    #return [solar, wind, geo]
    return [dummy]

def mock_options() -> List[RetrofitOption]:
    energy_objects = get_objects()
    df = []
    for energy_object in energy_objects:
        df.append(RetrofitOption(
            name=energy_object.name,
            npv=energy_object.NPV(),
            annual_savings=energy_object.ann,
            installation_cost=energy_object.installCost(),
            reason="fuckass",
            )
        )
    return df

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