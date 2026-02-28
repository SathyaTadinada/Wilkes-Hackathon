from __future__ import annotations

import io
import os
import re
from typing import Any, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pypdf import PdfReader
import uvicorn

from construct_data import to_ranked_json

from analysis_core import build_analysis_result

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("retrofit")

app = FastAPI(title="Retrofit Backend", version="0.2.0")

def parse_cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "")
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    return origins if origins else ["http://localhost:3000", "http://127.0.0.1:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=parse_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ANNUAL_RE = re.compile(r"annual|annually|yearly|per year|12 months", re.IGNORECASE)

def to_float(token: str) -> float:
    return float(token.replace(",", "").strip())

def round_to(value: float, decimals: int) -> float:
    factor = 10 ** decimals
    return round(value * factor) / factor

def context_looks_annual(context: str) -> bool:
    return bool(ANNUAL_RE.search(context))

def collect_unit_candidates(text: str, pattern: re.Pattern[str], multiplier: float) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for match in pattern.finditer(text):
        raw = match.group(1)
        value = to_float(raw) * multiplier
        start = max(0, match.start() - 28)
        end = min(len(text), match.end() + 28)
        context = text[start:end]
        candidates.append({"value": value, "is_annual": context_looks_annual(context), "context": context})
    return candidates

def choose_usage_value(candidates: list[dict[str, Any]], label: str) -> tuple[float, bool]:
    if not candidates:
        raise ValueError(f"Could not find {label} usage in the PDF text.")
    annual_candidate = next((c for c in candidates if c["is_annual"]), None)
    chosen = annual_candidate if annual_candidate is not None else max(candidates, key=lambda c: c["value"])
    yearly = chosen["value"] if chosen["is_annual"] else chosen["value"] * 12
    return yearly, bool(chosen["is_annual"])

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
        raise HTTPException(status_code=400, detail=f"Could not read PDF '{upload.filename}': {exc}") from exc

def parse_electricity_text(text: str) -> dict[str, Any]:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        raise ValueError("Electricity PDF did not contain extractable text.")

    cost_per_kwh: float | None = None

    cents_rate = re.search(r"(\d+(?:\.\d+)?)\s*(?:¢|cents?)\s*(?:per|/)\s*kwh", normalized, re.IGNORECASE)
    if cents_rate:
        cost_per_kwh = to_float(cents_rate.group(1)) / 100.0

    if cost_per_kwh is None:
        dollar_rate = re.search(r"\$?\s*(\d+(?:\.\d+)?)\s*(?:per|/)\s*kwh", normalized, re.IGNORECASE)
        if dollar_rate:
            cost_per_kwh = to_float(dollar_rate.group(1))

    if cost_per_kwh is None:
        raise ValueError("Could not parse cost per kWh from electricity PDF. Use manual mode if needed.")

    usage_candidates = collect_unit_candidates(
        normalized,
        re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*kwh\b", re.IGNORECASE),
        1.0,
    )
    yearly_kwh, was_annual = choose_usage_value(usage_candidates, "electricity")

    return {
        "cost_per_kwh": round_to(cost_per_kwh, 6),
        "yearly_kwh_usage": round_to(yearly_kwh, 2),
        "notes": ["Detected annual usage." if was_annual else "Detected monthly-ish usage; multiplied by 12."],
    }

def parse_gas_text(text: str) -> dict[str, Any]:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        raise ValueError("Gas PDF did not contain extractable text.")

    cost_per_btu: float | None = None

    direct_btu = re.search(r"\$?\s*(\d+(?:\.\d+)?)\s*(?:per|/)\s*btu", normalized, re.IGNORECASE)
    if direct_btu:
        cost_per_btu = to_float(direct_btu.group(1))

    if cost_per_btu is None:
        mmbtu_rate = re.search(r"\$?\s*(\d+(?:\.\d+)?)\s*(?:per|/)\s*mmbtu", normalized, re.IGNORECASE)
        if mmbtu_rate:
            cost_per_btu = to_float(mmbtu_rate.group(1)) / 1_000_000.0

    if cost_per_btu is None:
        therm_rate = re.search(r"\$?\s*(\d+(?:\.\d+)?)\s*(?:per|/)\s*therms?\b", normalized, re.IGNORECASE)
        if therm_rate:
            cost_per_btu = to_float(therm_rate.group(1)) / 100_000.0

    if cost_per_btu is None:
        therm_rate_cents = re.search(r"(\d+(?:\.\d+)?)\s*(?:¢|cents?)\s*(?:per|/)\s*therms?\b", normalized, re.IGNORECASE)
        if therm_rate_cents:
            cost_per_btu = (to_float(therm_rate_cents.group(1)) / 100.0) / 100_000.0

    if cost_per_btu is None:
        raise ValueError("Could not parse cost per BTU from gas PDF. Use manual mode if needed.")

    btu_candidates = collect_unit_candidates(normalized, re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*btu\b", re.IGNORECASE), 1.0)
    therm_candidates = collect_unit_candidates(normalized, re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*therms?\b", re.IGNORECASE), 100_000.0)
    mmbtu_candidates = collect_unit_candidates(normalized, re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*mmbtu\b", re.IGNORECASE), 1_000_000.0)

    yearly_btu, was_annual = choose_usage_value(btu_candidates + therm_candidates + mmbtu_candidates, "gas")

    return {
        "cost_per_btu": round_to(cost_per_btu, 10),
        "yearly_btu_usage": round_to(yearly_btu, 2),
        "notes": ["Detected annual usage." if was_annual else "Detected monthly-ish usage; multiplied by 12."],
    }

def build_processing_summary(payload: dict[str, Any]) -> dict[str, Any]:
    electric_cost = payload["cost_per_kwh"] * payload["yearly_kwh_usage"]
    gas_cost = payload["cost_per_btu"] * payload["yearly_btu_usage"]
    total = electric_cost + gas_cost
    return {
        "estimated_annual_electric_cost": round_to(electric_cost, 2),
        "estimated_annual_gas_cost": round_to(gas_cost, 2),
        "estimated_total_annual_energy_cost": round_to(total, 2),
        "estimated_monthly_energy_cost": round_to(total / 12.0, 2),
    }

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/analyze")
async def analyze(
    # Address
    address: str = Form(...),
    city: str = Form(...),
    state: str = Form(...),
    zip: str = Form(...),

    # Home info
    years_in_home: float = Form(...),
    average_sq_ft: float = Form(...),
    is_electric_heating: bool = Form(...),
    heating_fuel: str = Form(...),
    cooling_fuel: str = Form(...),

    # Modes
    electricity_mode: str = Form(...),  # "pdf" | "manual"
    gas_mode: str = Form(...),          # "pdf" | "manual"

    # Manual fields
    electric_rate_override: Optional[float] = Form(None),
    yearly_kwh_override: Optional[float] = Form(None),
    gas_rate_override: Optional[float] = Form(None),
    yearly_btu_override: Optional[float] = Form(None),

    # PDFs
    electricity_pdf: UploadFile | None = File(None),
    gas_pdf: UploadFile | None = File(None),
) -> dict[str, Any]:
    logger.info("POST /analyze: %s, %s %s", address, city, zip)

    if years_in_home <= 0:
        raise HTTPException(status_code=400, detail="years_in_home must be > 0.")
    if average_sq_ft <= 0:
        raise HTTPException(status_code=400, detail="average_sq_ft must be > 0.")

    if electricity_mode not in ("pdf", "manual"):
        raise HTTPException(status_code=400, detail="electricity_mode must be 'pdf' or 'manual'.")
    if gas_mode not in ("pdf", "manual"):
        raise HTTPException(status_code=400, detail="gas_mode must be 'pdf' or 'manual'.")

    # Validate per-mode
    if electricity_mode == "pdf" and electricity_pdf is None:
        raise HTTPException(status_code=400, detail="Electricity mode is pdf but no electricity_pdf was provided.")
    if electricity_mode == "manual" and (electric_rate_override is None or yearly_kwh_override is None):
        raise HTTPException(status_code=400, detail="Electricity mode is manual; provide electric_rate_override and yearly_kwh_override.")

    if gas_mode == "pdf" and gas_pdf is None:
        raise HTTPException(status_code=400, detail="Gas mode is pdf but no gas_pdf was provided.")
    if gas_mode == "manual" and (gas_rate_override is None or yearly_btu_override is None):
        raise HTTPException(status_code=400, detail="Gas mode is manual; provide gas_rate_override and yearly_btu_override.")

    electricity_text = await extract_pdf_text(electricity_pdf) if electricity_pdf else None
    gas_text = await extract_pdf_text(gas_pdf) if gas_pdf else None

    try:
        if electricity_mode == "manual":
            electric_data = {
                "cost_per_kwh": round_to(float(electric_rate_override), 6),
                "yearly_kwh_usage": round_to(float(yearly_kwh_override), 2),
                "source": "manual",
                "notes": ["Used manual electricity values."],
            }
        else:
            if electricity_text is None:
                raise ValueError("Electricity PDF had no extractable text.")
            parsed = parse_electricity_text(electricity_text)
            electric_data = {**parsed, "source": "pdf"}

        if gas_mode == "manual":
            gas_data = {
                "cost_per_btu": round_to(float(gas_rate_override), 10),
                "yearly_btu_usage": round_to(float(yearly_btu_override), 2),
                "source": "manual",
                "notes": ["Used manual gas values."],
            }
        else:
            if gas_text is None:
                raise ValueError("Gas PDF had no extractable text.")
            parsed = parse_gas_text(gas_text)
            gas_data = {**parsed, "source": "pdf"}

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    normalized_payload = {
        "zip": zip,
        "cost_per_kwh": electric_data["cost_per_kwh"],
        "yearly_kwh_usage": electric_data["yearly_kwh_usage"],
        "cost_per_btu": gas_data["cost_per_btu"],
        "yearly_btu_usage": gas_data["yearly_btu_usage"],
        "years_in_home": years_in_home,
        "average_sq_ft": average_sq_ft,
    }

    ranked_options = to_ranked_json(normalized_payload)

    result = build_analysis_result(
        address=address,
        city=city,
        state=state,
        zip=zip,
        years_in_home=years_in_home,
        average_sq_ft=average_sq_ft,
        is_electric_heating=is_electric_heating,
        heating_fuel=heating_fuel,
        cooling_fuel=cooling_fuel,
        electricity_mode=electricity_mode,
        gas_mode=gas_mode,
        electric_data=electric_data,
        gas_data=gas_data,
        electricity_text=electricity_text,
        gas_text=gas_text,
        ranked_options=ranked_options,
        build_processing_summary_fn=build_processing_summary,
    )
    return result

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("BACKEND_HOST", "127.0.0.1"),
        port=int(os.getenv("BACKEND_PORT", "8000")),
        reload=True,
    )