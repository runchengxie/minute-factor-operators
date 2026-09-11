import type {
  Factor,
  FactorRecord,
  FactorSeriesPoint,
  FactorStatus,
  FundamentalCatalog,
  FundamentalFactor,
  FundamentalSnapshot,
  ResearchContext,
  ExplorerFilters,
  ExplorerSort,
  Snapshot,
} from './types'

type Metadata = Pick<FactorRecord, 'definition' | 'intuition' | 'interpretationHigh' | 'interpretationLow' | 'inputFields' | 'unit' | 'transformHint' | 'failureModes' | 'subfamily'>

const statusLabel: Record<FactorStatus, string> = { descriptive: '描述性快照', experimental: '实验性', validated: '已验证' }

const minuteMetadata: Record<string, Metadata> = {
  volume_volatility: { definition: '分钟成交量的变异系数，衡量日内成交活跃度的相对波动。', intuition: '成交量越不稳定，日内交易状态切换越明显。', interpretationHigh: '成交量波动更高', interpretationLow: '成交量更稳定', inputFields: ['minute volume'], unit: 'ratio', transformHint: '横截面偏态时可考虑 winsorize', failureModes: ['低成交量股票可能产生不稳定比率'], subfamily: 'volume' },
  star_volatility: { definition: '在成交量突变分钟上计算的收益波动，强调交易活动异常时的价格风险。', intuition: '放量伴随的波动可能反映信息到达或流动性冲击。', interpretationHigh: '放量时价格波动更强', interpretationLow: '放量时价格反应更平稳', inputFields: ['minute returns', 'minute volume'], unit: 'return variance', transformHint: '适合与日内成交量状态一起解释', failureModes: ['依赖成交量峰值阈值'], subfamily: 'volume / volatility' },
  illiquidity: { definition: '分钟级 Amihud 风格非流动性，按价格变动相对于成交金额衡量冲击成本。', intuition: '同样的成交额造成更大价格变化，意味着市场更难吸收交易。', interpretationHigh: '价格冲击成本更高', interpretationLow: '市场流动性更好', inputFields: ['minute returns', 'minute amount'], unit: 'return / amount', transformHint: '通常使用 log1p 或横截面 winsorize', failureModes: ['极低成交额会放大极端值'], subfamily: 'liquidity' },
  price_elasticity: { definition: '价格振幅相对成交额的弹性，描述交易活动对价格区间的影响。', intuition: '相同交易规模下振幅更大的股票具有更高的价格敏感度。', interpretationHigh: '单位成交额对应更大价格振幅', interpretationLow: '价格对交易活动更不敏感', inputFields: ['minute amplitude', 'minute amount'], unit: 'amplitude / amount', transformHint: '建议检查成交额为零和极端值', failureModes: ['盘中停牌或缺失分钟会改变分母'], subfamily: 'liquidity' },
  realized_variance: { definition: '单日分钟对数收益平方和，即实现方差。', intuition: '把日内价格变化聚合为可观测的 realized volatility proxy。', interpretationHigh: '当日实现波动更高', interpretationLow: '当日价格路径更平稳', inputFields: ['minute close'], unit: 'squared return', transformHint: '常用 log 变换观察分布', failureModes: ['微观结构噪声和分钟缺失会影响估计'], subfamily: 'realized moments' },
  realized_skewness: { definition: '分钟收益的实现偏度，描述日内收益分布的方向不对称性。', intuition: '正负尾部不对称可能反映单日买卖压力差异。', interpretationHigh: '右偏或正向尾部更强', interpretationLow: '左偏或负向尾部更强', inputFields: ['minute returns'], unit: 'dimensionless', transformHint: '对极端收益敏感', failureModes: ['少量分钟观测会使高阶矩不稳定'], subfamily: 'realized moments' },
  realized_kurtosis: { definition: '分钟收益的实现峰度，描述日内尾部和尖峰程度。', intuition: '更高峰度表示极端分钟收益出现得更频繁或更集中。', interpretationHigh: '尾部风险更明显', interpretationLow: '日内收益更接近轻尾分布', inputFields: ['minute returns'], unit: 'dimensionless', transformHint: '建议配合分位数和异常值诊断', failureModes: ['高阶矩对极端观测高度敏感'], subfamily: 'realized moments' },
  rv_pos: { definition: '日内正收益平方和，衡量上涨方向的实现波动贡献。', intuition: '将总实现方差拆成上涨与下跌方向，便于识别方向性风险。', interpretationHigh: '上涨方向波动贡献更高', interpretationLow: '上涨方向波动贡献更低', inputFields: ['minute returns'], unit: 'squared return', transformHint: '可与 rv_neg 比较方向不平衡', failureModes: ['依赖正负号阈值和分钟价格质量'], subfamily: 'signed volatility' },
  rv_neg: { definition: '日内负收益平方和，衡量下跌方向的实现波动贡献。', intuition: '下跌方向的波动集中可能反映下行压力或风险厌恶。', interpretationHigh: '下跌方向波动贡献更高', interpretationLow: '下跌方向波动贡献更低', inputFields: ['minute returns'], unit: 'squared return', transformHint: '可与 rv_pos 比较方向不平衡', failureModes: ['依赖正负号阈值和分钟价格质量'], subfamily: 'signed volatility' },
  ivhat: { definition: '对跳跃稳健的 tripower variation 方差估计，近似连续路径波动。', intuition: '先估计连续波动，再把实现方差中的跳跃部分分离出来。', interpretationHigh: '连续波动背景更强', interpretationLow: '连续波动背景更弱', inputFields: ['minute returns'], unit: 'variance', transformHint: '与 rjv 一起阅读', failureModes: ['样本量和价格跳点会影响高阶变差估计'], subfamily: 'jump decomposition' },
  rjv: { definition: '实现方差中扣除连续波动估计后的跳跃部分。', intuition: '捕捉不能由连续价格路径解释的离散价格变化。', interpretationHigh: '跳跃风险贡献更高', interpretationLow: '跳跃风险贡献更低', inputFields: ['realized variance', 'ivhat'], unit: 'variance', transformHint: '可看 jump share = rjv / rv', failureModes: ['连续波动估计误差会传导到跳跃值'], subfamily: 'jump decomposition' },
  rljv: { definition: '超过自适应阈值的大跳跃方差贡献。', intuition: '将跳跃风险中更极端的部分单独识别。', interpretationHigh: '大跳跃风险更集中', interpretationLow: '大跳跃风险更弱', inputFields: ['minute returns', 'gamma threshold'], unit: 'variance', transformHint: '与 rsjv 对照', failureModes: ['阈值选择会改变大跳跃数量'], subfamily: 'jump decomposition' },
  rsjv: { definition: '跳跃方差中未归入大跳跃的较小跳跃残差。', intuition: '补充大跳跃之外的频繁小幅离散变化。', interpretationHigh: '小跳跃贡献更高', interpretationLow: '小跳跃贡献更低', inputFields: ['rjv', 'rljv'], unit: 'variance', transformHint: '与 rljv 构成跳跃分解', failureModes: ['依赖 rjv 和大跳跃阈值的稳定性'], subfamily: 'jump decomposition' },
}

