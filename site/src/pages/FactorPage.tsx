import LineChart from '../components/LineChart'
import MetricCard from '../components/MetricCard'
import { findSeries } from '../data'
import type { Snapshot } from '../types'

export default function FactorPage({ snapshot, factorName }: { snapshot: Snapshot; factorName: string }) {
  const factor = snapshot.factors.find((item) => item.name === factorName)
  if (!factor) return <main className="empty"><h1>未找到因子</h1><a href={import.meta.env.BASE_URL}>返回总览</a></main>
  const series = findSeries(snapshot, '000001', factor.name) ?? snapshot.series.find((item) => item.metric.includes(factor.name))
  const stats = snapshot.cross_section.find((item) => item.metric === factor.name)
  return <main className="page"><a className="back" href={import.meta.env.BASE_URL}>← 因子总览</a><section className="detail-head"><p className="eyebrow">{factor.family}</p><h1>{factor.name}</h1><p className="lede">{factor.meaning}</p><code>{factor.module}</code></section><div className="detail-grid"><section className="panel"><p className="eyebrow">DEFINITION</p><h2>如何计算</h2><div className="formula">{factor.formula}</div><p>{factor.meaning}。该指标由现有因子算子生成，供下游模型进行横截面比较或体制识别。</p></section><section className="panel"><p className="eyebrow">SNAPSHOT</p><h2>当前摘要</h2><div className="mini-metrics"><MetricCard label="P01" value={stats?.p01?.toFixed(3) ?? '—'} /><MetricCard label="中位数" value={stats?.p50?.toFixed(3) ?? '—'} /><MetricCard label="P99" value={stats?.p99?.toFixed(3) ?? '—'} /></div></section></div><section className="panel chart-panel"><div className="panel-head"><div><p className="eyebrow">REPRESENTATIVE SERIES</p><h2>000001 · {series?.metric ?? factor.name}</h2></div><span className="badge">42 DAYS</span></div>{series ? <LineChart dates={series.dates} series={[{ name: series.metric, values: series.values, color: '#ef8d5e' }]} /> : <div className="chart-empty">暂无该因子的快照数据</div>}</section></main>
}
