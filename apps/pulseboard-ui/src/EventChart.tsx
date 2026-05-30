import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { ChartDataRow, DataPoint } from './types';

const EVENT_COLORS: Record<string, string> = {
  page_view: '#3b82f6',
  button_click: '#22c55e',
  api_call: '#f97316',
  search: '#a855f7',
  checkout: '#ec4899',
  login: '#14b8a6',
  error: '#ef4444',
};

function toChartRows(data: DataPoint[]): { rows: ChartDataRow[]; eventNames: string[] } {
  const rowMap = new Map<string, ChartDataRow>();
  const eventNames = new Set<string>();

  for (const point of data) {
    const label = new Date(point.time_bucket).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    });
    eventNames.add(point.event_name);
    const row = rowMap.get(label) ?? { time_bucket: label };
    row[point.event_name] = point.count;
    rowMap.set(label, row);
  }

  return { rows: Array.from(rowMap.values()), eventNames: Array.from(eventNames).sort() };
}

interface EventChartProps {
  data: DataPoint[];
}

export function EventChart({ data }: EventChartProps) {
  const { rows, eventNames } = toChartRows(data);

  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={rows} margin={{ top: 8, right: 24, left: 0, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis dataKey="time_bucket" tick={{ fill: '#9ca3af', fontSize: 11 }} />
        <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} allowDecimals={false} />
        <Tooltip
          contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', color: '#f9fafb' }}
        />
        <Legend wrapperStyle={{ color: '#9ca3af' }} />
        {eventNames.map((name) => (
          <Line
            key={name}
            type="monotone"
            dataKey={name}
            stroke={EVENT_COLORS[name] ?? '#6b7280'}
            dot={false}
            strokeWidth={2}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
