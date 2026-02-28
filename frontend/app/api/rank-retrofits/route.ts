import { NextResponse } from "next/server";
import type { UploadApiResponse } from "@/lib/types";

export const runtime = "nodejs";

function getString(fd: FormData, key: string): string {
  const value = fd.get(key);

  if (typeof value !== "string" || !value.trim()) {
    throw new Error(`Missing required field: ${key}`);
  }

  return value.trim();
}

function getOptionalNumber(fd: FormData, key: string): number | null {
  const value = fd.get(key);

  if (value === null) return null;
  if (typeof value !== "string" || !value.trim()) return null;

  const parsed = Number(value);

  if (!Number.isFinite(parsed) || parsed < 0) {
    throw new Error(`Invalid numeric field: ${key}`);
  }

  return parsed;
}

function getRequiredPositiveNumber(fd: FormData, key: string): number {
  const raw = getString(fd, key);
  const parsed = Number(raw);

  if (!Number.isFinite(parsed) || parsed <= 0) {
    throw new Error(`Invalid positive numeric field: ${key}`);
  }

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

    const address = getString(incoming, "address");
    const city = getString(incoming, "city");
    const state = getString(incoming, "state");
    const zip = getString(incoming, "zip");
    const yearsInHome = getRequiredPositiveNumber(incoming, "years_in_home");
    const averageSqFt = getRequiredPositiveNumber(incoming, "average_sq_ft");
    const heatingFuel = getString(incoming, "heating_fuel");
    const coolingFuel = getString(incoming, "cooling_fuel");
    const isElectricHeating =
      getString(incoming, "is_electric_heating") === "true";

    const electricityPdf = getOptionalPdf(incoming, "electricity_pdf");
    const gasPdf = getOptionalPdf(incoming, "gas_pdf");

    const electricRateOverride = getOptionalNumber(
      incoming,
      "electric_rate_override",
    );
    const yearlyKwhOverride = getOptionalNumber(
      incoming,
      "yearly_kwh_override",
    );
    const gasRateOverride = getOptionalNumber(incoming, "gas_rate_override");
    const yearlyBtuOverride = getOptionalNumber(incoming, "yearly_btu_override");

    const hasElectricOverrides =
      electricRateOverride !== null && yearlyKwhOverride !== null;

    const hasGasOverrides =
      gasRateOverride !== null && yearlyBtuOverride !== null;

    if (!electricityPdf && !hasElectricOverrides) {
      return NextResponse.json(
        {
          error:
            "Electricity data is incomplete. Upload an electricity PDF or provide both electric override fields.",
        },
        { status: 400 },
      );
    }

    if (!gasPdf && !hasGasOverrides) {
      return NextResponse.json(
        {
          error:
            "Gas data is incomplete. Upload a gas PDF or provide both gas override fields.",
        },
        { status: 400 },
      );
    }

    const backendUrl = process.env.BACKEND_ANALYSIS_URL?.trim();

    const submittedFields: UploadApiResponse["submitted_fields"] = {
      address,
      city,
      state,
      zip,
      years_in_home: yearsInHome,
      average_sq_ft: averageSqFt,
      is_electric_heating: isElectricHeating,
      heating_fuel: heatingFuel === "electric" ? "electric" : "gas",
      cooling_fuel: coolingFuel === "gas" ? "gas" : "electric",
      has_electricity_pdf: Boolean(electricityPdf),
      has_gas_pdf: Boolean(gasPdf),
      electric_rate_override: electricRateOverride,
      yearly_kwh_override: yearlyKwhOverride,
      gas_rate_override: gasRateOverride,
      yearly_btu_override: yearlyBtuOverride,
    };

    if (backendUrl) {
      const forward = new FormData();

      forward.append("address", address);
      forward.append("city", city);
      forward.append("state", state);
      forward.append("zip", zip);
      forward.append("years_in_home", String(yearsInHome));
      forward.append("average_sq_ft", String(averageSqFt));
      forward.append("is_electric_heating", String(isElectricHeating));
      forward.append("heating_fuel", submittedFields.heating_fuel);
      forward.append("cooling_fuel", submittedFields.cooling_fuel);

      if (electricRateOverride !== null) {
        forward.append("electric_rate_override", String(electricRateOverride));
      }
      if (yearlyKwhOverride !== null) {
        forward.append("yearly_kwh_override", String(yearlyKwhOverride));
      }
      if (gasRateOverride !== null) {
        forward.append("gas_rate_override", String(gasRateOverride));
      }
      if (yearlyBtuOverride !== null) {
        forward.append("yearly_btu_override", String(yearlyBtuOverride));
      }

      if (electricityPdf) {
        forward.append("electricity_pdf", electricityPdf, electricityPdf.name);
      }
      if (gasPdf) {
        forward.append("gas_pdf", gasPdf, gasPdf.name);
      }

      try {
        const backendResponse = await fetch(backendUrl, {
          method: "POST",
          body: forward,
          cache: "no-store",
        });

        const backendBody = await parseResponseBody(backendResponse);

        const response: UploadApiResponse = {
          ok: backendResponse.ok,
          source: "backend",
          submitted_fields: submittedFields,
          backend_response: backendBody,
          message: backendResponse.ok
            ? "Files and fields were forwarded to the backend."
            : "Backend was reached, but it returned a non-OK response.",
        };

        return NextResponse.json(response, {
          status: backendResponse.ok ? 200 : 502,
        });
      } catch {
        const response: UploadApiResponse = {
          ok: true,
          source: "mock",
          submitted_fields: submittedFields,
          backend_response: {
            note: "Backend forwarding failed, so the frontend returned a local fallback response.",
          },
          message:
            "Backend request failed. Returning a local mock response instead.",
        };

        return NextResponse.json(response);
      }
    }

    const response: UploadApiResponse = {
      ok: true,
      source: "mock",
      submitted_fields: submittedFields,
      backend_response: {
        received: true,
        note: "No BACKEND_ANALYSIS_URL is configured yet.",
      },
      message:
        "No backend is configured, so the frontend returned a local mock response.",
    };

    return NextResponse.json(response);
  } catch (error) {
    return NextResponse.json(
      {
        error:
          error instanceof Error ? error.message : "Could not process upload.",
      },
      { status: 400 },
    );
  }
}