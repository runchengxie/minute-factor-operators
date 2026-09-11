import type { FundamentalCatalog, FundamentalSnapshot, Snapshot } from './types'

const required = ['schema_version', 'generated_at', 'source', 'datasets', 'factor_groups', 'factors', 'series', 'cross_section', 'jump_decomposition'] as const

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
  return { catalog: await catalogResponse.json() as FundamentalCatalog, snapshot: await snapshotResponse.json() as FundamentalSnapshot }
}
