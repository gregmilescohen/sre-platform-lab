import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useEvents } from '../useEvents';
import type { EventDataResponse } from '../types';

const MOCK_RESPONSE: EventDataResponse = {
  event_name: null,
  since: '2026-01-01T00:00:00Z',
  bucket: 'minute',
  data: [{ time_bucket: '2026-01-01T00:00:00Z', event_name: 'page_view', count: 5 }],
};

beforeEach(() => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: () => Promise.resolve(MOCK_RESPONSE),
  } as Response);
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.useRealTimers();
});

describe('useEvents', () => {
  it('starts in loading state', () => {
    const { result } = renderHook(() => useEvents(10_000));
    expect(result.current.loading).toBe(true);
    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it('fetches data on mount and clears loading', async () => {
    const { result } = renderHook(() => useEvents(10_000));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.data).toEqual(MOCK_RESPONSE);
    expect(result.current.error).toBeNull();
  });

  it('sets lastUpdated after successful fetch', async () => {
    const { result } = renderHook(() => useEvents(10_000));
    await waitFor(() => expect(result.current.lastUpdated).not.toBeNull());
    expect(result.current.lastUpdated).toBeInstanceOf(Date);
  });

  it('sets error on non-ok response', async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: false, status: 503 } as Response);
    const { result } = renderHook(() => useEvents(10_000));
    await waitFor(() => expect(result.current.error).toBe('HTTP 503'));
    expect(result.current.data).toBeNull();
  });

  it('sets error on network failure', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('network error'));
    const { result } = renderHook(() => useEvents(10_000));
    await waitFor(() => expect(result.current.error).toBe('network error'));
  });

  it('polls at the given interval', async () => {
    const { result } = renderHook(() => useEvents(5_000));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(global.fetch).toHaveBeenCalledTimes(1);

    await act(async () => { vi.advanceTimersByTime(5_000); });
    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(2));
  });

  it('refresh() triggers an additional fetch', async () => {
    const { result } = renderHook(() => useEvents(60_000));
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(global.fetch).toHaveBeenCalledTimes(1);

    await act(async () => { result.current.refresh(); });
    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(2));
  });
});
