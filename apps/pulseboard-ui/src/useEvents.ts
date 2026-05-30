import { useCallback, useEffect, useState } from 'react';
import type { EventDataResponse } from './types';

export interface UseEventsResult {
  data: EventDataResponse | null;
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  refresh: () => void;
}

export function useEvents(intervalMs: number = 10_000): UseEventsResult {
  const [data, setData] = useState<EventDataResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch('/api/events?bucket=minute');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = (await res.json()) as EventDataResponse;
      setData(json);
      setError(null);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchData();
    const id = setInterval(() => { void fetchData(); }, intervalMs);
    return () => clearInterval(id);
  }, [fetchData, intervalMs]);

  return { data, loading, error, lastUpdated, refresh: fetchData };
}
