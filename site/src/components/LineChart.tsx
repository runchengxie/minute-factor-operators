import ReactECharts from 'echarts-for-react'

export default function LineChart({ dates, series }: { dates: string[]; series: Array<{ name: string; values: Array<number | null>; color: string }> }) {
  if (!dates.length || !series.some((item) => item.values.some((value) => value !== null))) return <div className="chart-empty">暂无可绘制的数据</div>
  return <ReactECharts style={{ height: 300 }} option={{ animation: false, tooltip: { trigger: 'axis' }, legend: { textStyle: { color: '#a8b0bf' } }, grid: { left: 45, right: 20, top: 35, bottom: 35 }, xAxis: { type: 'category', data: dates, axisLabel: { color: '#788397', hideOverlap: true } }, yAxis: { type: 'value', axisLabel: { color: '#788397' }, splitLine: { lineStyle: { color: '#263043' } } }, series: series.map((item) => ({ name: item.name, type: 'line', showSymbol: false, connectNulls: false, data: item.values, lineStyle: { color: item.color, width: 2 }, itemStyle: { color: item.color } })) }} />
}
