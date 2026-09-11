import type { FundamentalCatalog, FundamentalSnapshot, Snapshot } from './types'

const required = ['schema_version', 'generated_at', 'source', 'datasets', 'factor_groups', 'factors', 'series', 'cross_section', 'jump_decomposition'] as const
const fundamentalRequired = ['schema_version', 'source', 'vintage', 'dataset', 'coverage', 'latest_cross_section', 'validation', 'series', 'notes'] as const

export async function loadSnapshot(): Promise<Snapshot> {
  const response = await fetch(`${import.meta.env.BASE_URL}data/factor-snapshot.json`)
  if (!response.ok) throw new Error(`无法加载研究快照（HTTP ${response.status}）`)
  const value: unknown = await response.json()
  if (!value || typeof value !== 'object') throw new Error('研究快照格式无效')
  for (const key of required) if (!(key in value)) throw new Error(`研究快照缺少字段：${key}`)
  return value as Snapshot
}

export function findSeries(snapshot: Snapshot, ticker: string, metric: string) {
  return snapshot.series.find((item) => item.ticker === ticker && item.metric === metric)
}

export async function loadFundamentalData(): Promise<{ catalog: FundamentalCatalog; snapshot: FundamentalSnapshot }> {
  const base = import.meta.env.BASE_URL
  const [catalogResponse, snapshotResponse] = await Promise.all([
    fetch(`${base}data/fundamental-factor-catalog.json`),
    fetch(`${base}data/fundamental-snapshot.json`),
  ])
  if (!catalogResponse.ok || !snapshotResponse.ok) throw new Error('基本面研究数据未能加载')
  const catalogValue: unknown = await catalogResponse.json()
  const snapshotValue: unknown = await snapshotResponse.json()
  if (!catalogValue || typeof catalogValue !== 'object' || !Array.isArray((catalogValue as { factors?: unknown }).factors)) throw new Error('基本面因子目录格式无效')
  if (!snapshotValue || typeof snapshotValue !== 'object') throw new Error('基本面研究快照格式无效')
  for (const key of fundamentalRequired) if (!(key in snapshotValue)) throw new Error(`基本面研究快照缺少字段：${key}`)
  return { catalog: catalogValue as FundamentalCatalog, snapshot: snapshotValue as FundamentalSnapshot }
}
