import BarChart from '../components/BarChart'
import type { Snapshot } from '../types'

export default function JumpPage({ snapshot }: { snapshot: Snapshot }) {
  const row = snapshot.jump_decomposition[0]
  return <main className="page"><a className="back" href={import.meta.env.BASE_URL}>← 因子总览</a><section className="detail-head"><p className="eyebrow">JUMP DECOMPOSITION / 02</p><h1>波动不是一个数字。</h1><p className="lede">把已实现方差拆成连续波动与跳跃，再观察大跳跃和小跳跃的结构。</p></section><div className="jump-flow"><div><b>RV</b><span>已实现方差</span></div><i>−</i><div><b>IVhat</b><span>连续方差估计</span></div><i>=</i><div className="accent"><b>RJV</b><span>跳跃方差</span></div><i>→</i><div><b>RLJV + RSJV</b><span>大跳跃 + 小跳跃</span></div></div><section className="panel chart-panel"><div className="panel-head"><div><p className="eyebrow">EXAMPLE / {row?.ticker ?? '—'}</p><h2>{row?.date ?? '暂无日期'} 的分解</h2></div></div>{row ? <><BarChart labels={["RV", "IVhat", "RJV", "RLJV", "RSJV"]} values={[row.rv, row.ivhat, row.rjv, row.rljv, row.rsjv]} colors={["#8fa4c7", "#5cc8b0", "#ef8d5e", "#e3b55e", "#bc7bea"]} /><p className="annotation">RJV = RLJV + RSJV = {row.rjv?.toFixed(6)}</p></> : <div className="chart-empty">暂无分解数据</div>}</section></main>
}
