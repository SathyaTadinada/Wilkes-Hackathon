import type {
  HomeAnalysisRequest,
  RankingResponse,
  RetrofitOption,
  SupportedCity,
} from "@/lib/types";

type SeedOption = {
  name: string;
  baseCost: number;
  baseSavings: number;
  baseFeasibility: 1 | 2 | 3;
  timeEstimate: string;
};

const SEED_OPTIONS: SeedOption[] = [
  {
    name: "Air sealing + attic insulation",
    baseCost: 2800,
    baseSavings: 440,
    baseFeasibility: 3,
    timeEstimate: "1-2 days",
  },
  {
    name: "Smart thermostat",
    baseCost: 240,
    baseSavings: 95,
    baseFeasibility: 3,
    timeEstimate: "1-2 hours",
  },
  {
    name: "Heat pump HVAC upgrade",
    baseCost: 9800,
    baseSavings: 1250,
    baseFeasibility: 2,
    timeEstimate: "2-4 days",
  },
  {
    name: "Heat pump water heater",
    baseCost: 3200,
    baseSavings: 280,
    baseFeasibility: 2,
    timeEstimate: "1 day",
  },
  {
    name: "Rooftop solar",
    baseCost: 15500,
    baseSavings: 1450,
    baseFeasibility: 2,
    timeEstimate: "2-5 days",
  },
  {
    name: "Window weatherization / selective upgrades",
    baseCost: 5200,
    baseSavings: 360,
    baseFeasibility: 2,
    timeEstimate: "1-3 days",
  },
  {
    name: "Enroll in demand-response utility program",
    baseCost: 0,
    baseSavings: 85,
    baseFeasibility: 3,
    timeEstimate: "Same day",
  },
];

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function cityFactor(city: SupportedCity): number {
  switch (city) {
    case "Ogden":
      return 1.06;
    case "Salt Lake City":
      return 1;
    case "Provo":
      return 0.97;
  }
}

function budgetCostCeiling(
  budget: HomeAnalysisRequest["budget"],
  sqft: number,
): number {
  const baseline = Math.max(2500, sqft * 3);

  switch (budget) {
    case "low":
      return baseline;
    case "medium":
      return baseline * 2.2;
    case "high":
      return baseline * 5;
  }
}

function priorityScoreBoost(
  optionName: string,
  request: HomeAnalysisRequest,
  paybackYears: number,
): number {
  switch (request.priority) {
    case "lowest_upfront_cost":
      if (
        optionName.includes("thermostat") ||
        optionName.includes("demand-response") ||
        optionName.includes("Air sealing")
      ) {
        return 14;
      }
      return 0;

    case "fastest_payback":
      return clamp(12 - paybackYears, 0, 12);

    case "max_long_term_savings":
      if (
        optionName.includes("solar") ||
        optionName.includes("Heat pump HVAC") ||
        optionName.includes("Air sealing")
      ) {
        return 16;
      }
      return 4;

    case "lower_emissions":
      if (
        optionName.includes("Heat pump") ||
        optionName.includes("solar") ||
        optionName.includes("demand-response")
      ) {
        return 15;
      }
      return 3;
  }
}

function compatibilityMultiplier(
  optionName: string,
  request: HomeAnalysisRequest,
): number {
  let multiplier = 1;

  if (
    optionName.includes("Heat pump HVAC") &&
    request.heating_type === "electric_resistance"
  ) {
    multiplier += 0.22;
  }

  if (
    optionName.includes("Heat pump HVAC") &&
    request.cooling_type === "none"
  ) {
    multiplier += 0.12;
  }

  if (
    optionName.includes("Smart thermostat") &&
    request.heating_type === "unknown"
  ) {
    multiplier -= 0.1;
  }

  if (
    optionName.includes("Rooftop solar") &&
    request.monthly_electric_bill < 70
  ) {
    multiplier -= 0.15;
  }

  if (
    optionName.includes("Window weatherization") &&
    request.home_type === "condo"
  ) {
    multiplier -= 0.08;
  }

  return clamp(multiplier, 0.7, 1.35);
}

