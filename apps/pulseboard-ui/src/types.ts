export interface DataPoint {
  time_bucket: string;
  event_name: string;
  count: number;
}

export interface EventDataResponse {
  event_name: string | null;
  since: string;
  bucket: string;
  data: DataPoint[];
}

export interface ChartDataRow {
  time_bucket: string;
  [eventName: string]: string | number;
}
