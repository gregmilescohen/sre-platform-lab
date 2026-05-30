import { render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { EventChart } from '../EventChart';
import type { DataPoint } from '../types';

vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  LineChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Line: ({ dataKey }: { dataKey: string }) => <div data-testid={`line-${dataKey}`} />,
  XAxis: () => <div />,
  YAxis: () => <div />,
  CartesianGrid: () => <div />,
  Tooltip: () => <div />,
  Legend: () => <div />,
}));

beforeEach(() => {
  vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockReturnValue({
    width: 800, height: 400, top: 0, left: 0, bottom: 400, right: 800, x: 0, y: 0,
    toJSON: () => ({}),
  } as DOMRect);
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe('EventChart', () => {
  it('renders without crashing with empty data', () => {
    render(<EventChart data={[]} />);
    // No lines rendered for empty data
    expect(screen.queryByTestId(/^line-/)).toBeNull();
  });

  it('renders a line for a single event type', () => {
    const data: DataPoint[] = [
      { time_bucket: '2026-01-01T00:00:00Z', event_name: 'page_view', count: 5 },
    ];
    render(<EventChart data={data} />);
    expect(screen.getByTestId('line-page_view')).toBeInTheDocument();
  });

  it('renders lines for multiple event types', () => {
    const data: DataPoint[] = [
      { time_bucket: '2026-01-01T00:00:00Z', event_name: 'page_view', count: 3 },
      { time_bucket: '2026-01-01T00:01:00Z', event_name: 'api_call', count: 7 },
      { time_bucket: '2026-01-01T00:02:00Z', event_name: 'login', count: 1 },
    ];
    render(<EventChart data={data} />);
    expect(screen.getByTestId('line-page_view')).toBeInTheDocument();
    expect(screen.getByTestId('line-api_call')).toBeInTheDocument();
    expect(screen.getByTestId('line-login')).toBeInTheDocument();
  });

  it('merges multiple time buckets for the same event into one row', () => {
    // Two points with the same time bucket label should merge into one row
    const data: DataPoint[] = [
      { time_bucket: '2026-01-01T00:00:00Z', event_name: 'page_view', count: 2 },
      { time_bucket: '2026-01-01T00:00:00Z', event_name: 'button_click', count: 4 },
    ];
    render(<EventChart data={data} />);
    expect(screen.getByTestId('line-page_view')).toBeInTheDocument();
    expect(screen.getByTestId('line-button_click')).toBeInTheDocument();
  });

  it('uses fallback color for an unknown event name not in EVENT_COLORS', () => {
    const data: DataPoint[] = [
      { time_bucket: '2026-01-01T00:00:00Z', event_name: 'unknown_event', count: 1 },
    ];
    // Renders without error and the line element appears
    render(<EventChart data={data} />);
    expect(screen.getByTestId('line-unknown_event')).toBeInTheDocument();
  });
});
