from __future__ import annotations
from typing import Any


def build_processing_summary(payload: dict[str, Any]) -> dict[str, Any]:
    electric_cost = payload["cost_per_kwh"] * payload["yearly_kwh_usage"]
    gas_cost = payload["cost_per_btu"] * payload["yearly_btu_usage"]
    total = electric_cost + gas_cost
    return {
        "estimated_annual_electric_cost": round(electric_cost, 2),
        "estimated_annual_gas_cost": round(gas_cost, 2),
        "estimated_total_annual_energy_cost": round(total, 2),
        "estimated_monthly_energy_cost": round(total / 12.0, 2),
    }


def build_analysis_result(
    *,
    normalized_payload: dict[str, Any],
    processing_summary: dict[str, Any],
    ranked_options: list[dict[str, Any]],
    electricity_parse: dict[str, Any],
    gas_parse: dict[str, Any],
    modes: dict[str, str],
) -> dict[str, Any]:
    return {
        "ok": True,
        "message": "Backend received inputs, parsed utility values, and returned mock ranked retrofit options.",
        "modes": modes,
        "electric_parse": electricity_parse,
        "gas_parse": gas_parse,
        "normalized_payload": normalized_payload,
        "processing_summary": processing_summary,
        "ranked_options": ranked_options,
    }