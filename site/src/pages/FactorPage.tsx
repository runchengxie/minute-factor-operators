import { useMemo, useState } from 'react'
import LineChart from '../components/LineChart'
import MetricCard from '../components/MetricCard'
import { statusText } from '../research'
import type { FactorRecord, ResearchContext } from '../types'

function value(value: number | null | undefined) {
  return value === null || value === undefined || !Number.isFinite(value) ? '不可用' : value.toFixed(3)
}

export default function FactorPage({ factor, context }: { factor?: FactorRecord; context: ResearchContext }) {
  const [seriesKey, setSeriesKey] = useState('')
  const selectedSeries = useMemo(() => {
    if (!factor?.series?.length) return undefined
    return factor.series.find((item) => `${item.ticker}:${item.metric}` === seriesKey) ?? factor.series[0]
  }, [factor, seriesKey])

  if (!factor) return <main className="empty"><h1>未找到因子</h1><p>这个因子不在当前研究快照中。</p><a href={`${import.meta.env.BASE_URL}factors`}>返回因子目录</a></main>

  const stats = factor.statistics
  const metricOptions = factor.series ?? []
  return <main className="page factor-detail-page">
    <a className="back" href={`${import.meta.env.BASE_URL}factors`}>← 因子目录</a>
    <section className="detail-head"><p className="eyebrow">{factor.family}{factor.subfamily ? ` / ${factor.subfamily}` : ''}</p><h1>{factor.displayNameCn ?? factor.displayName}</h1><p className="factor-id">{factor.id}</p><p className="lede">{factor.definition}</p><div className="detail-tags"><span className={`status-pill status-${factor.status}`}>{statusText(factor.status)}</span><span className="tag">{factor.frequencyIn ?? '频率不可用'} → {factor.frequencyOut ?? '频率不可用'}</span><span className="tag">{factor.sourceModule ?? '来源不可用'}</span></div></section>
    <div className="detail-grid">
      <section className="panel"><p className="eyebrow">DEFINITION</p><h2>如何理解</h2><div className="formula">{factor.formula ?? '公式暂未结构化'}</div><p>{factor.intuition ?? '当前仅提供描述性定义，尚无额外经济解释。'}</p><dl className="research-dl"><div><dt>输入字段</dt><dd>{factor.inputFields?.join(' · ') ?? '不可用'}</dd></div><div><dt>单位</dt><dd>{factor.unit ?? '不可用'}</dd></div><div><dt>变换提示</dt><dd>{factor.transformHint ?? '不可用'}</dd></div></dl></section>
      <section className="panel"><p className="eyebrow">DATA QUALITY</p><h2>当前快照</h2><div className="mini-metrics"><MetricCard label="有效值" value={factor.coverage?.count?.toLocaleString() ?? '—'} note={factor.coverage?.missing !== undefined ? `缺失 ${factor.coverage.missing.toLocaleString()}` : '未提供全量计数'} /><MetricCard label="P01" value={value(stats?.p01)} /><MetricCard label="中位数" value={value(stats?.p50)} /><MetricCard label="P99" value={value(stats?.p99)} /></div><p className="panel-note">{context.source} · {context.snapshotRange}</p></section>
    </div>
    <section className="panel interpretation-grid"><div><p className="eyebrow">INTERPRETATION</p><h2>研究提示</h2><p><strong>高值：</strong>{factor.interpretationHigh ?? '方向尚未定义。'}</p><p><strong>低值：</strong>{factor.interpretationLow ?? '方向尚未定义。'}</p></div><div><p className="eyebrow">KNOWN LIMITS</p><h2>注意事项</h2>{factor.failureModes?.length ? <ul>{factor.failureModes.map((item) => <li key={item}>{item}</li>)}</ul> : <p>暂无结构化 failure modes。</p>}</div></section>
    <section className="panel chart-panel"><div className="panel-head"><div><p className="eyebrow">EXAMPLE SERIES</p><h2>{selectedSeries ? `${selectedSeries.ticker} · ${selectedSeries.metric}` : '没有可用的序列'}</h2></div>{metricOptions.length ? <label className="series-select"><span>选择序列</span><select value={seriesKey || (selectedSeries ? `${selectedSeries.ticker}:${selectedSeries.metric}` : '')} onChange={(event) => setSeriesKey(event.target.value)}>{metricOptions.map((item) => <option key={`${item.ticker}:${item.metric}`} value={`${item.ticker}:${item.metric}`}>{item.ticker} · {item.metric}</option>)}</select></label> : <span className="tag">序列不可用</span>}</div>{selectedSeries ? <><p className="chart-caption">这是当前快照中的示例序列，不代表全市场代表性股票。</p><LineChart dates={selectedSeries.dates} series={[{ name: selectedSeries.metric, values: selectedSeries.values, color: '#ef8d5e' }]} /></> : <div className="chart-empty">该因子当前没有可展示的 ticker 序列。</div>}</section>
    <section className="research-boundary"><p><strong>研究边界：</strong>{factor.status === 'validated' ? '该因子已有验证状态，但本页面仍只展示快照诊断。' : '当前页面展示的是描述性/实验性快照，不代表 IC、分层收益或交易策略已经验证。'}</p></section>
  </main>
}
