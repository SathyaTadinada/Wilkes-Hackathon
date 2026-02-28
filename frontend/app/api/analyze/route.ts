import { NextResponse } from "next/server";
import type { UploadApiResponse } from "@/lib/types";

export const runtime = "nodejs";

function getString(fd: FormData, key: string): string {
  const value = fd.get(key);
  if (typeof value !== "string" || !value.trim()) throw new Error(`Missing required field: ${key}`);
  return value.trim();
}

function getEnum<T extends string>(fd: FormData, key: string, allowed: readonly T[]): T {
  const value = getString(fd, key);
  if (!allowed.includes(value as T)) throw new Error(`Invalid ${key}: ${value}`);
  return value as T;
}

function getOptionalNumber(fd: FormData, key: string): number | null {
  const value = fd.get(key);
  if (value === null) return null;
  if (typeof value !== "string" || !value.trim()) return null;
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed < 0) throw new Error(`Invalid numeric field: ${key}`);
  return parsed;
}

function getRequiredPositiveNumber(fd: FormData, key: string): number {
  const raw = getString(fd, key);
  const parsed = Number(raw);
  if (!Number.isFinite(parsed) || parsed <= 0) throw new Error(`Invalid positive numeric field: ${key}`);
  return parsed;
}

function getOptionalPdf(fd: FormData, key: string): File | null {
  const value = fd.get(key);
  if (!(value instanceof File)) return null;
  if (value.size <= 0) return null;
  return value;
}

