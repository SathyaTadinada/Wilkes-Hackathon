from __future__ import annotations

import io
import os
import re
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pypdf import PdfReader
import uvicorn

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("retrofit")

app = FastAPI(title="Retrofit Backend", version="0.1.0")

ANNUAL_RE = re.compile(r"annual|annually|yearly|per year|12 months", re.IGNORECASE)

def to_float(token: str) -> float:
    return float(token.replace(",", "").strip())


def round_to(value: float, decimals: int) -> float:
    factor = 10 ** decimals
    return round(value * factor) / factor


def context_looks_annual(context: str) -> bool:
    return bool(ANNUAL_RE.search(context))


def collect_unit_candidates(
    text: str,
    pattern: re.Pattern[str],
    multiplier: float,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []

    for match in pattern.finditer(text):
        raw = match.group(1)
        value = to_float(raw) * multiplier

        start = max(0, match.start() - 24)
        end = min(len(text), match.end() + 24)
        context = text[start:end]

        candidates.append(
            {
                "value": value,
                "is_annual": context_looks_annual(context),
                "context": context,
            }
        )

    return candidates


def choose_usage_value(
    candidates: list[dict[str, Any]],
    label: str,
) -> tuple[float, bool]:
    if not candidates:
        raise ValueError(f"Could not find {label} usage in the PDF text.")

    annual_candidate = next((c for c in candidates if c["is_annual"]), None)
    chosen = annual_candidate if annual_candidate is not None else max(
        candidates,
        key=lambda c: c["value"],
    )

    yearly_value = chosen["value"] if chosen["is_annual"] else chosen["value"] * 12
    return yearly_value, bool(chosen["is_annual"])


def require_complete_override_pair(
    rate_value: float | None,
    usage_value: float | None,
    utility_name: str,
) -> None:
    only_one_present = (rate_value is None) != (usage_value is None)
    if only_one_present:
        raise HTTPException(
            status_code=400,
            detail=f"For {utility_name}, provide both override fields or neither.",
        )


async def extract_pdf_text(upload: UploadFile | None) -> str | None:
    if upload is None:
        return None

    file_bytes = await upload.read()
    await upload.close()

    if not file_bytes:
        return None

    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        page_texts: list[str] = []

        for page in reader.pages:
            page_texts.append(page.extract_text() or "")

        text = "\n".join(page_texts).strip()
        return text or None
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Could not read PDF '{upload.filename}': {exc}",
        ) from exc


def parse_electricity_text(text: str) -> dict[str, Any]:
    normalized = re.sub(r"\s+", " ", text).strip()

    if not normalized:
        raise ValueError("Electricity PDF did not contain extractable text.")

    cost_per_kwh: float | None = None

    cents_rate = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:¢|cents?)\s*(?:per|/)\s*kwh",
        normalized,
        re.IGNORECASE,
    )
    if cents_rate:
        cost_per_kwh = to_float(cents_rate.group(1)) / 100.0

    if cost_per_kwh is None:
        dollar_rate = re.search(
            r"\$?\s*(\d+(?:\.\d+)?)\s*(?:per|/)\s*kwh",
            normalized,
            re.IGNORECASE,
        )
        if dollar_rate:
            cost_per_kwh = to_float(dollar_rate.group(1))

    if cost_per_kwh is None:
        raise ValueError(
            "Could not parse cost per kWh from electricity PDF. "
            "Use an override or include text like '$0.12 per kWh'."
        )

    usage_candidates = collect_unit_candidates(
        normalized,
        re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*kwh\b", re.IGNORECASE),
        1.0,
    )
    yearly_kwh_usage, was_annual = choose_usage_value(usage_candidates, "electricity")

    return {
        "cost_per_kwh": round_to(cost_per_kwh, 6),
        "yearly_kwh_usage": round_to(yearly_kwh_usage, 2),
        "notes": [
            "Electricity usage was detected as annual."
            if was_annual
            else "Electricity usage looked monthly, so it was multiplied by 12."
        ],
    }


