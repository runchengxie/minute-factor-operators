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
export type FundamentalSnapshot = { schema_version: number; source: string; vintage: string; dataset: string; coverage: { date_start: string; date_end: string; tickers: string[]; tickers_count: number; representative_tickers: string[]; observations: number }; latest_cross_section: { metric: string; count: number; missing: number; p01: number | null; p25: number | null; p50: number | null; p75: number | null; p99: number | null }; validation: { all_market_computed: boolean; historical_ttm_window: number; complete_quarters_required: number; quarterly_rule: string; pit_date_field: string; report_period_field: string }; series: FundamentalSeries[]; notes: string[] }

export type FactorStatus = 'descriptive' | 'experimental' | 'validated'
export type FactorCoverage = { count: number; missing?: number; total?: number; ratio?: number }
export type FactorStatistics = { date?: string; count?: number; p01: number | null; p25: number | null; p50: number | null; p75: number | null; p99: number | null }
export type FactorSeriesPoint = { ticker: string; metric: string; dates: string[]; values: Array<number | null> }
export type FactorRecord = {
  id: string
  displayName: string
  displayNameCn?: string
  family: string
  subfamily?: string
  frequencyIn?: string
  frequencyOut?: string
  status: FactorStatus
  formula?: string
  formulaLatex?: string
  definition: string
  intuition?: string
  interpretationHigh?: string
  interpretationLow?: string
  inputFields?: string[]
  unit?: string
  transformHint?: string
  failureModes?: string[]
  sourceModule?: string
  coverage?: FactorCoverage
  statistics?: FactorStatistics
  series?: FactorSeriesPoint[]
}
export type ResearchContext = {
  source: string
  snapshotRange: string
  universe: string
  frequency: string
  pitStatus: string
  status: FactorStatus
  notes: string[]
}
export type ExplorerFilters = { query: string; family: string; frequency: string; status: '' | FactorStatus }
export type ExplorerSort = 'name' | 'coverage' | 'status'
