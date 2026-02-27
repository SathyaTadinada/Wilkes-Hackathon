import { extractLocationData } from "@/lib/location";
import type {
  HomeAnalysisRequest,
  HomeFormState,
  SupportedCity,
} from "@/lib/types";

type SearchParamsLike = {
  get(name: string): string | null;
};

export function createDefaultFormState(): HomeFormState {
  return {
    address: "",
    sqft: "",
    home_type: "single_family",
    heating_type: "gas_furnace",
    cooling_type: "central_ac",
    monthly_electric_bill: "",
    monthly_gas_bill: "",
    budget: "medium",
    priority: "fastest_payback",
  };
}

export function decodeFormState(searchParams: SearchParamsLike): HomeFormState {
  const defaults = createDefaultFormState();

  return {
    address: searchParams.get("address") ?? defaults.address,
    sqft: searchParams.get("sqft") ?? defaults.sqft,
    home_type:
      (searchParams.get("home_type") as HomeFormState["home_type"]) ??
      defaults.home_type,
    heating_type:
      (searchParams.get("heating_type") as HomeFormState["heating_type"]) ??
      defaults.heating_type,
    cooling_type:
      (searchParams.get("cooling_type") as HomeFormState["cooling_type"]) ??
      defaults.cooling_type,
    monthly_electric_bill:
      searchParams.get("monthly_electric_bill") ?? defaults.monthly_electric_bill,
    monthly_gas_bill:
      searchParams.get("monthly_gas_bill") ?? defaults.monthly_gas_bill,
    budget:
      (searchParams.get("budget") as HomeFormState["budget"]) ?? defaults.budget,
    priority:
      (searchParams.get("priority") as HomeFormState["priority"]) ??
      defaults.priority,
  };
}

export function encodeFormState(form: HomeFormState): URLSearchParams {
  const params = new URLSearchParams();

  params.set("address", form.address);
  params.set("sqft", form.sqft);
  params.set("home_type", form.home_type);
  params.set("heating_type", form.heating_type);
  params.set("cooling_type", form.cooling_type);
  params.set("monthly_electric_bill", form.monthly_electric_bill);
  params.set("monthly_gas_bill", form.monthly_gas_bill);
  params.set("budget", form.budget);
  params.set("priority", form.priority);

  return params;
}

function parseRequiredPositiveNumber(
  rawValue: string,
  label: string,
  errors: string[],
): number {
  const value = Number(rawValue);

  if (!Number.isFinite(value) || value <= 0) {
    errors.push(`${label} must be a number greater than 0.`);
    return 0;
  }

  return value;
}

function parseOptionalNonNegativeNumber(
  rawValue: string,
  label: string,
  errors: string[],
): number | null {
  if (!rawValue.trim()) return null;

  const value = Number(rawValue);

  if (!Number.isFinite(value) || value < 0) {
    errors.push(`${label} must be a number that is 0 or greater.`);
    return null;
  }

  return value;
}

export function normalizeFormState(
  form: HomeFormState,
):
  | { ok: true; payload: HomeAnalysisRequest; supportedCity: SupportedCity }
  | { ok: false; errors: string[] } {
  const errors: string[] = [];

  if (!form.address.trim()) {
    errors.push("Address is required.");
  }

  const location = extractLocationData(form.address);

  if (!location.supportedCity) {
    errors.push(
      "For this MVP, the address must be in Salt Lake City, Ogden, or Provo.",
    );
  }

  const sqft = parseRequiredPositiveNumber(form.sqft, "Square footage", errors);
  const monthlyElectricBill = parseRequiredPositiveNumber(
    form.monthly_electric_bill,
    "Monthly electric bill",
    errors,
  );
  const monthlyGasBill = parseOptionalNonNegativeNumber(
    form.monthly_gas_bill,
    "Monthly gas bill",
    errors,
  );

  if (errors.length > 0 || !location.supportedCity) {
    return { ok: false, errors };
  }

  return {
    ok: true,
    supportedCity: location.supportedCity,
    payload: {
      address: location.rawAddress,
      location,
      sqft,
      home_type: form.home_type,
      heating_type: form.heating_type,
      cooling_type: form.cooling_type,
      monthly_electric_bill: monthlyElectricBill,
      monthly_gas_bill: monthlyGasBill,
      budget: form.budget,
      priority: form.priority,
    },
  };
}