def parse_gas_text(text: str) -> dict[str, Any]:
    normalized = re.sub(r"\s+", " ", text).strip()

    if not normalized:
        raise ValueError("Gas PDF did not contain extractable text.")

    cost_per_btu: float | None = None

    direct_btu = re.search(
        r"\$?\s*(\d+(?:\.\d+)?)\s*(?:per|/)\s*btu",
        normalized,
        re.IGNORECASE,
    )
    if direct_btu:
        cost_per_btu = to_float(direct_btu.group(1))

    if cost_per_btu is None:
        mmbtu_rate = re.search(
            r"\$?\s*(\d+(?:\.\d+)?)\s*(?:per|/)\s*mmbtu",
            normalized,
            re.IGNORECASE,
        )
        if mmbtu_rate:
            cost_per_btu = to_float(mmbtu_rate.group(1)) / 1_000_000.0

    if cost_per_btu is None:
        therm_rate = re.search(
            r"\$?\s*(\d+(?:\.\d+)?)\s*(?:per|/)\s*therms?\b",
            normalized,
            re.IGNORECASE,
        )
        if therm_rate:
            cost_per_btu = to_float(therm_rate.group(1)) / 100_000.0

    if cost_per_btu is None:
        therm_rate_cents = re.search(
            r"(\d+(?:\.\d+)?)\s*(?:¢|cents?)\s*(?:per|/)\s*therms?\b",
            normalized,
            re.IGNORECASE,
        )
        if therm_rate_cents:
            cost_per_btu = to_float(therm_rate_cents.group(1)) / 100.0 / 100_000.0

    if cost_per_btu is None:
        raise ValueError(
            "Could not parse cost per BTU from gas PDF. "
            "Use an override or include text like '$1.20 per therm' or '$14 per MMBtu'."
        )

    btu_candidates = collect_unit_candidates(
        normalized,
        re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*btu\b", re.IGNORECASE),
        1.0,
    )
    therm_candidates = collect_unit_candidates(
        normalized,
        re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*therms?\b", re.IGNORECASE),
        100_000.0,
    )
    mmbtu_candidates = collect_unit_candidates(
        normalized,
        re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*mmbtu\b", re.IGNORECASE),
        1_000_000.0,
    )

    all_candidates = btu_candidates + therm_candidates + mmbtu_candidates
    yearly_btu_usage, was_annual = choose_usage_value(all_candidates, "gas")

    return {
        "cost_per_btu": round_to(cost_per_btu, 10),
        "yearly_btu_usage": round_to(yearly_btu_usage, 2),
        "notes": [
            "Gas usage was detected as annual."
            if was_annual
            else "Gas usage looked monthly, so it was multiplied by 12."
        ],
    }


