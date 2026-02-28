"use client";

import Link from "next/link";
import { loadUploadResult } from "@/lib/storage";
import type { BackendProofOfConceptResponse } from "@/lib/types";

function pretty(value: unknown): string {
  return JSON.stringify(value, null, 2);
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function parseBackendResponse(value: unknown): BackendProofOfConceptResponse | null {
  if (!isObject(value)) return null;
  return value as BackendProofOfConceptResponse;
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

export default function ResultsClient() {
  const result = loadUploadResult();

  if (!result) {
    return (
      <div className="stack">
        <div className="button-row">
          <Link href="/" className="secondary-button">
            Back to inputs
          </Link>
        </div>
        <div className="error-box">No upload result found. Please submit the form first.</div>
      </div>
    );
  }

  const backend = parseBackendResponse(result.backend_response);
  const normalized = backend?.normalized_payload ?? null;
  const summary = backend?.processing_summary ?? null;
  const rankedOptions = Array.isArray(backend?.ranked_options) ? backend!.ranked_options : [];

  return (
    <div className="stack">
      <div className="button-row">
        <Link href="/" className="secondary-button">
          Back to inputs
        </Link>
      </div>

      <div>
        <h1 className="hero-title">Results</h1>
        <p className="hero-subtitle">{backend?.message ?? result.message}</p>
      </div>

      <section className="page-card stack">
        <h2 className="section-title">Request status</h2>

        <div className="summary-grid">
          <div className="summary-card">
            <span className="summary-label">API source</span>
            <span className="summary-value">{result.source}</span>
          </div>

          <div className="summary-card">
            <span className="summary-label">API ok</span>
            <span className="summary-value">{result.ok ? "true" : "false"}</span>
          </div>

          <div className="summary-card">
            <span className="summary-label">Recommendations returned</span>
            <span className="summary-value">{rankedOptions.length > 0 ? "yes" : "no"}</span>
          </div>
        </div>
      </section>

      {summary ? (
        <section className="page-card stack">
          <h2 className="section-title">Processing summary</h2>

          <div className="summary-grid">
            <div className="summary-card">
              <span className="summary-label">Annual electric cost</span>
              <span className="summary-value">{formatCurrency(summary.estimated_annual_electric_cost)}</span>
            </div>
            <div className="summary-card">
              <span className="summary-label">Annual gas cost</span>
              <span className="summary-value">{formatCurrency(summary.estimated_annual_gas_cost)}</span>
            </div>
            <div className="summary-card">
              <span className="summary-label">Annual total</span>
              <span className="summary-value">{formatCurrency(summary.estimated_total_annual_energy_cost)}</span>
            </div>
          </div>
        </section>
      ) : null}

      {rankedOptions.length > 0 ? (
        <section className="page-card stack">
          <h2 className="section-title">Next best retrofits</h2>

          <div className="stack">
            {rankedOptions.map((option, index) => (
              <div key={`${option.name}-${index}`} className="summary-card">
                <div className="stack">
                  <div>
                    <strong>
                      #{index + 1} {option.name}
                    </strong>
                  </div>

                  <div className="badge-row">
                    <span className="badge">Score: {option.score}</span>
                    <span className="badge">Upfront: {formatCurrency(option.upfront_cost)}</span>
                    <span className="badge">Annual savings: {formatCurrency(option.estimated_annual_savings)}</span>
                    <span className="badge">Payback: {option.simple_payback_years} yrs</span>
                    <span className="badge">Value during stay: {formatCurrency(option.estimated_value_during_stay)}</span>
                  </div>

                  <div className="helper">{option.reason}</div>
                </div>
              </div>
            ))}
          </div>
        </section>
      ) : (
        <section className="page-card stack">
          <h2 className="section-title">Next best retrofits</h2>
          <div className="notice-box">No ranked options were returned.</div>
        </section>
      )}

      {normalized ? (
        <section className="page-card stack">
          <h2 className="section-title">Normalized payload</h2>
          <pre className="code-block">{pretty(normalized)}</pre>
        </section>
      ) : null}

      <section className="page-card stack">
        <h2 className="section-title">Raw backend response</h2>
        <pre className="code-block">{pretty(result.backend_response)}</pre>
      </section>
    </div>
  );
}