const hermiteMetadata: Metadata = {
  definition: '在滚动标准化因子上计算 Hermite H3/H4 分量或其能量，描述相对高斯参考分布的形状偏离。',
  intuition: '高阶形状信息可以补充均值和方差，识别不对称、厚尾或状态变化。',
  interpretationHigh: '对应的非高斯形状分量或偏离能量更高',
  interpretationLow: '对应的非高斯形状分量或偏离能量更低',
  inputFields: ['daily factor series'],
  unit: 'dimensionless',
  transformHint: 'closeness 是自定义 Hermite energy composite，不是正式正态性检验',
  failureModes: ['滚动窗口较短时高阶矩对异常值敏感'],
  subfamily: 'Hermite shape diagnostics',
}

function genericMinuteMetadata(factor: Factor): Metadata {
  const known = minuteMetadata[factor.name]
  if (known) return known
  return {
    definition: `${factor.name}：基于分钟 OHLCV 输入计算的日度微观结构统计量。原始含义为“${factor.meaning}”。`,
    intuition: '用于描述日内价格、成交量或跳跃状态的变化，不单独构成收益预测结论。',
    interpretationHigh: '该统计量相对更高',
    interpretationLow: '该统计量相对更低',
    inputFields: ['minute OHLCV'],
    unit: 'factor-specific',
    transformHint: '研究时应结合分布、缺失和极端值检查',
    failureModes: ['分钟缺失、低成交量和极端观测可能影响结果'],
    subfamily: 'microstructure',
  }
}

