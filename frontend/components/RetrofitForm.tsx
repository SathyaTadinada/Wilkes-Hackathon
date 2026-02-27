"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { decodeFormState, encodeFormState, normalizeFormState } from "@/lib/form";
import { extractLocationData } from "@/lib/location";
import {
  BUDGET_OPTIONS,
  COOLING_TYPES,
  HEATING_TYPES,
  HOME_TYPES,
  PRIORITY_OPTIONS,
  type HomeFormState,
} from "@/lib/types";

const HOME_TYPE_LABELS: Record<(typeof HOME_TYPES)[number], string> = {
  single_family: "Single-family home",
  townhouse: "Townhouse",
  condo: "Condo",
};

const HEATING_LABELS: Record<(typeof HEATING_TYPES)[number], string> = {
  gas_furnace: "Gas furnace",
  electric_resistance: "Electric resistance",
  heat_pump: "Heat pump",
  boiler: "Boiler",
  unknown: "Unknown",
};

const COOLING_LABELS: Record<(typeof COOLING_TYPES)[number], string> = {
  central_ac: "Central AC",
  evaporative_cooler: "Evaporative cooler",
  heat_pump: "Heat pump",
  none: "None",
  unknown: "Unknown",
};

const BUDGET_LABELS: Record<(typeof BUDGET_OPTIONS)[number], string> = {
  low: "Low budget",
  medium: "Medium budget",
  high: "High budget",
};

const PRIORITY_LABELS: Record<(typeof PRIORITY_OPTIONS)[number], string> = {
  lowest_upfront_cost: "Lowest upfront cost",
  fastest_payback: "Fastest payback",
  max_long_term_savings: "Max long-term savings",
  lower_emissions: "Lower emissions",
};

export default function RetrofitForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const searchKey = searchParams.toString();

  const initialState = useMemo(
    () => decodeFormState(searchParams),
    [searchKey, searchParams],
  );

  const [form, setForm] = useState<HomeFormState>(initialState);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    setForm(initialState);
  }, [initialState]);

  const extracted = useMemo(
    () => extractLocationData(form.address),
    [form.address],
  );

  const supportedCity = extracted.supportedCity;

  function setField<K extends keyof HomeFormState>(
    key: K,
    value: HomeFormState[K],
  ) {
    setForm((current) => ({
      ...current,
      [key]: value,
    }));
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const normalized = normalizeFormState(form);

    if (!normalized.ok) {
      setError(normalized.errors.join(" "));
      return;
    }

    setError("");

    const params = encodeFormState(form);
    router.push(`/results?${params.toString()}`);
  }

  return (
    <form onSubmit={handleSubmit} className="stack">
      <div className="stack">
        <div>
          <h2 className="section-title">Home profile</h2>
          <p className="section-subtitle">
            The full address is collected now, but the app only uses the city
            for MVP ranking. That keeps the input flexible for future geocoding,
            utility lookups, and more detailed parsing later.
          </p>
        </div>

        <div className="form-grid">
          <label className="field field-full">
            <span className="label">Property address</span>
            <textarea
              className="textarea"
              value={form.address}
              onChange={(event) => setField("address", event.target.value)}
              placeholder="123 Main St, Salt Lake City, UT 84101"
            />
            <span className="helper">
              Current MVP support: Salt Lake City, Ogden, and Provo.
            </span>
          </label>

          <div className="field field-full">
            <div className="badge-row">
              <span className={`badge ${supportedCity ? "good" : "warn"}`}>
                {supportedCity
                  ? `Detected supported city: ${supportedCity}`
                  : "No supported city detected yet"}
              </span>

              {extracted.city && (
                <span className="badge">Parsed city: {extracted.city}</span>
              )}

              {extracted.state && (
                <span className="badge">State: {extracted.state}</span>
              )}

              {extracted.postalCode && (
                <span className="badge">ZIP: {extracted.postalCode}</span>
              )}
            </div>
          </div>

          <label className="field">
            <span className="label">Square footage</span>
            <input
              className="input"
              type="number"
              min="1"
              step="1"
              value={form.sqft}
              onChange={(event) => setField("sqft", event.target.value)}
              placeholder="2200"
            />
          </label>

          <label className="field">
            <span className="label">Home type</span>
            <select
              className="select"
              value={form.home_type}
              onChange={(event) =>
                setField("home_type", event.target.value as HomeFormState["home_type"])
              }
            >
              {HOME_TYPES.map((option) => (
                <option key={option} value={option}>
                  {HOME_TYPE_LABELS[option]}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span className="label">Current heating type</span>
            <select
              className="select"
              value={form.heating_type}
              onChange={(event) =>
                setField(
                  "heating_type",
                  event.target.value as HomeFormState["heating_type"],
                )
              }
            >
              {HEATING_TYPES.map((option) => (
                <option key={option} value={option}>
                  {HEATING_LABELS[option]}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span className="label">Current cooling type</span>
            <select
              className="select"
              value={form.cooling_type}
              onChange={(event) =>
                setField(
                  "cooling_type",
                  event.target.value as HomeFormState["cooling_type"],
                )
              }
            >
              {COOLING_TYPES.map((option) => (
                <option key={option} value={option}>
                  {COOLING_LABELS[option]}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span className="label">Monthly electric bill ($)</span>
            <input
              className="input"
              type="number"
              min="0"
              step="0.01"
              value={form.monthly_electric_bill}
              onChange={(event) =>
                setField("monthly_electric_bill", event.target.value)
              }
              placeholder="110"
            />
          </label>

          <label className="field">
            <span className="label">Monthly gas bill ($)</span>
            <input
              className="input"
              type="number"
              min="0"
              step="0.01"
              value={form.monthly_gas_bill}
              onChange={(event) => setField("monthly_gas_bill", event.target.value)}
              placeholder="65 (optional)"
            />
          </label>

          <label className="field">
            <span className="label">Budget</span>
            <select
              className="select"
              value={form.budget}
              onChange={(event) =>
                setField("budget", event.target.value as HomeFormState["budget"])
              }
            >
              {BUDGET_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {BUDGET_LABELS[option]}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            <span className="label">Primary goal</span>
            <select
              className="select"
              value={form.priority}
              onChange={(event) =>
                setField("priority", event.target.value as HomeFormState["priority"])
              }
            >
              {PRIORITY_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {PRIORITY_LABELS[option]}
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>

      {error ? <div className="error-box">{error}</div> : null}

      <div className="button-row">
        <button type="submit" className="primary-button">
          Generate ranked retrofit list
        </button>
      </div>
    </form>
  );
}