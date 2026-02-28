import type { LocationData, SupportedCity } from "@/lib/types";

function cleanAddress(value: string): string {
  return value.trim().replace(/\s+/g, " ");
}

function titleCase(value: string): string {
  return value
    .toLowerCase()
    .split(" ")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function detectSupportedCity(value: string): SupportedCity | null {
  const lower = value.toLowerCase();

  if (lower.includes("salt lake city")) return "Salt Lake City";
  if (lower.includes("ogden")) return "Ogden";
  if (lower.includes("provo")) return "Provo";

  return null;
}

export function extractLocationData(address: string): LocationData {
  const normalized = cleanAddress(address);

  if (!normalized) {
    return {
      rawAddress: "",
      city: null,
      state: null,
      postalCode: null,
      supportedCity: null,
    };
  }

  const supportedCity = detectSupportedCity(normalized);

  const commaParts = normalized
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean);

  let city: string | null = supportedCity;

  if (!city && commaParts.length >= 2) {
    city = titleCase(commaParts[1]);
  }

  const stateMatch = normalized.match(/,\s*([A-Z]{2})\b/i);
  const zipMatch = normalized.match(/\b\d{5}(?:-\d{4})?\b/);

  return {
    rawAddress: normalized,
    city,
    state: stateMatch ? stateMatch[1].toUpperCase() : null,
    postalCode: zipMatch ? zipMatch[0] : null,
    supportedCity,
  };
}