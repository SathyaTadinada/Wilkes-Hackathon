import type { HomeAnalysisRequest, RankingResponse } from "@/lib/types";

type ResultsPanelProps = {
  payload: HomeAnalysisRequest;
  result: RankingResponse;
};

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

export default function ResultsPanel({
  payload,
  result,
}: ResultsPanelProps) {
  const detectedCity = payload.location.supportedCity ?? "Unknown";

  return (
    <div className="stack">
      <div>
        <h2 className="section-title">Ranked retrofit recommendations</h2>
        <p className="section-subtitle">
          These rankings are based on the form inputs plus the currently detected
          city. The full address stays attached to the payload for future
          expansion, but the scoring model is only using city-level logic for
          now.
        </p>
      </div>

      <div className="summary-grid">
        <div className="summary-card">
          <span className="summary-label">Detected city</span>
          <span className="summary-value">{detectedCity}</span>
        </div>

        <div className="summary-card">
          <span className="summary-label">Square footage</span>
          <span className="summary-value">
            {payload.sqft.toLocaleString()} sq ft
          </span>
        </div>

        <div className="summary-card">
          <span className="summary-label">Monthly electric</span>
          <span className="summary-value">
            {formatCurrency(payload.monthly_electric_bill)}
          </span>
        </div>

        <div className="summary-card">
          <span className="summary-label">Data source</span>
          <span className="summary-value">
            {result.source === "python" ? "Python backend" : "Demo fallback"}
          </span>
        </div>
      </div>

      <div className="results-list">
        {result.ranked_options.map((option, index) => (
          <article key={`${option.name}-${index}`} className="result-card">
            <div className="result-top">
              <div>
                <h3 className="result-title">
                  #{index + 1} {option.name}
                </h3>
                <p className="result-meta">{option.reason}</p>
              </div>

              <div className="score-pill">Score {option.score}</div>
            </div>

            <div className="chip-row">
              <span className="chip">
                Upfront: {formatCurrency(option.upfront_cost)}
              </span>
              <span className="chip">
                Annual savings: {formatCurrency(option.annual_savings)}
              </span>
              <span className="chip">
                Payback: {option.payback_years.toFixed(1)} years
              </span>
              <span className="chip">
                Install time: {option.time_estimate}
              </span>
              <span className="chip">
                Feasibility: {option.feasibility}
              </span>
            </div>
          </article>
        ))}
      </div>

      <div className="stack">
        <div className="divider" />
        <div>
          <h3 className="section-title">Assumptions used</h3>
        </div>
        <ul className="assumption-list">
          {result.assumptions.map((assumption, index) => (
            <li key={`${assumption}-${index}`}>{assumption}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}