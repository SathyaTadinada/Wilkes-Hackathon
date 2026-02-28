import HomeAnalysisForm from "@/components/HomeAnalysisForm";

export default function HomePage() {
  return (
    <main className="page-shell">
      <div className="stack">
        <section className="page-card stack">
          <div>
            <h1 className="hero-title">Retrofit Analyzer</h1>
            <p className="hero-subtitle">
              Enter your address and utility data (upload bills or manual values).
              We forward the payload to a Python backend that returns “next best retrofit” recommendations.
            </p>
          </div>

          <div className="notice-box">
            Tip: If bill parsing fails, switch that utility to “Manual entry” and submit
            rate + yearly usage values.
          </div>
        </section>

        <section className="page-card">
          <HomeAnalysisForm />
        </section>
      </div>
    </main>
  );
}