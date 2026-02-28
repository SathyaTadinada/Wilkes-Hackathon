from __future__ import annotations
from typing import Any, Optional

def build_analysis_result(
    *,
    address: str,
    city: str,
    state: str,
    zip: str,
    years_in_home: float,
    average_sq_ft: float,
    is_electric_heating: bool,
    heating_fuel: str,
    cooling_fuel: str,
    electricity_mode: str,
    gas_mode: str,
    electric_data: dict[str, Any],
    gas_data: dict[str, Any],
    electricity_text: Optional[str],
    gas_text: Optional[str],
    ranked_options: list[dict[str, Any]],
    build_processing_summary_fn,
) -> dict[str, Any]:
    normalized_payload = {
        "address": address,
        "city": city,
        "state": state,
        "zip": zip,
        "cost_per_kwh": electric_data["cost_per_kwh"],
        "yearly_kwh_usage": electric_data["yearly_kwh_usage"],
        "cost_per_btu": gas_data["cost_per_btu"],
        "yearly_btu_usage": gas_data["yearly_btu_usage"],
        "years_in_home": years_in_home,
        "is_electric_heating": is_electric_heating,
        "average_sq_ft": average_sq_ft,
        "heating_fuel": heating_fuel,
        "cooling_fuel": cooling_fuel,
    }

    processing_summary = build_processing_summary_fn(normalized_payload)

    return {
        "ok": True,
        "message": "",
        "received_fields": {
            "address": address,
            "city": city,
            "state": state,
            "zip": zip,
            "years_in_home": years_in_home,
            "average_sq_ft": average_sq_ft,
            "is_electric_heating": is_electric_heating,
            "heating_fuel": heating_fuel,
            "cooling_fuel": cooling_fuel,
            "electricity_mode": electricity_mode,
            "gas_mode": gas_mode,
        },
        "electric_parse": {
            "source": electric_data.get("source"),
            "notes": electric_data.get("notes"),
            "pdf_text_preview": (electricity_text[:500] if electricity_text else None),
        },
        "gas_parse": {
            "source": gas_data.get("source"),
            "notes": gas_data.get("notes"),
            "pdf_text_preview": (gas_text[:500] if gas_text else None),
        },
        "normalized_payload": normalized_payload,
        "processing_summary": processing_summary,
        "ranked_options": ranked_options,
    }