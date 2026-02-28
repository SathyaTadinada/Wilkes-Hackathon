export type FuelType = "gas" | "electric";

export type UploadFormState = {
  fullAddress: string;
  heatingFuel: FuelType;
  coolingFuel: FuelType;
  yearsInHome: string;
  approxSqft: string;

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