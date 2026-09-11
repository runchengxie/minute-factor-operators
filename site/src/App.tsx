import { useEffect, useState } from 'react'
import { loadFundamentalData, loadSnapshot } from './data'
import type { FundamentalCatalog, FundamentalSnapshot, Snapshot } from './types'
import OverviewPage from './pages/OverviewPage'
import FactorPage from './pages/FactorPage'
import JumpPage from './pages/JumpPage'
import HermitePage from './pages/HermitePage'
import FundamentalsPage from './pages/FundamentalsPage'

function pathView(snapshot: Snapshot, catalog: FundamentalCatalog, fundamental: FundamentalSnapshot) {
  const path = window.location.pathname.replace(import.meta.env.BASE_URL, '').replace(/^\//, '')
  if (path === '' || path === 'index.html') return <OverviewPage snapshot={snapshot} />
  if (path === 'jumps') return <JumpPage snapshot={snapshot} />
  if (path === 'hermite') return <HermitePage snapshot={snapshot} />
  if (path === 'fundamentals') return <FundamentalsPage catalog={catalog} snapshot={fundamental} />
  if (path.startsWith('factors/')) return <FactorPage snapshot={snapshot} factorName={decodeURIComponent(path.slice(8))} />
  return <main className="empty"><h1>找不到这个页面</h1><a href={import.meta.env.BASE_URL}>返回总览</a></main>
}

export default function App() {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null)
  const [fundamental, setFundamental] = useState<{ catalog: FundamentalCatalog; snapshot: FundamentalSnapshot } | null>(null)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => { Promise.all([loadSnapshot(), loadFundamentalData()]).then(([main, fundamentals]) => { setSnapshot(main); setFundamental(fundamentals) }).catch((reason: unknown) => setError(reason instanceof Error ? reason.message : '加载失败')) }, [])
  if (error) return <main className="empty"><h1>研究快照加载失败</h1><p>{error}</p><button onClick={() => window.location.reload()}>重试</button></main>
  if (!snapshot || !fundamental) return <main className="empty"><p>正在加载研究快照…</p></main>
  return <><header className="topbar"><a className="brand" href={import.meta.env.BASE_URL}>FACTOR RESEARCH <span>OBSERVATORY</span></a><nav><a href={`${import.meta.env.BASE_URL}jumps`}>跳跃分解</a><a href={`${import.meta.env.BASE_URL}hermite`}>Hermite 体制</a><a href={`${import.meta.env.BASE_URL}fundamentals`}>基本面因子</a></nav></header>{pathView(snapshot, fundamental.catalog, fundamental.snapshot)}<footer>factor-research-observatory · {snapshot.source === 'demo' ? 'Demo snapshot' : 'Parquet snapshot'} · 研究展示，不构成交易建议</footer></>
}
