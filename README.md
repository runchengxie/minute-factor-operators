# minute-factor-operators

Alpha 因子计算算子 —— `guan-factor-research-framework` 的特征工程层。

对 A 股分钟级行情数据（OHLCV），计算波动率、跳跃、流动性及 Hermite 元因子，产出结构化的因子面板供下游 ML 模型消费。

## 目录结构

```
.
├── mf_volatility_32.py              # 基础因子：波动率 / 跳跃 / 流动性，32 个子因子
├── hermite_factor_meta.py           # 元因子：Hermite 多项式变换，12×4 = 48 个二阶特征
├── factor_results/                  # 因子输出目录（Parquet）
│   ├── mf_volatility_32/
│   └── hermite_factor_meta/
└── README.md
```

## 因子体系

### mf_volatility_32 — 基础因子

对每只股票、每个交易日，基于当日分钟 K 线计算 **32 个标量因子**，涵盖四个维度：

| 族 | 因子数 | 代表因子 | 说明 |
|---|---|---|---|
| F1105 波动率/跳跃 | 4 | `volume_volatility`, `star_volatility` | 成交量波动、星形波动 |
| F1107 流动性 | 3 | `illiquidity`, `price_elasticity` | Amihud 非流动性、价格弹性 |
| 微观结构 | 5 | `diff_abs_mean_volume`, `peak_count_1std` | 量变幅度、峰度计数 |
| 已实现矩 | 3 | `realized_variance`, `realized_skewness`, `realized_kurtosis` | 已实现方差/偏度/峰度 |
| 跳跃分解 | 17 | `ivhat`, `rjv`, `rljv`, `rsjv` | 三幂变差跳跃检测与分解 |

**跳跃检测** 实现了 Barndorff-Nielsen & Shephard 框架：用 tripower variation (`ivhat`) 估计对跳跃稳健的积分方差，将已实现方差分解为连续部分和跳跃部分 (`rjv = RV − IV`)，并进一步将跳跃分解为大跳跃 (`rljv`) 和小跳跃 (`rsjv`)。

### hermite_factor_meta — 元因子（算子之算子）

对 12 个已计算的基础因子做 **滚动 Hermite 多项式变换**，产出 48 个二阶特征，量化因子分布的非高斯性和稳定性：

| 输出指标 | 窗口 | 含义 |
|---|---|---|
| `h3_60` | 60 日 | 滚动偏度幅度（分布不对称程度） |
| `h4_60` | 60 日 | 滚动峰度幅度（厚尾程度） |
| `ts_closeness_60` | 60 日 | `−log(1+h3²+h4²)`，接近高斯的程度 |
| `energy_compression_20_60` | 20/60 日 | `log(1+E60) − log(1+E20)`，非高斯能量压缩/膨胀 |

这 4 个指标 × 12 个源因子 = 48 个输出特征，覆盖以下因子族：

`hermite_information_rg`, `mf_hermite_information_rg`, `mf_price_volume_pressure_24`, `mf_volatility_32`, `mf_distribution_22`, `order_flow_20`, `trade_informed_flow_20`, `daily_alpha_6`

这些特征作为 **体制/稳定性调制器**，当某只股票的因子行为变得非高斯，意味着市场微观结构可能正在切换，下游 ML 模型可利用该信号调整预测。

## 接口约定（框架插件协议）

每个算子模块需暴露三个接口，供父框架 `minute_factor_cal.py` 自动发现和调度：

```python
# 1. 因子族标识
GROUP_NAME = "mf_volatility_32"

# 2. 输入列声明
COLUMNS = ["ticker", "timestamp", "open", "high", "low", "close", "volume"]

# 3. 计算入口（基础因子）
def compute_factor(df, date: int, history: dict) -> dict:
    """
    df:      当日的分钟 K 线 DataFrame
    date:    交易日 int，如 20250701
    history: 历史数据缓存（本模块 HISTORY_DAYS=0，不使用）
    
    返回: {factor_name: {ticker: float}}
    """
    ...

# 3'. 计算入口（元因子）
def compute_factors(data: dict) -> dict[str, pd.DataFrame]:
    """
    data: {"returns": 日收益 DataFrame (date × ticker)}
    
    返回: {factor_alias_metric: DataFrame (date × ticker)}
    """
    ...
```

## 使用方式

在父框架 `guan-factor-research-framework` 下运行：

```bash
# 计算 mf_volatility_32 因子，指定日期范围
python -m frame.minute_factor_cal --group mf_volatility_32 --start 20250101 --end 20250131

# 计算 Hermite 元因子（需先跑完所有基础因子）
python -m frame.minute_factor_cal --group hermite_factor_meta
```

## 技术栈

| 层 | 技术 |
|---|---|
| 语言 | Python 3.11+ |
| 计算 | NumPy, Pandas |
| 存储 | PyArrow / Apache Parquet（列式压缩） |
| 可选加速 | cuDF/cuPy (GPU), Polars (CPU) |

## 数据流

```
分钟 OHLCV 数据
    │
    ▼
mf_volatility_32         ──→  factor_results/mf_volatility_32/*.parquet
    │
    ▼ (与其他 6 个因子族一起)
hermite_factor_meta      ──→  factor_results/hermite_factor_meta/*.parquet
    │
    ▼
下游 ML 模型训练 / 回测
```

## 设计原则

- **插件式协议**：只需暴露 `GROUP_NAME` + `COLUMNS` + `compute_factor/compute_factors`，无需注册即可被框架发现
- **GPU/CPU 双后端**：运行时检测输入是否为 cuDF，自动适配
- **刻意紧凑**：Hermite 部分限定 12 个源因子 × 4 个指标，避免候选爆炸
- **数值稳健**：无穷值裁剪、零方差 guard（`std > 1e-8`）、z-score 限幅 [-8, 8]、float32 存储
- **零 ML 依赖**：纯特征生成，不耦合任何模型库

## 因子研究站点

本仓库包含一个可部署到 GitHub Pages 的静态研究站点，用于浏览因子元数据和代表性快照。站点不在浏览器中运行分钟级因子计算，完整 Parquet 数据也不提交到 Git。

### 本地运行

```bash
# 生成可预览的 demo 数据
python scripts/build_factor_snapshot.py --demo --output site/public/data/factor-snapshot.json

# 启动站点
cd site
npm install
npm run dev
```

站点包含以下入口：

- `/`：因子总览与数据流
- `/factors/realized_variance`：因子详情示例
- `/jumps`：RV / IVhat / RJV / RLJV / RSJV 跳跃分解
- `/hermite`：Hermite 非高斯体制时间线

如果已有真实因子结果，可将其根目录传给快照生成器：

```bash
python scripts/build_factor_snapshot.py \
  --input-root /path/to/factor_results \
  --output site/public/data/factor-snapshot.json
```

推送到 `master` 后，GitHub Actions 会构建并发布 Pages。首次启用时，需要在仓库 Settings → Pages → Build and deployment 中选择 GitHub Actions。站点地址通常为 `https://<owner>.github.io/<repository>/`。
