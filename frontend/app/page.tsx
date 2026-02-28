import HomeAnalysisForm from "@/components/HomeAnalysisForm";

export default function HomePage() {
  return (
    <main className="page-shell">
      <div className="stack">
        <section className="page-card stack">
          <div>
            <h1 className="hero-title">Retrofit Analysis Input</h1>
            <p className="hero-subtitle">
              This frontend collects home data, parses address + utility bill
              information, and builds the exact payload your backend models need.
            </p>
          </div>

          <div className="notice-box">
            The bill parser is intentionally simple for MVP speed. If a pasted
            bill format is weird, use the manual override fields for the parsed
            rate/usage values.
          </div>
        </section>

        <section className="page-card">
          <HomeAnalysisForm />
        </section>
      </div>
    </main>
  );
}