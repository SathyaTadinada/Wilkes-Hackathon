import type { ParsedAddress } from "@/lib/types";

function clean(value: string): string {
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

export function parseFullAddress(input: string): ParsedAddress {
  const normalized = clean(input);
  if (!normalized) throw new Error("A full address is required.");

  // expects "... , ST 12345"
  const tailMatch = normalized.match(/^(.*?)(?:,\s*|\s+)([A-Za-z]{2})\s+(\d{5}(?:-\d{4})?)$/);
  if (!tailMatch) {
    throw new Error('Address must end like: "123 Main St, Salt Lake City, UT 84101".');
  }

  const leftSide = clean(tailMatch[1]);
  const state = tailMatch[2].toUpperCase();
  const zip = tailMatch[3];

  const parts = leftSide.split(",").map(clean).filter(Boolean);
  if (parts.length < 2) {
    throw new Error("Address must include both street and city, separated by a comma.");
  }

  const city = titleCase(parts[parts.length - 1]);
  const shortAddress = parts.slice(0, -1).join(", ");
  if (!shortAddress) throw new Error("Could not extract the street address portion.");

  return { fullAddress: normalized, shortAddress, city, state, zip };
}