function minuteRecord(factor: Factor, snapshot: Snapshot): FactorRecord {
  const metadata = factor.name.startsWith('h_') || factor.name.startsWith('vol_') && factor.name.includes('_ts_') ? hermiteMetadata : genericMinuteMetadata(factor)
  const stats = snapshot.cross_section.filter((item) => item.metric === factor.name).sort((a, b) => b.date.localeCompare(a.date))[0]
  const series = snapshot.series.filter((item) => item.metric === factor.name)
  return {
    id: factor.name,
    displayName: factor.name,
    family: factor.family,
    subfamily: metadata.subfamily,
    frequencyIn: 'minute',
    frequencyOut: 'daily',
    status: 'descriptive',
    formula: factor.formula === '见实现模块' ? undefined : factor.formula,
    definition: metadata.definition,
    intuition: metadata.intuition,
    interpretationHigh: metadata.interpretationHigh,
    interpretationLow: metadata.interpretationLow,
    inputFields: metadata.inputFields,
    unit: metadata.unit,
    transformHint: metadata.transformHint,
    failureModes: metadata.failureModes,
    sourceModule: factor.module,
    coverage: stats ? { count: stats.count } : undefined,
    statistics: stats ? { date: stats.date, count: stats.count, p01: stats.p01, p25: stats.p25, p50: stats.p50, p75: stats.p75, p99: stats.p99 } : undefined,
    series,
  }
}

const fundamentalMetadata: Record<string, Metadata> = {
  standardized_operating_profit: { definition: '当前营业利润 TTM 相对公司自身过去六个 TTM 的标准化偏离。', intuition: '衡量经营利润是否进入相对自身历史的异常改善或恶化状态。', interpretationHigh: '当前经营利润高于自身历史状态', interpretationLow: '当前经营利润低于自身历史状态', inputFields: ['operate_profit', 'report_period', 'available_date'], unit: 'z-score', transformHint: '正式回测前需核验季度归属与公告日可得性', failureModes: ['季度重构、缺失季度和标准差过小会造成极端值'], subfamily: 'operating momentum' },
  operating_profit_yoy_zscore: { definition: '营业利润 TTM 同比增长相对历史波动的标准化强度。', intuition: '区分普通增长和相对公司自身历史更异常的增长。', interpretationHigh: '盈利同比改善更强', interpretationLow: '盈利同比恶化或改善更弱', inputFields: ['operate_profit', 'report_period', 'available_date'], unit: 'z-score', transformHint: '需严格使用 point-in-time 财报', failureModes: ['同比基数异常会放大结果'], subfamily: 'operating momentum' },
  operating_profit_acceleration: { definition: '营业利润增长率的二阶变化，衡量盈利改善速度是否进一步加快。', intuition: '盈利趋势的加速可能比单期增长更接近状态转换。', interpretationHigh: '盈利改善速度加快', interpretationLow: '盈利改善速度放缓', inputFields: ['operate_profit', 'report_period', 'available_date'], unit: 'growth change', transformHint: '对异常财报值敏感', failureModes: ['需要连续季度和可比口径'], subfamily: 'operating momentum' },
}

