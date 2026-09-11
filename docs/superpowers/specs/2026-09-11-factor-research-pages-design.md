# factor-research-observatory 因子研究 GitHub Pages 设计

## 目标

为 `factor-research-observatory` 提供一个可部署到 GitHub Pages 的静态研究站点，用于解释因子体系、展示代表性统计结果，并帮助研究者检查因子输出。站点是浏览和解释层，不在浏览器中实时运行分钟级因子计算。

第一版聚焦已有文档和代表性因子：32 个分钟因子、48 个 Hermite 元因子、跳跃分解链路，以及 `vol_rv_ts_closeness_60` 的单股时间序列与横截面分布。

## 范围

包含：

- 因子总览页：因子族、数量、输入输出和数据流。
- 因子详情页：公式、经济含义、输入、实现位置和统计摘要。
- 跳跃分解可视化：RV、IVhat、RJV、大跳跃和小跳跃的关系。
- Hermite 体制可视化：h3、h4、ts closeness、energy compression 的时间序列。
- 由 Parquet 生成轻量静态 JSON 的脚本。
- GitHub Actions 构建并发布到 GitHub Pages。
- 无数据时的明确空状态；可用提交到仓库的 demo snapshot 保证页面可预览。

不包含：

- 浏览器端执行 Python 或分钟级因子计算。
- 将完整 Parquet 数据提交到 Git。
- 完整回测、IC 分析、分组收益和在线数据服务。
- 修改现有因子计算公式或父框架插件协议。

## 技术方案

在仓库根目录新增 `site/` 前端和 `scripts/` 数据摘要生成脚本。前端使用 Vite、React、TypeScript 和 ECharts；生成后的 JSON 放在站点静态资源中。GitHub Actions 使用 Node 构建站点，并通过 Pages artifact 发布。

数据生成脚本提供两种输入模式：

1. 若存在仓库外或本地指定路径的 Parquet，读取并生成真实摘要。
2. 若没有数据，生成受 schema 约束的 demo snapshot，让站点可以在 CI 和新 clone 环境下完成构建；页面明确标注 demo 数据。

生成内容包括：因子元数据、数据集概况、因子分布分位数、代表性股票时间序列、日期截面摘要，以及跳跃分解示例。原始数据路径通过命令行参数或环境变量传入，不硬编码本机路径。

## 页面和交互

### 总览页

展示因子数量、因子族卡片、数据流图和当前 snapshot 状态。因子族卡片链接至详情页。

### 因子详情页

通过 URL 参数选择因子，展示描述、公式、实现模块、统计摘要和代表性时间序列。首版至少覆盖 `realized_variance`、`ivhat`、`rjv`、`rljv`、`rsjv` 和 `vol_rv_ts_closeness_60`；其他因子以元数据列表形式可浏览。

### 跳跃分解页

用流程图或层级卡片解释 `RV → IVhat → RJV → RLJV / RSJV`，配合代表股票或日期的分解柱状图。数值缺失时显示原因而不是伪造零值。

### Hermite 体制页

支持代表股票选择，绘制 h3、h4 和 ts closeness 的同步时间线，并显示“越接近 0 / 越负”的解释。页面须说明它是研究信号，不是交易建议。

## 数据契约

静态 snapshot 使用版本化 JSON schema，至少包含：

- `generated_at`
- `source`: `demo` 或 `parquet`
- `datasets`
- `factor_groups`
- `factors`
- `series`
- `cross_section`
- `jump_decomposition`

所有数值在生成阶段转换为有限 JSON 数值或 `null`；日期统一使用 `YYYY-MM-DD` 展示格式，股票代码保留六位字符串。前端只消费 snapshot，不读取 Parquet。

## 错误处理与可复现性

- 缺少 Parquet、列名不匹配或数据为空时，生成脚本失败并给出具体路径/列名错误；CI 可以显式选择 demo 模式。
- 前端加载 snapshot 失败时显示错误状态和恢复提示。
- 数据摘要脚本提供 `--input-root`、`--output` 和 `--demo` 参数。
- 页面 footer 显示 snapshot 来源、生成时间和仓库版本信息。

## 验证

- Python：对 snapshot 生成器运行最小 demo 数据测试，检查 schema、有限数值、六位股票代码和跳跃分解关系。
- 前端：运行 TypeScript 类型检查和 production build。
- 静态检查：确认生成目录不包含 Parquet，确认 Pages 子路径下资源引用正确。
- 手工检查：打开构建后的总览、因子详情、跳跃分解和 Hermite 页面，验证空状态与 demo 状态。

## 后续扩展

在 MVP 稳定后，再增加因子 IC、分组收益、衰减曲线、相关性矩阵和真实数据自动刷新。这些功能不应阻塞第一版静态研究站点。
