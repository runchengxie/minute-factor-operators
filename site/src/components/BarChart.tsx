import ReactECharts from 'echarts-for-react'

export default function BarChart({ labels, values, colors }: { labels: string[]; values: Array<number | null>; colors: string[] }) {
  if (!labels.length || !values.some((value) => value !== null)) return <div className="chart-empty">暂无可绘制的数据</div>
  return <ReactECharts style={{ height: 280 }} option={{ animation: false, tooltip: { trigger: 'axis' }, grid: { left: 55, right: 20, top: 20, bottom: 35 }, xAxis: { type: 'category', data: labels, axisLabel: { color: '#a8b0bf' } }, yAxis: { type: 'value', axisLabel: { color: '#788397' }, splitLine: { lineStyle: { color: '#263043' } } }, series: [{ type: 'bar', data: values.map((value, index) => ({ value, itemStyle: { color: colors[index] } })) }] }} />
}
