"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import ResultsPanel from "@/components/ResultsPanel";
import { decodeFormState, normalizeFormState } from "@/lib/form";
import type { RankingResponse } from "@/lib/types";

export default function ResultsPage() {
  const searchParams = useSearchParams();
  const searchKey = searchParams.toString();

  const form = useMemo(
    () => decodeFormState(searchParams),
    [searchKey, searchParams],
  );

  const normalized = useMemo(() => normalizeFormState(form), [form]);

  const [result, setResult] = useState<RankingResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    if (!normalized.ok) {
      setError(normalized.errors.join(" "));
      setResult(null);
      setLoading(false);
      return;
    }

    const controller = new AbortController();

    async function runAnalysis() {
      setLoading(true);
      setError("");

      try {
        const response = await fetch("/api/rank-retrofits", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(normalized.payload),
          signal: controller.signal,
          cache: "no-store",
        });

        if (!response.ok) {
          const text = await response.text();
          throw new Error(text || "Request failed.");
        }

        const data = (await response.json()) as RankingResponse;
        setResult(data);
      } catch (err) {
        if ((err as Error).name === "AbortError") return;

        setError(
          err instanceof Error
            ? err.message
            : "Something went wrong while generating rankings.",
        );
        setResult(null);
      } finally {
        setLoading(false);
      }
    }

    void runAnalysis();

    return () => controller.abort();
  }, [normalized]);

  return (
    <main className="page-shell">
      <div className="stack">
        <section className="page-card stack">
          <div className="button-row">
            <Link
              href={searchKey ? `/?${searchKey}` : "/"}
              className="secondary-button"
            >
              Back to inputs
            </Link>
          </div>

          <div>
            <h1 className="hero-title">Results</h1>
            <p className="hero-subtitle">
              The frontend is routing correctly, re-validating the query-backed
              form state, and then calling the frontend API endpoint to fetch
              ranked retrofit options.
            </p>
          </div>

          {loading ? (
            <div className="loading-box">
              Generating a ranked retrofit list…
            </div>
          ) : null}

          {!loading && error ? <div className="error-box">{error}</div> : null}

          {!loading && !error && normalized.ok && result ? (
            <ResultsPanel payload={normalized.payload} result={result} />
          ) : null}
        </section>
      </div>
    </main>
  );
}