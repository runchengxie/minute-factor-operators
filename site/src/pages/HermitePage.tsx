import { useState } from 'react'
import LineChart from '../components/LineChart'
import { findSeries } from '../data'
import type { Snapshot } from '../types'

export default function HermitePage({ snapshot }: { snapshot: Snapshot }) {
  const [ticker, setTicker] = useState(snapshot.series[0]?.ticker ?? '')
  const closeness = findSeries(snapshot, ticker, 'vol_rv_ts_closeness_60')
  const h3 = findSeries(snapshot, ticker, 'h_daily_close60_ts_h3_60')
  const h4 = findSeries(snapshot, ticker, 'h_daily_close60_ts_h4_60')
  const dates = closeness?.dates ?? h3?.dates ?? []
  return <main className="page"><a className="back" href={import.meta.env.BASE_URL}>← 因子总览</a><section className="detail-head"><p className="eyebrow">HERMITE REGIME / 03</p><h1>寻找分布的裂缝。</h1><p className="lede">h3 / h4 追踪非高斯性，ts closeness 将它压缩成一个可监控的体制稳定性信号。</p></section><section className="panel chart-panel"><div className="panel-head"><div><p className="eyebrow">ROLLING STATE</p><h2>股票：{ticker}</h2></div><select value={ticker} onChange={(event) => setTicker(event.target.value)}>{[...new Set(snapshot.series.map((item) => item.ticker))].map((item) => <option key={item}>{item}</option>)}</select></div><LineChart dates={dates} series={[{ name: 'ts closeness', values: closeness?.values ?? [], color: '#ef8d5e' }, { name: 'h3', values: h3?.values ?? [], color: '#5cc8b0' }, { name: 'h4', values: h4?.values ?? [], color: '#bc7bea' }]} /><div className="legend-note"><b>解释：</b>越接近 0 越接近高斯；越负表示偏离越明显。该指标是研究信号，不是交易建议。</div></section></main>
}
