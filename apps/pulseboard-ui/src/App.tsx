import { EventChart } from './EventChart';
import { useEvents } from './useEvents';

export function App() {
  const { data, loading, error, lastUpdated, refresh } = useEvents(10_000);

  return (
    <div className="app">
      <header>
        <h1>PulseBoard</h1>
        <div className="header-meta">
          {lastUpdated && (
            <span className="last-updated">
              Updated {lastUpdated.toLocaleTimeString()}
            </span>
          )}
          <button onClick={() => { void refresh(); }} className="refresh-btn">
            ↻ Refresh
          </button>
        </div>
      </header>

      <main>
        <section className="chart-section">
          <h2>Event Rate — last hour</h2>
          {loading && <p className="status">Loading…</p>}
          {error && <p className="status error">Error: {error}</p>}
          {!loading && !error && data && <EventChart data={data.data} />}
          {!loading && !error && data?.data.length === 0 && (
            <p className="status">No events yet — worker may still be starting up.</p>
          )}
        </section>
      </main>
    </div>
  );
}