def build_mock_ranked_options(
    normalized_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    electric_annual_cost = (
        normalized_payload["cost_per_kwh"] * normalized_payload["yearly_kwh_usage"]
    )
    gas_annual_cost = (
        normalized_payload["cost_per_btu"] * normalized_payload["yearly_btu_usage"]
    )
    total_annual_energy_cost = electric_annual_cost + gas_annual_cost

    years_in_home = normalized_payload["years_in_home"]
    average_sq_ft = normalized_payload["average_sq_ft"]
    is_electric_heating = normalized_payload["is_electric_heating"]

    heating_energy_cost = (
        electric_annual_cost if is_electric_heating else gas_annual_cost
    )

    options = [
        {
            "name": "Smart thermostat",
            "upfront_cost": 250.0,
            "annual_savings": max(60.0, total_annual_energy_cost * 0.05),
            "reason": "Low-cost control upgrade with fast implementation.",
        },
        {
            "name": "Air sealing + attic insulation",
            "upfront_cost": max(1800.0, average_sq_ft * 1.75),
            "annual_savings": max(180.0, heating_energy_cost * 0.14),
            "reason": "Envelope improvements reduce heating and cooling demand.",
        },
        {
            "name": "High-efficiency HVAC / heat pump upgrade",
            "upfront_cost": max(6500.0, average_sq_ft * 4.0),
            "annual_savings": max(
                350.0,
                heating_energy_cost * (0.22 if is_electric_heating else 0.28),
            ),
            "reason": "Higher upfront cost, but larger long-term savings potential.",
        },
    ]

    ranked: list[dict[str, Any]] = []

    for option in options:
        annual_savings = float(option["annual_savings"])
        upfront_cost = float(option["upfront_cost"])
        payback_years = upfront_cost / annual_savings if annual_savings > 0 else 999.0

        years_captured = min(years_in_home, 15.0)
        lifetime_value = annual_savings * years_captured - upfront_cost

        score = max(
            1,
            min(
                99,
                int(
                    60
                    + (annual_savings / 75.0)
                    - (payback_years * 2.5)
                    + (10 if lifetime_value > 0 else 0)
                ),
            ),
        )

        ranked.append(
            {
                "name": option["name"],
                "score": score,
                "upfront_cost": round_to(upfront_cost, 0),
                "estimated_annual_savings": round_to(annual_savings, 0),
                "simple_payback_years": round_to(payback_years, 1),
                "estimated_value_during_stay": round_to(lifetime_value, 0),
                "reason": option["reason"],
            }
        )

    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked


def build_processing_summary(normalized_payload: dict[str, Any]) -> dict[str, Any]:
    electric_annual_cost = (
        normalized_payload["cost_per_kwh"] * normalized_payload["yearly_kwh_usage"]
    )
    gas_annual_cost = (
        normalized_payload["cost_per_btu"] * normalized_payload["yearly_btu_usage"]
    )

    return {
        "estimated_annual_electric_cost": round_to(electric_annual_cost, 2),
        "estimated_annual_gas_cost": round_to(gas_annual_cost, 2),
        "estimated_total_annual_energy_cost": round_to(
            electric_annual_cost + gas_annual_cost,
            2,
        ),
        "estimated_monthly_energy_cost": round_to(
            (electric_annual_cost + gas_annual_cost) / 12.0,
            2,
        ),
    }


@app.post("/rank")
async def rank(
    address: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    zip: str = Form(...),
    years_in_home: float = Form(...),
    average_sq_ft: float = Form(...),
    is_electric_heating: bool = Form(...),
    heating_fuel: str = Form(...),
    cooling_fuel: str = Form(...),
    electric_rate_override: float | None = Form(None),
    yearly_kwh_override: float | None = Form(None),
    gas_rate_override: float | None = Form(None),
    yearly_btu_override: float | None = Form(None),
    electricity_pdf: UploadFile | None = File(None),
    gas_pdf: UploadFile | None = File(None),
) -> dict[str, Any]:

    logger.info(
        "POST /rank: %s, %s %s, electric_pdf=%s, gas_pdf=%s, electric_overrides=%s, gas_overrides=%s",
        address,
        city,
        zip,
        electricity_pdf is not None,
        gas_pdf is not None,
        (electric_rate_override is not None and yearly_kwh_override is not None),
        (gas_rate_override is not None and yearly_btu_override is not None),
    )

    if years_in_home <= 0:
        raise HTTPException(
            status_code=400,
            detail="years_in_home must be greater than 0.",
        )

    if average_sq_ft <= 0:
        raise HTTPException(
            status_code=400,
            detail="average_sq_ft must be greater than 0.",
        )

    require_complete_override_pair(
        electric_rate_override,
        yearly_kwh_override,
        "electricity",
    )
    require_complete_override_pair(
        gas_rate_override,
        yearly_btu_override,
        "gas",
    )

    has_electric_overrides = (
        electric_rate_override is not None and yearly_kwh_override is not None
    )
    has_gas_overrides = (
        gas_rate_override is not None and yearly_btu_override is not None
    )

    if electricity_pdf is None and not has_electric_overrides:
        raise HTTPException(
            status_code=400,
            detail=(
                "Electricity data is incomplete. Upload an electricity PDF "
                "or provide both electric overrides."
            ),
        )

    if gas_pdf is None and not has_gas_overrides:
        raise HTTPException(
            status_code=400,
            detail=(
                "Gas data is incomplete. Upload a gas PDF "
                "or provide both gas overrides."
            ),
        )

    electricity_text = await extract_pdf_text(electricity_pdf) if electricity_pdf else None
    gas_text = await extract_pdf_text(gas_pdf) if gas_pdf else None

    try:
        if has_electric_overrides:
            electric_data = {
                "cost_per_kwh": round_to(float(electric_rate_override), 6),
                "yearly_kwh_usage": round_to(float(yearly_kwh_override), 2),
                "source": "override",
                "notes": ["Used explicit electricity overrides."],
            }
        else:
            if electricity_text is None:
                raise ValueError("Electricity PDF had no extractable text.")
            parsed = parse_electricity_text(electricity_text)
            electric_data = {
                **parsed,
                "source": "pdf",
            }

        if has_gas_overrides:
            gas_data = {
                "cost_per_btu": round_to(float(gas_rate_override), 10),
                "yearly_btu_usage": round_to(float(yearly_btu_override), 2),
                "source": "override",
                "notes": ["Used explicit gas overrides."],
            }
        else:
            if gas_text is None:
                raise ValueError("Gas PDF had no extractable text.")
            parsed = parse_gas_text(gas_text)
            gas_data = {
                **parsed,
                "source": "pdf",
            }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

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
    }

    processing_summary = build_processing_summary(normalized_payload)
    ranked_options = build_mock_ranked_options(normalized_payload)

    return {
        "ok": True,
        "message": "Backend received the upload, parsed the values, and generated mock ranked options.",
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
            "has_electricity_pdf": electricity_pdf is not None,
            "has_gas_pdf": gas_pdf is not None,
        },
        "electric_parse": {
            "source": electric_data["source"],
            "notes": electric_data["notes"],
            "pdf_text_preview": (electricity_text[:500] if electricity_text else None),
        },
        "gas_parse": {
            "source": gas_data["source"],
            "notes": gas_data["notes"],
            "pdf_text_preview": (gas_text[:500] if gas_text else None),
        },
        "normalized_payload": normalized_payload,
        "processing_summary": processing_summary,
        "ranked_options": ranked_options,
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("BACKEND_HOST", "127.0.0.1"),
        port=int(os.getenv("BACKEND_PORT", "8000")),
        reload=True,
    )