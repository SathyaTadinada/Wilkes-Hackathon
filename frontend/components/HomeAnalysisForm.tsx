"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { parseFullAddress } from "@/lib/address";
import {
  createDefaultUploadForm,
  loadUploadForm,
  saveUploadForm,
  saveUploadResult,
} from "@/lib/storage";
import type { UploadApiResponse, UploadFormState, UtilityMode } from "@/lib/types";

export default function HomeAnalysisForm() {
  const router = useRouter();

  const [form, setForm] = useState<UploadFormState>(createDefaultUploadForm());
  const [electricityPdf, setElectricityPdf] = useState<File | null>(null);
  const [gasPdf, setGasPdf] = useState<File | null>(null);

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const stored = loadUploadForm();
    if (stored) setForm(stored);
  }, []);

  const addressPreview = useMemo(() => {
    try {
      return parseFullAddress(form.fullAddress);
    } catch {
      return null;
    }
  }, [form.fullAddress]);

  function update<K extends keyof UploadFormState>(key: K, value: UploadFormState[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function parsePositive(rawValue: string, label: string): number {
    const parsed = Number(rawValue);
    if (!Number.isFinite(parsed) || parsed <= 0) throw new Error(`${label} must be > 0.`);
    return parsed;
  }

  function appendIfPresent(fd: FormData, key: string, value: string) {
    if (value.trim()) fd.append(key, value.trim());
  }

  function validateUtility(mode: UtilityMode, pdf: File | null, rate: string, usage: string, label: string) {
    if (mode === "pdf") {
      if (!pdf) throw new Error(`${label}: mode is PDF, but no PDF is selected.`);
      return;
    }
    // manual
    if (!rate.trim() || !usage.trim()) {
      throw new Error(`${label}: mode is Manual, but rate/usage are missing.`);
    }
    const r = Number(rate);
    const u = Number(usage);
    if (!Number.isFinite(r) || r <= 0) throw new Error(`${label}: rate must be a number > 0.`);
    if (!Number.isFinite(u) || u <= 0) throw new Error(`${label}: yearly usage must be a number > 0.`);
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    try {
      const parsedAddress = parseFullAddress(form.fullAddress);
      const yearsInHome = parsePositive(form.yearsInHome, "Years in home");
      const approxSqft = parsePositive(form.approxSqft, "Approximate square footage");

      validateUtility(
        form.electricityMode,
        electricityPdf,
        form.electricRateOverride,
        form.electricUsageOverride,
        "Electricity",
      );

      validateUtility(
        form.gasMode,
        gasPdf,
        form.gasRateOverride,
        form.gasUsageOverride,
        "Gas",
      );

      const multipart = new FormData();

      multipart.append("address", parsedAddress.shortAddress);
      multipart.append("city", parsedAddress.city);
      multipart.append("state", parsedAddress.state);
      multipart.append("zip", parsedAddress.zip);

      multipart.append("years_in_home", String(yearsInHome));
      multipart.append("average_sq_ft", String(approxSqft));
      multipart.append("is_electric_heating", String(form.heatingFuel === "electric"));
      multipart.append("heating_fuel", form.heatingFuel);
      multipart.append("cooling_fuel", form.coolingFuel);

      multipart.append("electricity_mode", form.electricityMode);
      multipart.append("gas_mode", form.gasMode);

      if (form.electricityMode === "manual") {
        appendIfPresent(multipart, "electric_rate_override", form.electricRateOverride);
        appendIfPresent(multipart, "yearly_kwh_override", form.electricUsageOverride);
      } else if (electricityPdf) {
        multipart.append("electricity_pdf", electricityPdf, electricityPdf.name);
      }

      if (form.gasMode === "manual") {
        appendIfPresent(multipart, "gas_rate_override", form.gasRateOverride);
        appendIfPresent(multipart, "yearly_btu_override", form.gasUsageOverride);
      } else if (gasPdf) {
        multipart.append("gas_pdf", gasPdf, gasPdf.name);
      }

      setSubmitting(true);
      setError("");

      const response = await fetch("/api/analyze", {
        method: "POST",
        body: multipart,
        cache: "no-store",
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || "Analyze request failed.");
      }

      const result = (await response.json()) as UploadApiResponse;

      saveUploadForm(form);
      saveUploadResult(result);
      router.push("/results");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not submit the form.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="stack">
      <div>
        <h2 className="section-title">Home + Utility Inputs</h2>
        <p className="section-subtitle">
          Choose “PDF” or “Manual” for each utility.
        </p>
      </div>

      <div className="form-grid">
        <label className="field field-full">
          <span className="label">Full address</span>
          <textarea
            className="textarea"
            value={form.fullAddress}
            onChange={(event) => update("fullAddress", event.target.value)}
            placeholder="123 Main St, Salt Lake City, UT 84101"
          />
          <span className="helper">
            Format: street, city, ST ZIP.
          </span>
        </label>

        <div className="field field-full">
          <div className="badge-row">
            <span className={`badge ${addressPreview ? "good" : "warn"}`}>
              {addressPreview ? "Address parsed" : "Address not parsed yet"}
            </span>
            {addressPreview ? (
              <>
                <span className="badge">Street: {addressPreview.shortAddress}</span>
                <span className="badge">City: {addressPreview.city}</span>
                <span className="badge">State: {addressPreview.state}</span>
                <span className="badge">ZIP: {addressPreview.zip}</span>
              </>
            ) : null}
          </div>
        </div>

        <label className="field">
          <span className="label">Heating fuel</span>
          <select
            className="select"
            value={form.heatingFuel}
            onChange={(event) => update("heatingFuel", event.target.value as any)}
          >
            <option value="gas">Gas</option>
            <option value="electric">Electric</option>
          </select>
        </label>

        <label className="field">
          <span className="label">Cooling fuel</span>
          <select
            className="select"
            value={form.coolingFuel}
            onChange={(event) => update("coolingFuel", event.target.value as any)}
          >
            <option value="electric">Electric</option>
            <option value="gas">Gas</option>
          </select>
        </label>

        <label className="field">
          <span className="label">Years in home</span>
          <input
            className="input"
            type="number"
            min="1"
            step="1"
            value={form.yearsInHome}
            onChange={(event) => update("yearsInHome", event.target.value)}
            placeholder="10"
          />
        </label>

        <label className="field">
          <span className="label">Approx. square footage</span>
          <input
            className="input"
            type="number"
            min="1"
            step="1"
            value={form.approxSqft}
            onChange={(event) => update("approxSqft", event.target.value)}
            placeholder="2200"
          />
        </label>

        {/* ELECTRICITY */}
        <div className="field field-full">
          <span className="label">Electricity input</span>
          <div className="radio-row">
            <label>
              <input
                type="radio"
                checked={form.electricityMode === "pdf"}
                onChange={() => update("electricityMode", "pdf")}
              />
              PDF upload
            </label>
            <label>
              <input
                type="radio"
                checked={form.electricityMode === "manual"}
                onChange={() => update("electricityMode", "manual")}
              />
              Manual entry
            </label>
          </div>
          <span className="helper">Pick one; only the relevant fields will be sent.</span>
        </div>

        {form.electricityMode === "pdf" ? (
          <label className="field field-full">
            <span className="label">Electricity bill PDF</span>
            <input
              className="input"
              type="file"
              accept="application/pdf"
              onChange={(event) => setElectricityPdf(event.target.files?.[0] ?? null)}
            />
            <span className="helper">
              Selected: {electricityPdf ? electricityPdf.name : "none"}
            </span>
          </label>
        ) : (
          <>
            <label className="field">
              <span className="label">Cost per kWh (USD)</span>
              <input
                className="input"
                type="number"
                min="0"
                step="0.000001"
                value={form.electricRateOverride}
                onChange={(event) => update("electricRateOverride", event.target.value)}
                placeholder="0.14"
              />
            </label>
            <label className="field">
              <span className="label">Yearly kWh</span>
              <input
                className="input"
                type="number"
                min="0"
                step="0.01"
                value={form.electricUsageOverride}
                onChange={(event) => update("electricUsageOverride", event.target.value)}
                placeholder="8500"
              />
            </label>
          </>
        )}

        {/* GAS */}
        <div className="field field-full">
          <span className="label">Gas input</span>
          <div className="radio-row">
            <label>
              <input
                type="radio"
                checked={form.gasMode === "pdf"}
                onChange={() => update("gasMode", "pdf")}
              />
              PDF upload
            </label>
            <label>
              <input
                type="radio"
                checked={form.gasMode === "manual"}
                onChange={() => update("gasMode", "manual")}
              />
              Manual entry
            </label>
          </div>
          <span className="helper">Pick one; only the relevant fields will be sent.</span>
        </div>

        {form.gasMode === "pdf" ? (
          <label className="field field-full">
            <span className="label">Gas bill PDF</span>
            <input
              className="input"
              type="file"
              accept="application/pdf"
              onChange={(event) => setGasPdf(event.target.files?.[0] ?? null)}
            />
            <span className="helper">Selected: {gasPdf ? gasPdf.name : "none"}</span>
          </label>
        ) : (
          <>
            <label className="field">
              <span className="label">Cost per BTU (USD)</span>
              <input
                className="input"
                type="number"
                min="0"
                step="0.0000000001"
                value={form.gasRateOverride}
                onChange={(event) => update("gasRateOverride", event.target.value)}
                placeholder="0.000012"
              />
            </label>
            <label className="field">
              <span className="label">Yearly BTU</span>
              <input
                className="input"
                type="number"
                min="0"
                step="0.01"
                value={form.gasUsageOverride}
                onChange={(event) => update("gasUsageOverride", event.target.value)}
                placeholder="65000000"
              />
            </label>
          </>
        )}
      </div>

      {error ? <div className="error-box">{error}</div> : null}

      <div className="button-row">
        <button type="submit" className="primary-button" disabled={submitting}>
          {submitting ? "Analyzing..." : "Analyze & get recommendations"}
        </button>
      </div>
    </form>
  );
}