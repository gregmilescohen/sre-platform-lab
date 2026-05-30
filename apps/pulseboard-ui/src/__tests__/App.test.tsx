import { render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { App } from '../App';
import type { EventDataResponse } from '../types';

const MOCK_RESPONSE: EventDataResponse = {
  event_name: null,
  since: '2026-01-01T00:00:00Z',
  bucket: 'minute',
  data: [{ time_bucket: '2026-01-01T00:00:00Z', event_name: 'page_view', count: 3 }],
};

beforeEach(() => {
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: () => Promise.resolve(MOCK_RESPONSE),
  } as Response);
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('App', () => {
  it('renders the PulseBoard heading', () => {
    render(<App />);
    expect(screen.getByRole('heading', { name: 'PulseBoard' })).toBeInTheDocument();
  });

  it('renders the chart section heading', () => {
    render(<App />);
    expect(screen.getByText(/Event Rate/)).toBeInTheDocument();
  });

  it('shows loading text initially', () => {
    render(<App />);
    expect(screen.getByText('Loading…')).toBeInTheDocument();
  });

  it('shows error message on fetch failure', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('connection refused'));
    render(<App />);
    await screen.findByText(/Error: connection refused/);
  });
});
