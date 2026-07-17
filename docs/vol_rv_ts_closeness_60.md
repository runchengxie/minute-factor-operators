# vol_rv_ts_closeness_60.parquet

> **数据词典 / Data Dictionary**

## 概述

| 属性 | 值 |
|---|---|
| **产生算子** | `hermite_factor_meta.py` |
| **变量名** | `ts_closeness_60` |
| **源特征** | `realized_variance`（来自 `mf_volatility_32`） |
| **文件大小** | 56 MB |
| **存储格式** | Apache Parquet（列式压缩） |

该文件是 **Hermite 元因子（二阶算子）的计算产物**，衡量每只 A 股在过去 60 个交易日内已实现方差（`realized_variance`）时间序列的 **非高斯偏离程度**，供下游 ML 模型作为体制识别 / 稳定性调制信号使用。

---

## Schema

| 列名 | 类型 | 说明 |
|---|---|---|
| `ticker` | `string` | 股票代码，6 位数字，如 `000001`、`600519`、`688981` |
| `date` | `int64` | 交易日，格式 `YYYYMMDD`，如 `20210420` |
| `vol_rv_ts_closeness_60` | `float64` | 因子值：已实现方差的 60 日 Hermite 序列近似度 |

文件为 **长格式（tidy/long）**，每行代表一个 (股票, 日期) 组合的单个因子值。

---

## 数据画像

| 统计量 | 值 |
|---|---|
| **总行数** | 6,147,502 |
| **日期范围** | 2021-04-20 ~ 2026-07-03（1261 个交易日） |
| **覆盖股票** | 5,363 只（A 股全市场） |
| **缺失值** | 0（100% 覆盖） |

### 因子值分布

| 统计量 | 值 |
|---|---|
| **最小值** | −7.15 |
| **最大值** | −0.000000 |
| **均值** | −1.87 |
| **中位数** | −1.20 |
| **标准差** | ~1.5 |
| **负值比例** | 100% |

### 典型行示例

| ticker | date | vol_rv_ts_closeness_60 |
|---|---|---|
| `000001` | 20210420 | −0.374776 |
| `000002` | 20210420 | −0.139619 |
| `000004` | 20210420 | −3.096145 |
| `688819` | 20260703 | −0.163090 |
| `688981` | 20260703 | −4.092375 |
| `689009` | 20260703 | −1.550362 |

---

## 计算方法

### 输入

每只股票的 `realized_variance` 时间序列（过去 60 个交易日），`realized_variance` 由 `mf_volatility_32.py` 基于当日分钟 K 线计算：

$$RV_t = \sum_{i=1}^{N} r_{t,i}^2$$

其中 $r_{t,i}$ 是第 $t$ 日第 $i$ 个分钟区间的对数收益，$N$ 为当日分钟数（A 股约 240）。

### 算法

对每只股票，取最近 $T=60$ 个交易日的 RV 序列 $\{x_1, x_2, \dots, x_T\}$：

1. **标准化**：$z_i = \frac{x_i - \mu}{\sigma}\ (\text{若 } \sigma > 10^{-8})$

2. **Hermite 多项式展开**，计算偏度和峰度对应的 Hermite 振幅：
   - $h_3 = \frac{1}{\sqrt{6}} \cdot \frac{1}{T} \sum (z_i^3 - 3z_i)$ — 偏度分量
   - $h_4 = \frac{1}{\sqrt{24}} \cdot \frac{1}{T} \sum (z_i^4 - 6z_i^2 + 3)$ — 峰度分量

3. **序列高斯近似度（TS Closeness）**：
   $$\text{ts\_closeness\_60} = -\ln\!\big(1 + h_3^2 + h_4^2\big)$$

### 直觉

- 如果 RV 序列表现接近高斯（$h_3 \approx 0,\ h_4 \approx 0$），则 $\text{ts\_closeness} \approx 0$
- RV 序列偏离高斯越远（偏斜、厚尾、跳跃），`ts_closeness` 越负（−5 ~ −7）
- 该值是 **体制稳定性调制器**：值越负 → 该股票近期波动行为越不稳定 → 下游模型应降低预测置信度或调整策略权重

---

## 为什么全是负数？

金融时间序列天然具有厚尾和非对称特征 — 股价波动不会严格服从高斯分布。因此 $h_3^2 + h_4^2$ 始终大于 0，$-\ln(1 + h_3^2 + h_4^2)$ 永远为负。

- **接近 0**（如 −0.14）：该股票近期波动行为"相对正常"
- **−1 到 −3**（如 −1.2 的中位数）：有一定偏离，属于常见状态
- **−5 到 −7**（极端值）：波动体制剧烈切换，需高度警惕

---

## 在因子体系中的位置

```
mf_volatility_32.py
  └── realized_variance (已实现方差)
         │
         ▼
hermite_factor_meta.py
  └── vol_rv_ts_closeness_60  ← 本文件
         │
         ▼
   下游 ML 模型（alpha 预测 / 风险管理）
```

本文件是 `hermite_factor_meta` 的 48 个输出之一（12 源因子 × 4 指标）。

---

## 使用示例

```python
import pandas as pd

df = pd.read_parquet("vol_rv_ts_closeness_60.parquet")

# 过滤单只股票
ts = df[df["ticker"] == "000001"].set_index("date")["vol_rv_ts_closeness_60"]
print(ts.describe())

# 过滤单日截面
cross = df[df["date"] == 20260703]
print(f"2026-07-03: {cross['vol_rv_ts_closeness_60'].describe()}")

# 转宽表（date × ticker）
wide = df.pivot(index="date", columns="ticker", values="vol_rv_ts_closeness_60")
```

---

## 注意事项

1. **需要前 60 个交易日预热**：滚动窗口需要至少 `MIN_LONG = 36` 个有效观测，初期日期可能用较短窗口计算
2. **已做数值裁剪**：z-score 限幅 $[-8, 8]$，无穷值裁剪为 0
3. **float64 存储**：文件内为 float64 以保留足够精度，父框架实际加载时可能转为 float32
4. **与框架路径耦合**：本文件在框架中位于 `factor_results/hermite_factor_meta/` 下，独立使用时需自行管理路径
