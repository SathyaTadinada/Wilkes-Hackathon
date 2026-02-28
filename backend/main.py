from __future__ import annotations

import io
import os
import re
import logging
from typing import Any, Optional, Callable

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pypdf import PdfReader
import uvicorn

from construct_data import to_ranked_json
from analysis_core import build_analysis_result, build_processing_summary

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("retrofit")

app = FastAPI(title="Retrofit Backend", version="0.3.0")


def parse_cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "")
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    return origins or ["http://localhost:3000", "http://127.0.0.1:3000"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=parse_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ANNUAL_RE = re.compile(r"annual|annually|yearly|per year|12 months", re.IGNORECASE)


def round_to(value: float, decimals: int) -> float:
    factor = 10**decimals
    return round(value * factor) / factor


def to_float(token: str) -> float:
    return float(token.replace(",", "").strip())


def context_looks_annual(context: str) -> bool:
    return bool(ANNUAL_RE.search(context))


async def extract_pdf_text(upload: UploadFile) -> str:
    file_bytes = await upload.read()
    await upload.close()

    if not file_bytes:
        raise HTTPException(status_code=400, detail=f"PDF '{upload.filename}' was empty.")

    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        text = "\n".join((page.extract_text() or "") for page in reader.pages).strip()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read PDF '{upload.filename}': {exc}") from exc

    if not text:
        raise HTTPException(status_code=400, detail=f"PDF '{upload.filename}' had no extractable text.")
    return text


def choose_yearly_usage(text: str, pattern: re.Pattern[str], multiplier: float, label: str) -> tuple[float, bool]:
    """
    Finds usage candidates and returns (yearly_value, was_annual).
    If not annual-looking, assumes monthly and multiplies by 12.
    """
    candidates: list[dict[str, Any]] = []

    for match in pattern.finditer(text):
        raw = match.group(1)
        value = to_float(raw) * multiplier

        start = max(0, match.start() - 28)
        end = min(len(text), match.end() + 28)
        context = text[start:end]

        candidates.append(
            {"value": value, "is_annual": context_looks_annual(context)}
        )

    if not candidates:
        raise ValueError(f"Could not find {label} usage in the PDF text.")

    annual = next((c for c in candidates if c["is_annual"]), None)
    chosen = annual if annual is not None else max(candidates, key=lambda c: c["value"])

    yearly = chosen["value"] if chosen["is_annual"] else chosen["value"] * 12
    return yearly, bool(chosen["is_annual"])


def parse_electricity_text(text: str) -> dict[str, Any]:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        raise ValueError("Electricity PDF did not contain extractable text.")

    # Rate: prefer cents/kWh, else dollars/kWh
    cents_rate = re.search(r"(\d+(?:\.\d+)?)\s*(?:¢|cents?)\s*(?:per|/)\s*kwh", normalized, re.IGNORECASE)
    dollar_rate = re.search(r"\$?\s*(\d+(?:\.\d+)?)\s*(?:per|/)\s*kwh", normalized, re.IGNORECASE)

    cost_per_kwh: float | None = None
    if cents_rate:
        cost_per_kwh = to_float(cents_rate.group(1)) / 100.0
    elif dollar_rate:
        cost_per_kwh = to_float(dollar_rate.group(1))

    if cost_per_kwh is None:
        raise ValueError("Could not parse cost per kWh from electricity PDF. Use manual mode if needed.")

    yearly_kwh, was_annual = choose_yearly_usage(
        normalized,
        re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*kwh\b", re.IGNORECASE),
        1.0,
        "electricity",
    )

    return {
        "cost_per_kwh": round_to(cost_per_kwh, 6),
        "yearly_kwh_usage": round_to(yearly_kwh, 2),
        "notes": ["Detected annual usage." if was_annual else "Detected monthly-ish usage; multiplied by 12."],
    }


def parse_gas_text(text: str) -> dict[str, Any]:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        raise ValueError("Gas PDF did not contain extractable text.")

    # Rate parsing
    direct_btu = re.search(r"\$?\s*(\d+(?:\.\d+)?)\s*(?:per|/)\s*btu", normalized, re.IGNORECASE)
    mmbtu_rate = re.search(r"\$?\s*(\d+(?:\.\d+)?)\s*(?:per|/)\s*mmbtu", normalized, re.IGNORECASE)
    therm_rate = re.search(r"\$?\s*(\d+(?:\.\d+)?)\s*(?:per|/)\s*therms?\b", normalized, re.IGNORECASE)
    therm_rate_cents = re.search(r"(\d+(?:\.\d+)?)\s*(?:¢|cents?)\s*(?:per|/)\s*therms?\b", normalized, re.IGNORECASE)

    cost_per_btu: float | None = None
    if direct_btu:
        cost_per_btu = to_float(direct_btu.group(1))
    elif mmbtu_rate:
        cost_per_btu = to_float(mmbtu_rate.group(1)) / 1_000_000.0
    elif therm_rate:
        cost_per_btu = to_float(therm_rate.group(1)) / 100_000.0
    elif therm_rate_cents:
        cost_per_btu = (to_float(therm_rate_cents.group(1)) / 100.0) / 100_000.0

    if cost_per_btu is None:
        raise ValueError("Could not parse cost per BTU from gas PDF. Use manual mode if needed.")

    # Usage parsing: accept BTU, therms, or MMBtu (convert to BTU)
    btu_candidates = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*btu\b", re.IGNORECASE)
    therm_candidates = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*therms?\b", re.IGNORECASE)
    mmbtu_candidates = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*mmbtu\b", re.IGNORECASE)

    # Find yearly via "best" match among all units
    # We’ll just run choose_yearly_usage on each and take the max yearly (simple heuristic)
    yearly_values: list[tuple[float, bool]] = []

    def try_usage(pat: re.Pattern[str], mult: float):
        try:
            yearly_values.append(choose_yearly_usage(normalized, pat, mult, "gas"))
        except ValueError:
            pass

    try_usage(btu_candidates, 1.0)
    try_usage(therm_candidates, 100_000.0)
    try_usage(mmbtu_candidates, 1_000_000.0)

    if not yearly_values:
        raise ValueError("Could not find gas usage in BTU/therms/MMBtu in the PDF text.")

    yearly_btu, was_annual = max(yearly_values, key=lambda t: t[0])

    return {
        "cost_per_btu": round_to(cost_per_btu, 10),
        "yearly_btu_usage": round_to(yearly_btu, 2),
        "notes": ["Detected annual usage." if was_annual else "Detected monthly-ish usage; multiplied by 12."],
    }


def parse_utility(
    *,
    mode: str,
    pdf: UploadFile | None,
    rate_override: Optional[float],
    usage_override: Optional[float],
    pdf_parser: Callable[[str], dict[str, Any]],
    rate_key: str,
    usage_key: str,
    rate_decimals: int,
    usage_decimals: int,
    label: str,
) -> tuple[dict[str, Any], Optional[str]]:
    """
    Returns (utility_data, pdf_text_preview_source_text_or_none)
    utility_data contains the normalized keys needed downstream.
    """
    if mode == "manual":
        if rate_override is None or usage_override is None:
            raise HTTPException(status_code=400, detail=f"{label} mode is manual; provide both override fields.")
        return (
            {
                rate_key: round_to(float(rate_override), rate_decimals),
                usage_key: round_to(float(usage_override), usage_decimals),
                "source": "manual",
                "notes": [f"Used manual {label} values."],
            },
            None,
        )

    # mode == "pdf"
    if pdf is None:
        raise HTTPException(status_code=400, detail=f"{label} mode is pdf but no PDF was provided.")


    # Extract text (raises HTTPException on failure)
    # `extract_pdf_text` is async, so we can’t call it here; handled in route.
    raise RuntimeError("parse_utility(pdf) should not be used directly without extracted text.")


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

    # Basic validation
    if years_in_home <= 0:
        raise HTTPException(status_code=400, detail="years_in_home must be > 0.")
    if average_sq_ft <= 0:
        raise HTTPException(status_code=400, detail="average_sq_ft must be > 0.")
    if electricity_mode not in ("pdf", "manual"):
        raise HTTPException(status_code=400, detail="electricity_mode must be 'pdf' or 'manual'.")
    if gas_mode not in ("pdf", "manual"):
        raise HTTPException(status_code=400, detail="gas_mode must be 'pdf' or 'manual'.")

    # Extract PDF text only if needed
    electricity_text = await extract_pdf_text(electricity_pdf) if (electricity_mode == "pdf" and electricity_pdf) else None
    gas_text = await extract_pdf_text(gas_pdf) if (gas_mode == "pdf" and gas_pdf) else None

    # Parse utilities (single pattern for both)
    try:
        if electricity_mode == "manual":
            if electric_rate_override is None or yearly_kwh_override is None:
                raise HTTPException(status_code=400, detail="Electricity manual mode requires electric_rate_override + yearly_kwh_override.")
            electric_data = {
                "cost_per_kwh": round_to(float(electric_rate_override), 6),
                "yearly_kwh_usage": round_to(float(yearly_kwh_override), 2),
                "source": "manual",
                "notes": ["Used manual electricity values."],
            }
        else:
            if electricity_text is None:
                raise HTTPException(status_code=400, detail="Electricity pdf mode requires electricity_pdf with extractable text.")
            parsed = parse_electricity_text(electricity_text)
            electric_data = {**parsed, "source": "pdf"}

        if gas_mode == "manual":
            if gas_rate_override is None or yearly_btu_override is None:
                raise HTTPException(status_code=400, detail="Gas manual mode requires gas_rate_override + yearly_btu_override.")
            gas_data = {
                "cost_per_btu": round_to(float(gas_rate_override), 10),
                "yearly_btu_usage": round_to(float(yearly_btu_override), 2),
                "source": "manual",
                "notes": ["Used manual gas values."],
            }
        else:
            if gas_text is None:
                raise HTTPException(status_code=400, detail="Gas pdf mode requires gas_pdf with extractable text.")
            parsed = parse_gas_text(gas_text)
            gas_data = {**parsed, "source": "pdf"}

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Build payload + summary + ranked options
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

    processing_summary = build_processing_summary(normalized_payload)
    ranked_options = to_ranked_json(years_in_home)

    # Single final response (no duplicated “received_fields” that repeats normalized_payload)
    return build_analysis_result(
        normalized_payload=normalized_payload,
        processing_summary=processing_summary,
        ranked_options=ranked_options,
        electricity_parse={
            "source": electric_data["source"],
            "notes": electric_data.get("notes", []),
            "pdf_text_preview": electricity_text[:500] if electricity_text else None,
        },
        gas_parse={
            "source": gas_data["source"],
            "notes": gas_data.get("notes", []),
            "pdf_text_preview": gas_text[:500] if gas_text else None,
        },
        modes={
            "electricity_mode": electricity_mode,
            "gas_mode": gas_mode,
        },
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("BACKEND_HOST", "127.0.0.1"),
        port=int(os.getenv("BACKEND_PORT", "8000")),
        reload=True,
    )