async function parseResponseBody(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

export async function POST(request: Request) {
  try {
    const incoming = await request.formData();

    // Address
    const address = getString(incoming, "address");
    const city = getString(incoming, "city");
    const state = getString(incoming, "state");
    const zip = getString(incoming, "zip");

    // Home info
    const yearsInHome = getRequiredPositiveNumber(incoming, "years_in_home");
    const averageSqFt = getRequiredPositiveNumber(incoming, "average_sq_ft");
    const heatingFuel = getEnum(incoming, "heating_fuel", ["gas", "electric"] as const);
    const coolingFuel = getEnum(incoming, "cooling_fuel", ["gas", "electric"] as const);
    const isElectricHeating = getString(incoming, "is_electric_heating") === "true";

    // Utility modes
    const electricityMode = getEnum(incoming, "electricity_mode", ["pdf", "manual"] as const);
    const gasMode = getEnum(incoming, "gas_mode", ["pdf", "manual"] as const);

    // Files
    const electricityPdf = getOptionalPdf(incoming, "electricity_pdf");
    const gasPdf = getOptionalPdf(incoming, "gas_pdf");

    // Manual fields
    const electricRate = getOptionalNumber(incoming, "electric_rate_override");
    const yearlyKwh = getOptionalNumber(incoming, "yearly_kwh_override");

    const gasRate = getOptionalNumber(incoming, "gas_rate_override");
    const yearlyBtu = getOptionalNumber(incoming, "yearly_btu_override");

    // Validation aligned with modes
    if (electricityMode === "pdf" && !electricityPdf) {
      return NextResponse.json({ error: "Electricity is set to PDF mode but no electricity PDF was uploaded." }, { status: 400 });
    }
    if (electricityMode === "manual" && (electricRate === null || yearlyKwh === null)) {
      return NextResponse.json({ error: "Electricity is set to manual mode. Provide both cost/kWh and yearly kWh." }, { status: 400 });
    }

    if (gasMode === "pdf" && !gasPdf) {
      return NextResponse.json({ error: "Gas is set to PDF mode but no gas PDF was uploaded." }, { status: 400 });
    }
    if (gasMode === "manual" && (gasRate === null || yearlyBtu === null)) {
      return NextResponse.json({ error: "Gas is set to manual mode. Provide both cost/BTU and yearly BTU." }, { status: 400 });
    }

    const submittedFields: UploadApiResponse["submitted_fields"] = {
      address,
      city,
      state,
      zip,
      years_in_home: yearsInHome,
      average_sq_ft: averageSqFt,
      is_electric_heating: isElectricHeating,
      heating_fuel: heatingFuel,
      cooling_fuel: coolingFuel,
      electricity_mode: electricityMode,
      gas_mode: gasMode,
      has_electricity_pdf: Boolean(electricityPdf),
      has_gas_pdf: Boolean(gasPdf),
      electric_rate_override: electricRate,
      yearly_kwh_override: yearlyKwh,
      gas_rate_override: gasRate,
      yearly_btu_override: yearlyBtu,
    };

    const backendUrl = process.env.BACKEND_ANALYSIS_URL?.trim();

    // If backend configured: forward multipart as-is (with files)
    if (backendUrl) {
      const forward = new FormData();

      forward.append("address", address);
      forward.append("city", city);
      forward.append("state", state);
      forward.append("zip", zip);
      forward.append("years_in_home", String(yearsInHome));
      forward.append("average_sq_ft", String(averageSqFt));
      forward.append("is_electric_heating", String(isElectricHeating));
      forward.append("heating_fuel", heatingFuel);
      forward.append("cooling_fuel", coolingFuel);

      forward.append("electricity_mode", electricityMode);
      forward.append("gas_mode", gasMode);

      if (electricRate !== null) forward.append("electric_rate_override", String(electricRate));
      if (yearlyKwh !== null) forward.append("yearly_kwh_override", String(yearlyKwh));

      if (gasRate !== null) forward.append("gas_rate_override", String(gasRate));
      if (yearlyBtu !== null) forward.append("yearly_btu_override", String(yearlyBtu));

      if (electricityPdf) forward.append("electricity_pdf", electricityPdf, electricityPdf.name);
      if (gasPdf) forward.append("gas_pdf", gasPdf, gasPdf.name);

      const backendResponse = await fetch(backendUrl, {
        method: "POST",
        body: forward,
        cache: "no-store",
      });

      const backendBody = await parseResponseBody(backendResponse);

      const payload: UploadApiResponse = {
        ok: backendResponse.ok,
        source: "backend",
        submitted_fields: submittedFields,
        backend_response: backendBody,
        message: backendResponse.ok
          ? "Forwarded to backend successfully."
          : "Backend responded with a non-OK status.",
      };

      return NextResponse.json(payload, { status: backendResponse.ok ? 200 : 502 });
    }

    // No backend -> mock response (still shaped like backend)
    const payload: UploadApiResponse = {
      ok: true,
      source: "mock",
      submitted_fields: submittedFields,
      backend_response: {
        ok: true,
        message: "No BACKEND_ANALYSIS_URL configured. Returning mock response from frontend.",
        received_fields: submittedFields,
        normalized_payload: null,
        processing_summary: null,
        ranked_options: [
          {
            name: "Air sealing + attic insulation",
            score: 92,
            upfront_cost: 1800,
            estimated_annual_savings: 420,
            simple_payback_years: 4.3,
            estimated_value_during_stay: 2400,
            reason: "Usually the most cost-effective first step; reduces heating/cooling loads.",
          },
          {
            name: "Smart thermostat",
            score: 84,
            upfront_cost: 250,
            estimated_annual_savings: 90,
            simple_payback_years: 2.8,
            estimated_value_during_stay: 650,
            reason: "Low-cost efficiency gain if schedules/temps are inconsistent.",
          },
          {
            name: "Heat pump water heater",
            score: 76,
            upfront_cost: 2400,
            estimated_annual_savings: 300,
            simple_payback_years: 8.0,
            estimated_value_during_stay: 600,
            reason: "High savings for electric resistance water heating; moderate payback.",
          },
        ],
      },
      message: "No backend configured; frontend returned a local mock response.",
    };

    return NextResponse.json(payload);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Could not process request." },
      { status: 400 },
    );
  }
}