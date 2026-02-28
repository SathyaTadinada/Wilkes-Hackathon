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
import type { UploadApiResponse, UploadFormState } from "@/lib/types";

export default function HomeAnalysisForm() {
  const router = useRouter();

  const [form, setForm] = useState<UploadFormState>(createDefaultUploadForm());
  const [electricityPdf, setElectricityPdf] = useState<File | null>(null);
  const [gasPdf, setGasPdf] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    const stored = loadUploadForm();
    if (stored) {
      setForm(stored);
    }
  }, []);

  const addressPreview = useMemo(() => {
    try {
      return parseFullAddress(form.fullAddress);
    } catch {
      return null;
    }
  }, [form.fullAddress]);

  function update<K extends keyof UploadFormState>(
    key: K,
    value: UploadFormState[K],
  ) {
    setForm((current) => ({
      ...current,
      [key]: value,
    }));
  }

  function parsePositive(rawValue: string, label: string): number {
    const parsed = Number(rawValue);
    if (!Number.isFinite(parsed) || parsed <= 0) {
      throw new Error(`${label} must be a number greater than 0.`);
    }
    return parsed;
  }

  function appendIfPresent(fd: FormData, key: string, value: string) {
    if (value.trim()) fd.append(key, value.trim());
  }

  function hasElectricOverrides(): boolean {
    return (
      form.electricRateOverride.trim().length > 0 &&
      form.electricUsageOverride.trim().length > 0
    );
  }

  function hasGasOverrides(): boolean {
    return (
      form.gasRateOverride.trim().length > 0 &&
      form.gasUsageOverride.trim().length > 0
    );
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    try {
      const parsedAddress = parseFullAddress(form.fullAddress);
      const yearsInHome = parsePositive(form.yearsInHome, "Years in home");
      const approxSqft = parsePositive(
        form.approxSqft,
        "Approximate square footage",
      );

      if (!electricityPdf && !hasElectricOverrides()) {
        throw new Error(
          "For electricity, upload a PDF or fill in both electric override fields.",
        );
      }

      if (!gasPdf && !hasGasOverrides()) {
        throw new Error(
          "For gas, upload a PDF or fill in both gas override fields.",
        );
      }

      const multipart = new FormData();

      multipart.append("address", parsedAddress.shortAddress);
      multipart.append("city", parsedAddress.city);
      multipart.append("state", parsedAddress.state);
      multipart.append("zip", parsedAddress.zip);
      multipart.append("years_in_home", String(yearsInHome));
      multipart.append("average_sq_ft", String(approxSqft));
      multipart.append(
        "is_electric_heating",
        String(form.heatingFuel === "electric"),
      );
      multipart.append("heating_fuel", form.heatingFuel);
      multipart.append("cooling_fuel", form.coolingFuel);

      appendIfPresent(
        multipart,
        "electric_rate_override",
        form.electricRateOverride,
      );
      appendIfPresent(
        multipart,
        "yearly_kwh_override",
        form.electricUsageOverride,
      );
      appendIfPresent(multipart, "gas_rate_override", form.gasRateOverride);
      appendIfPresent(multipart, "yearly_btu_override", form.gasUsageOverride);

      if (electricityPdf) {
        multipart.append(
          "electricity_pdf",
          electricityPdf,
          electricityPdf.name,
        );
      }

      if (gasPdf) {
        multipart.append("gas_pdf", gasPdf, gasPdf.name);
      }

      setSubmitting(true);
      setError("");

      const response = await fetch("/api/analyze-home-upload", {
        method: "POST",
        body: multipart,
        cache: "no-store",
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || "Upload request failed.");
      }

      const result = (await response.json()) as UploadApiResponse;

      saveUploadForm(form);
      saveUploadResult(result);
      router.push("/results");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not submit the form.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="stack">
      <div>
        <h2 className="section-title">Upload utility bills</h2>
        <p className="section-subtitle">
          The PDFs are sent to the backend for parsing. Manual overrides are
          optional and can be used if PDF extraction fails.
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
        </label>

        <div className="field field-full">
          <div className="badge-row">
            <span className={`badge ${addressPreview ? "good" : "warn"}`}>
              {addressPreview ? "Address parsed" : "Address not parsed yet"}
            </span>
            {addressPreview ? (
              <>
                <span className="badge">
                  Short: {addressPreview.shortAddress}
                </span>
                <span className="badge">City: {addressPreview.city}</span>
                <span className="badge">State: {addressPreview.state}</span>
                <span className="badge">ZIP: {addressPreview.zip}</span>
              </>
            ) : null}
          </div>
        </div>

        <label className="field">
          <span className="label">Electricity bill PDF</span>
          <input
            className="input"
            type="file"
            accept="application/pdf"
            onChange={(event) =>
              setElectricityPdf(event.target.files?.[0] ?? null)
            }
          />
        </label>

        <label className="field">
          <span className="label">Gas bill PDF</span>
          <input
            className="input"
            type="file"
            accept="application/pdf"
            onChange={(event) => setGasPdf(event.target.files?.[0] ?? null)}
          />
        </label>

        <label className="field">
          <span className="label">Heating fuel</span>
          <select
            className="select"
            value={form.heatingFuel}
            onChange={(event) =>
              update("heatingFuel", event.target.value as "gas" | "electric")
            }
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
            onChange={(event) =>
              update("coolingFuel", event.target.value as "gas" | "electric")
            }
          >
            <option value="gas">Gas</option>
            <option value="electric">Electric</option>
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
          <span className="label">Approximate square footage</span>
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

        <label className="field">
          <span className="label">Manual electric override: cost per kWh</span>
          <input
            className="input"
            type="number"
            min="0"
            step="0.000001"
            required={!electricityPdf}
            value={form.electricRateOverride}
            onChange={(event) =>
              update("electricRateOverride", event.target.value)
            }
            placeholder={
              electricityPdf ? "Optional" : "Required if no electricity PDF"
            }
          />
        </label>

        <label className="field">
          <span className="label">Manual electric override: yearly kWh</span>
          <input
            className="input"
            type="number"
            min="0"
            step="0.01"
            value={form.electricUsageOverride}
            onChange={(event) =>
              update("electricUsageOverride", event.target.value)
            }
            placeholder="Optional"
          />
          <input
            className="input"
            type="number"
            min="0"
            step="0.01"
            required={!electricityPdf}
            value={form.electricUsageOverride}
            onChange={(event) =>
              update("electricUsageOverride", event.target.value)
            }
            placeholder={
              electricityPdf ? "Optional" : "Required if no electricity PDF"
            }
          />
        </label>

        <label className="field">
          <span className="label">Manual gas override: cost per BTU</span>
          <input
            className="input"
            type="number"
            min="0"
            step="0.0000000001"
            required={!gasPdf}
            value={form.gasRateOverride}
            onChange={(event) => update("gasRateOverride", event.target.value)}
            placeholder={gasPdf ? "Optional" : "Required if no gas PDF"}
          />
        </label>

        <label className="field">
          <span className="label">Manual gas override: yearly BTU</span>
          <input
            className="input"
            type="number"
            min="0"
            step="0.01"
            required={!gasPdf}
            value={form.gasUsageOverride}
            onChange={(event) => update("gasUsageOverride", event.target.value)}
            placeholder={gasPdf ? "Optional" : "Required if no gas PDF"}
          />
        </label>
      </div>

      {error ? <div className="error-box">{error}</div> : null}

      <div className="button-row">
        <button type="submit" className="primary-button" disabled={submitting}>
          {submitting ? "Uploading..." : "Upload and analyze"}
        </button>
      </div>
    </form>
  );
}
