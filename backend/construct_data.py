from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from Models import WindFast, SolarFast, GeoFast, EnergyEfficiencyFast


@dataclass
class RetrofitOption:
    name: str
    npv: float
    installation_cost: float
    annual_savings: float
    annual_energy_savings_kwh: float
    reason: str


def get_objects(normalized_payload: Dict[str, Any]):
    zipcode = int(normalized_payload["zip"])

    costperkWh = float(normalized_payload["cost_per_kwh"])
    kWhperyear = float(normalized_payload["yearly_kwh_usage"])

    costperBTU = float(normalized_payload["cost_per_btu"])
    BTUperyear = float(normalized_payload["yearly_btu_usage"])

    sqfeet = float(normalized_payload["average_sq_ft"])
    years = int(float(normalized_payload["years_in_home"]))

    ee = EnergyEfficiencyFast(zipcode, kWhperyear, costperkWh, BTUperyear, costperBTU, years)
    solar = SolarFast(zipcode, kWhperyear, costperkWh, years)
    wind = WindFast(zipcode, kWhperyear, costperkWh, years)
    geo = GeoFast(zipcode, kWhperyear, BTUperyear, costperkWh, costperBTU, years, sqfeet)

    return [ee, solar, wind, geo]


def mock_options(normalized_payload) -> List[RetrofitOption]:
    objs = get_objects(normalized_payload)
    options: List[RetrofitOption] = []

    for obj in objs:
        # tiny hackathon "reason" stubs
        reason = ""
        if obj.name == "Energy Efficiency":
            reason = "Usually the fastest, lowest-risk first step: reduce loads before upgrading equipment."
        elif obj.name == "Solar":
            reason = "Offsets electricity use with on-site generation; best when roof/solar access is good."
        elif obj.name == "Wind":
            reason = "Small residential wind can work in high-wind areas; more site-dependent than solar."
        elif obj.name == "Geothermal":
            reason = "Major heating/cooling savings, but higher upfront and more invasive installation."

        annual_kwh_saved = float(obj.annual_energy_savings_kwh_eq()) if hasattr(obj, "annual_energy_savings_kwh_eq") else 0.0

        options.append(
            RetrofitOption(
                name=obj.name,
                npv=float(obj.npv()),
                annual_savings=float(obj.annual_savings()),
                installation_cost=float(obj.installation_cost()),
                annual_energy_savings_kwh=float(annual_kwh_saved),
                reason=reason,
            )
        )

    return options


def to_ranked_json(normalized_payload) -> List[Dict]:
    """
    Returns a list of ranked options in the exact structure the frontend expects,
    plus one extra field used by the new UI pill:
      - estimated_annual_energy_savings_kwh
    """
    options = mock_options(normalized_payload)
    years_in_home = float(normalized_payload["years_in_home"])
    ranked: List[Dict[str, Any]] = []

    years_captured = max(years_in_home, 1.0)

    for opt in options:
        payback = (opt.installation_cost / opt.annual_savings) if opt.annual_savings > 0 else 999.0
        value_during_stay = opt.annual_savings * years_captured - opt.installation_cost

        # simple hackathon score
        score = int(
            max(
                1,
                min(
                    99,
                    68
                    + (opt.annual_savings / 85.0)
                    + (opt.annual_energy_savings_kwh / 2500.0)
                    - (payback * 2.0)
                    + (8 if value_during_stay > 0 else 0),
                ),
            )
        )

        ranked.append(
            {
                "name": opt.name,
                "score": score,
                "upfront_cost": round(opt.installation_cost, 0),
                "estimated_annual_savings": round(opt.annual_savings, 0),
                "estimated_annual_energy_savings_kwh": round(opt.annual_energy_savings_kwh, 0),
                "simple_payback_years": round(payback, 1),
                "estimated_value_during_stay": round(value_during_stay, 0),
                "reason": opt.reason,
            }
        )

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked