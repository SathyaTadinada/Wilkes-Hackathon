export type FuelType = "gas" | "electric";
export type UtilityMode = "pdf" | "manual";

export type UploadFormState = {
  fullAddress: string;

  heatingFuel: FuelType;
  coolingFuel: FuelType;
  yearsInHome: string;
  approxSqft: string;

  electricityMode: UtilityMode;
  gasMode: UtilityMode;

  electricRateOverride: string;
  electricUsageOverride: string;

  gasRateOverride: string;
  gasUsageOverride: string;
};

export type ParsedAddress = {
  fullAddress: string;
  shortAddress: string;
  city: string;
  state: string;
  zip: string;
};

export type UploadApiResponse = {
  ok: boolean;
  source: "backend" | "mock";
  submitted_fields: {
    address: string;
    city: string;
    state: string;
    zip: string;

    years_in_home: number;
    average_sq_ft: number;

    is_electric_heating: boolean;
    heating_fuel: FuelType;
    cooling_fuel: FuelType;

    electricity_mode: UtilityMode;
    gas_mode: UtilityMode;

    has_electricity_pdf: boolean;
    has_gas_pdf: boolean;

    electric_rate_override: number | null;
    yearly_kwh_override: number | null;

    gas_rate_override: number | null;
    yearly_btu_override: number | null;
  };
  backend_response: unknown | null;
  message: string;
};

export type BackendRankedOption = {
  name: string;
  score: number;
  upfront_cost: number;
  estimated_annual_savings: number;
  simple_payback_years: number;
  estimated_value_during_stay: number;
  reason: string;
};

export type BackendNormalizedPayload = {
  address: string;
  city: string;
  state: string;
  zip: string;

  cost_per_kwh: number;
  yearly_kwh_usage: number;

  cost_per_btu: number;
  yearly_btu_usage: number;

  years_in_home: number;
  is_electric_heating: boolean;
  average_sq_ft: number;

  heating_fuel: FuelType;
  cooling_fuel: FuelType;
};

export type BackendProcessingSummary = {
  estimated_annual_electric_cost: number;
  estimated_annual_gas_cost: number;
  estimated_total_annual_energy_cost: number;
  estimated_monthly_energy_cost: number;
};

export type BackendProofOfConceptResponse = {
  ok?: boolean;
  message?: string;

  received_fields?: unknown;

  normalized_payload?: BackendNormalizedPayload | null;
  processing_summary?: BackendProcessingSummary | null;
  ranked_options?: BackendRankedOption[] | null;
};