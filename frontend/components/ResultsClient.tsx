"use client";

import Link from "next/link";
import { loadUploadResult } from "@/lib/storage";

function pretty(value: unknown): string {
  return JSON.stringify(value, null, 2);
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
        <div className="error-box">
          No upload result was found. Please submit the form first.
        </div>
      </div>
    );
  }

  return (
    <div className="stack">
      <div className="button-row">
        <Link href="/" className="secondary-button">
          Back to inputs
        </Link>
      </div>

      <div>
        <h1 className="hero-title">Upload Result</h1>
        <p className="hero-subtitle">{result.message}</p>
      </div>

      <section className="page-card stack">
        <h2 className="section-title">Submitted fields</h2>
        <pre className="code-block">{pretty(result.submitted_fields)}</pre>
      </section>

      <section className="page-card stack">
        <h2 className="section-title">Backend response</h2>
        <pre className="code-block">{pretty(result.backend_response)}</pre>
      </section>
    </div>
  );
}