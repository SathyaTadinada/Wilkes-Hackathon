export const SUPPORTED_CITIES = [
  "Salt Lake City",
  "Ogden",
  "Provo",
] as const;

export type SupportedCity = (typeof SUPPORTED_CITIES)[number];

export const HOME_TYPES = [
  "single_family",
  "townhouse",
  "condo",
] as const;

export const HEATING_TYPES = [
  "gas_furnace",
  "electric_resistance",
  "heat_pump",
  "boiler",
  "unknown",
] as const;

export const COOLING_TYPES = [
  "central_ac",
  "evaporative_cooler",
  "heat_pump",
  "none",
  "unknown",
] as const;

export const BUDGET_OPTIONS = [
  "low",
  "medium",
  "high",
] as const;

export const PRIORITY_OPTIONS = [
  "lowest_upfront_cost",
  "fastest_payback",
  "max_long_term_savings",
  "lower_emissions",
] as const;

export type HomeType = (typeof HOME_TYPES)[number];
export type HeatingType = (typeof HEATING_TYPES)[number];
export type CoolingType = (typeof COOLING_TYPES)[number];
export type BudgetOption = (typeof BUDGET_OPTIONS)[number];
export type PriorityOption = (typeof PRIORITY_OPTIONS)[number];

export type HomeFormState = {
  address: string;
  sqft: string;
  home_type: HomeType;
  heating_type: HeatingType;
  cooling_type: CoolingType;
  monthly_electric_bill: string;
  monthly_gas_bill: string;
  budget: BudgetOption;
  priority: PriorityOption;
};

export type LocationData = {
  rawAddress: string;
  city: string | null;
  state: string | null;
  postalCode: string | null;
  supportedCity: SupportedCity | null;
};

export type HomeAnalysisRequest = {
  address: string;
  location: LocationData;
  sqft: number;
  home_type: HomeType;
  heating_type: HeatingType;
  cooling_type: CoolingType;
  monthly_electric_bill: number;
  monthly_gas_bill: number | null;
  budget: BudgetOption;
  priority: PriorityOption;
};

export type RetrofitOption = {
  name: string;
  score: number;
  upfront_cost: number;
  annual_savings: number;
  payback_years: number;
  time_estimate: string;
  feasibility: "High" | "Medium" | "Low";
  reason: string;
};

export type RankingResponse = {
  ranked_options: RetrofitOption[];
  assumptions: string[];
  source: "python" | "demo-fallback";
};