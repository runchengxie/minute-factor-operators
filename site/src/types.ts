export type Factor = { name: string; family: string; module: string; formula: string; meaning: string }
export type Series = { ticker: string; metric: string; dates: string[]; values: Array<number | null> }
export type JumpRow = { ticker: string; date: string; rv: number | null; ivhat: number | null; rjv: number | null; rljv: number | null; rsjv: number | null }
export type Snapshot = {
  schema_version: number; generated_at: string; source: 'demo' | 'parquet';
  datasets: Array<{ name: string; date_start: string; date_end: string; trading_days: number; tickers: number }>;
  factor_groups: Array<{ name: string; label: string; count: number }>;
  factors: Factor[]; series: Series[];
  cross_section: Array<{ metric: string; date: string; count: number; p01: number | null; p25: number | null; p50: number | null; p75: number | null; p99: number | null }>;
  jump_decomposition: JumpRow[];
}
export type FundamentalFactor = { id: string; name: string; family: string; priority: 'core' | 'supporting'; formula: string; meaning: string; data_requirements: string[] }
export type FundamentalCatalog = { schema_version: number; title: string; status: string; data_status: string; research_notes: string[]; factors: FundamentalFactor[] }
export type FundamentalSeries = { ticker: string; metric: string; dates: string[]; values: Array<number | null> }
export type FundamentalSnapshot = { schema_version: number; source: string; vintage: string; dataset: string; coverage: { date_start: string; date_end: string; tickers: string[]; observations: number }; series: FundamentalSeries[]; notes: string[] }
