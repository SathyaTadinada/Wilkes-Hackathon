import RetrofitForm from "@/components/RetrofitForm";

export default function HomePage() {
  return (
    <main className="page-shell">
      <div className="stack">
        <section className="page-card hero-grid">
          <div className="stack">
            <div>
              <h1 className="hero-title">Home Energy Retrofit Ranking MVP</h1>
              <p className="hero-subtitle">
                Enter a home profile, then get a ranked list of retrofit options
                based on simplified city-level assumptions for Salt Lake City,
                Ogden, and Provo. This frontend is already wired to talk to a
                Python backend later, but it also works right now with a built-in
                fallback scorer.
              </p>
            </div>

            <div className="info-grid">
              <div className="info-card">
                <span className="info-label">Step 1</span>
                <span className="info-value">Collect the home inputs</span>
              </div>
              <div className="info-card">
                <span className="info-label">Step 2</span>
                <span className="info-value">Route to results page</span>
              </div>
              <div className="info-card">
                <span className="info-label">Step 3</span>
                <span className="info-value">Call API and rank options</span>
              </div>
            </div>
          </div>
        </section>

        <section className="page-card">
          <RetrofitForm />
        </section>
      </div>
    </main>
  );
}