function buildReason(
  optionName: string,
  request: HomeAnalysisRequest,
  paybackYears: number,
): string {
  const city = request.location.supportedCity;

  if (optionName.includes("Air sealing")) {
    return `Strong envelope upgrade for ${city}; good year-round heating and cooling reduction with manageable installation scope.`;
  }

  if (optionName.includes("thermostat")) {
    return `Low-cost HVAC control upgrade with quick implementation and a short payback of about ${paybackYears.toFixed(1)} years.`;
  }

  if (optionName.includes("Heat pump HVAC")) {
    return `High-impact HVAC replacement that ranks well when current heating/cooling is less efficient or when the user prioritizes long-term savings.`;
  }

  if (optionName.includes("Heat pump water heater")) {
    return `Moderate-cost electrification step that can reduce water-heating energy use without requiring a full HVAC replacement.`;
  }

  if (optionName.includes("solar")) {
    return `Best fit when electric usage is high and the user can handle a larger upfront investment for long-term bill reduction.`;
  }

  if (optionName.includes("Window weatherization")) {
    return `Envelope comfort improvement with moderate savings; especially useful when drafts or poor insulation are likely.`;
  }

  return `Very low-friction program option with little to no upfront cost and immediate participation potential.`;
}

export function buildDemoRanking(
  request: HomeAnalysisRequest,
): RankingResponse {
  const city = request.location.supportedCity ?? "Salt Lake City";
  const electricAndGas =
    request.monthly_electric_bill + (request.monthly_gas_bill ?? 0);

  const annualBillEstimate = electricAndGas * 12;
  const billScale = clamp(annualBillEstimate / 2200, 0.7, 1.6);
  const costCeiling = budgetCostCeiling(request.budget, request.sqft);
  const climateFactor = cityFactor(city);

  const rankedOptions: RetrofitOption[] = SEED_OPTIONS.map((seed) => {
    const savingsMultiplier =
      billScale *
      climateFactor *
      compatibilityMultiplier(seed.name, request);

    const annualSavings = Math.round(seed.baseSavings * savingsMultiplier);
    const upfrontCost = Math.round(
      seed.baseCost *
        (request.sqft > 2500 ? 1.12 : request.sqft < 1400 ? 0.92 : 1),
    );

    const paybackYears =
      annualSavings > 0
        ? Number((upfrontCost / annualSavings).toFixed(1))
        : 99;

    const affordabilityPenalty =
      upfrontCost > costCeiling
        ? clamp((upfrontCost - costCeiling) / 1200, 0, 18)
        : 0;

    const feasibilityScore = seed.baseFeasibility * 10;
    const savingsScore = clamp((annualSavings / 20), 0, 35);
    const paybackScore = clamp(18 - paybackYears, 0, 18);
    const priorityBoost = priorityScoreBoost(seed.name, request, paybackYears);

    const rawScore =
      feasibilityScore +
      savingsScore +
      paybackScore +
      priorityBoost -
      affordabilityPenalty;

    const score = Math.round(clamp(rawScore, 5, 99));

    return {
      name: seed.name,
      score,
      upfront_cost: upfrontCost,
      annual_savings: annualSavings,
      payback_years: paybackYears,
      time_estimate: seed.timeEstimate,
      feasibility:
        seed.baseFeasibility === 3
          ? "High"
          : seed.baseFeasibility === 2
            ? "Medium"
            : "Low",
      reason: buildReason(seed.name, request, paybackYears),
    };
  }).sort((a, b) => b.score - a.score);

  return {
    ranked_options: rankedOptions,
    assumptions: [
      `City-level climate and utility assumptions were used for ${city}.`,
      "Only the city is extracted from the address right now; the full address is preserved for future geocoding or utility matching.",
      "This fallback mode uses a simple scoring model so the frontend stays demoable before the Python service is fully ready.",
      "Federal incentives are not hard-coded into the score in this demo fallback.",
    ],
    source: "demo-fallback",
  };
}