function fundamentalRecord(factor: FundamentalFactor, snapshot: FundamentalSnapshot): FactorRecord {
  const metadata = fundamentalMetadata[factor.id] ?? {
    definition: factor.meaning,
    intuition: '这是一个基本面描述性指标，当前页面不把它解释为已验证的收益预测信号。',
    interpretationHigh: '指标值相对更高，具体方向取决于公式',
    interpretationLow: '指标值相对更低，具体方向取决于公式',
    inputFields: factor.data_requirements,
    unit: 'factor-specific',
    transformHint: '使用 point-in-time 数据并检查缺失、极端值和滞后',
    failureModes: ['财报披露时点、口径变化和一次性项目可能影响解释'],
    subfamily: factor.priority === 'core' ? 'core research set' : 'supporting research set',
  }
  const stats = snapshot.latest_cross_section.metric === factor.id ? snapshot.latest_cross_section : undefined
  const series = snapshot.series.filter((item) => item.metric === factor.id)
  const total = stats?.count !== undefined ? stats.count + (snapshot.latest_cross_section.metric === factor.id ? snapshot.latest_cross_section.missing : 0) : undefined
  return {
    id: factor.id,
    displayName: factor.name,
    displayNameCn: factor.name,
    family: factor.family,
    subfamily: metadata.subfamily,
    frequencyIn: 'PIT quarterly reports',
    frequencyOut: 'disclosure-date snapshot',
    status: 'experimental',
    formula: factor.formula,
    definition: metadata.definition,
    intuition: metadata.intuition,
    interpretationHigh: metadata.interpretationHigh,
    interpretationLow: metadata.interpretationLow,
    inputFields: metadata.inputFields,
    unit: metadata.unit,
    transformHint: metadata.transformHint,
    failureModes: metadata.failureModes,
    sourceModule: snapshot.dataset,
    coverage: stats ? { count: stats.count, missing: snapshot.latest_cross_section.missing, total } : undefined,
    statistics: stats ? { count: stats.count, p01: stats.p01, p25: stats.p25, p50: stats.p50, p75: stats.p75, p99: stats.p99 } : undefined,
    series,
  }
}

export function adaptMinuteAndHermite(snapshot: Snapshot): FactorRecord[] {
  return snapshot.factors.map((factor) => minuteRecord(factor, snapshot))
}

export function adaptFundamentals(catalog: FundamentalCatalog, snapshot: FundamentalSnapshot): FactorRecord[] {
  return catalog.factors.map((factor) => fundamentalRecord(factor, snapshot))
}

export function toResearchRecords(snapshot: Snapshot, catalog: FundamentalCatalog, fundamental: FundamentalSnapshot): FactorRecord[] {
  return [...adaptMinuteAndHermite(snapshot), ...adaptFundamentals(catalog, fundamental)]
}

export function filterResearchRecords(records: FactorRecord[], filters: ExplorerFilters): FactorRecord[] {
  const query = filters.query.trim().toLocaleLowerCase()
  return records.filter((record) => {
    const searchable = [record.id, record.displayName, record.displayNameCn, record.family, record.subfamily, record.definition, ...(record.inputFields ?? [])].filter(Boolean).join(' ').toLocaleLowerCase()
    return (!query || searchable.includes(query)) && (!filters.family || record.family === filters.family) && (!filters.frequency || record.frequencyIn === filters.frequency) && (!filters.status || record.status === filters.status)
  })
}

export function sortResearchRecords(records: FactorRecord[], sort: ExplorerSort): FactorRecord[] {
  return [...records].sort((a, b) => {
    if (sort === 'coverage') return (b.coverage?.count ?? -1) - (a.coverage?.count ?? -1) || a.id.localeCompare(b.id)
    if (sort === 'status') return statusLabel[a.status].localeCompare(statusLabel[b.status]) || a.id.localeCompare(b.id)
    return a.displayName.localeCompare(b.displayName) || a.id.localeCompare(b.id)
  })
}

export function buildResearchContext(snapshot: Snapshot, fundamental: FundamentalSnapshot): ResearchContext {
  const dataset = snapshot.datasets[0]
  const pitReady = fundamental.validation.all_market_computed
  return {
    source: snapshot.source === 'demo' ? 'demo snapshot' : 'parquet snapshot',
    snapshotRange: dataset ? `${dataset.date_start} → ${dataset.date_end}` : `${fundamental.coverage.date_start} → ${fundamental.coverage.date_end}`,
    universe: dataset ? `${dataset.tickers} tickers` : `${fundamental.coverage.tickers_count} A-share tickers`,
    frequency: 'minute → daily · PIT quarterly → disclosure snapshot',
    pitStatus: pitReady ? `PIT available via ${fundamental.validation.pit_date_field}; initial calculation` : 'PIT validation incomplete',
    status: pitReady ? 'experimental' : 'descriptive',
    notes: [
      `Fundamental dataset: ${fundamental.dataset}; vintage ${fundamental.vintage}`,
      `TTM requires ${fundamental.validation.complete_quarters_required} complete quarters; historical window ${fundamental.validation.historical_ttm_window} TTM`,
      'Snapshot is for research display and is not a validated backtest result.',
    ],
  }
}

export function statusText(status: FactorStatus): string {
  return statusLabel[status]
}
