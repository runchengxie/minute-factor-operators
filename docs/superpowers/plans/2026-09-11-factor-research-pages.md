# Factor Research Pages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a static, GitHub Pages-compatible research site that explains multi-frequency factor families and interactively explores representative jump, Hermite, and fundamental factor outputs.

**Architecture:** A Python snapshot builder reads local Parquet when available or emits a deterministic demo snapshot when requested. A Vite/React/TypeScript site consumes only the generated JSON, renders overview, factor detail, jump decomposition, and Hermite regime pages, and is deployed by a Pages artifact workflow.

**Tech Stack:** Python 3.11 standard library plus pandas/pyarrow when reading real data; Vite, React, TypeScript, ECharts, npm; GitHub Actions Pages deployment.

**Spec:** `docs/superpowers/specs/2026-09-11-factor-research-pages-design.md`

## Global Constraints

- The site is a browsing and explanation layer; it does not execute Python or minute-level factor calculation in the browser.
- Do not commit complete Parquet files; only commit lightweight demo/static JSON assets.
- Preserve the existing factor calculation modules and plugin protocol.
- All snapshot numbers must be finite JSON numbers or `null`; ticker codes remain six-character strings.
- The UI must identify demo data and state that signals are for research, not trading advice.
- The build must work under a GitHub Pages repository subpath.

## File Map

- Create `scripts/build_factor_snapshot.py`: deterministic snapshot builder with `--input-root`, `--output`, and `--demo`.
- Create `tests/test_build_factor_snapshot.py`: snapshot schema, finite-number, ticker, and decomposition tests.
- Create `site/package.json`, `site/tsconfig.json`, `site/vite.config.ts`, `site/index.html`: frontend toolchain and subpath-aware build.
- Create `site/src/types.ts`: TypeScript snapshot contract.
- Create `site/src/data.ts`: snapshot loader and factor metadata accessors.
- Create `site/src/App.tsx`, `site/src/main.tsx`, `site/src/styles.css`: routing, shell, and responsive styling.
- Create `site/src/components/MetricCard.tsx`, `site/src/components/LineChart.tsx`, `site/src/components/BarChart.tsx`: reusable display and chart components.
- Create `site/src/pages/OverviewPage.tsx`, `site/src/pages/FactorPage.tsx`, `site/src/pages/JumpPage.tsx`, `site/src/pages/HermitePage.tsx`: page-level views.
- Create `site/public/data/factor-snapshot.json`: small deterministic demo asset.
- Create `.github/workflows/deploy-pages.yml`: build and publish Pages artifact.
- Modify `README.md`: local preview, snapshot generation, and Pages link instructions.

### Task 1: Build and test the snapshot generator

**Files:**
- Create: `scripts/build_factor_snapshot.py`
- Create: `tests/test_build_factor_snapshot.py`

**Interfaces:**
- Produces `build_snapshot(input_root: Path | None, output: Path, demo: bool) -> dict`.
- CLI accepts `--input-root PATH`, `--output PATH`, and `--demo`.
- Emits the contract keys `generated_at`, `source`, `datasets`, `factor_groups`, `factors`, `series`, `cross_section`, and `jump_decomposition`.

- [ ] **Step 1: Write failing tests for deterministic demo output**

```python
def test_demo_snapshot_has_required_contract(tmp_path):
    result = build_snapshot(None, tmp_path / "snapshot.json", demo=True)
    assert result["source"] == "demo"
    assert {"generated_at", "datasets", "factor_groups", "factors", "series",
            "cross_section", "jump_decomposition"} <= result.keys()

def test_demo_snapshot_has_six_digit_tickers_and_finite_values(tmp_path):
    result = build_snapshot(None, tmp_path / "snapshot.json", demo=True)
    assert all(len(row["ticker"]) == 6 for row in result["series"])
    assert all(value is None or math.isfinite(value)
               for row in result["series"] for value in row["values"])

def test_jump_decomposition_preserves_residual_relation(tmp_path):
    result = build_snapshot(None, tmp_path / "snapshot.json", demo=True)
    jump = result["jump_decomposition"][0]
    assert jump["rjv"] == pytest.approx(jump["rljv"] + jump["rsjv"])
```

- [ ] **Step 2: Run the focused tests and verify they fail because the builder is absent**

Run: `python -m pytest tests/test_build_factor_snapshot.py -q`

Expected: collection failure reporting that `scripts.build_factor_snapshot` cannot be imported.

- [ ] **Step 3: Implement the snapshot contract and demo builder**

Define factor metadata from the existing `_FACTOR_NAMES` and `SOURCE_FACTORS`, use fixed demo dates/tickers, normalize tickers with `str.zfill(6)`, and serialize non-finite values as `None`. Generate jump rows where `rjv = rljv + rsjv`. For real input, inspect `factor_results/<group>/<factor>.parquet`, validate `date`/`ticker` columns, calculate quantiles and representative series, and raise `FileNotFoundError` or `ValueError` with the exact path/columns when input is invalid.

- [ ] **Step 4: Run the focused tests and add real-input validation tests**

Run: `python -m pytest tests/test_build_factor_snapshot.py -q`

Expected: all tests pass, including a test that a missing requested Parquet path raises `FileNotFoundError` and a test that `--output` contains valid JSON.

- [ ] **Step 5: Commit the data-layer deliverable**

```bash
git add scripts/build_factor_snapshot.py tests/test_build_factor_snapshot.py
git commit -m "feat: add factor snapshot builder"
```

### Task 2: Scaffold the static frontend and snapshot loading

**Files:**
- Create: `site/package.json`
- Create: `site/tsconfig.json`
- Create: `site/vite.config.ts`
- Create: `site/index.html`
- Create: `site/src/types.ts`
- Create: `site/src/data.ts`
- Create: `site/src/main.tsx`
- Create: `site/src/App.tsx`
- Create: `site/src/styles.css`
- Create: `site/public/data/factor-snapshot.json`

**Interfaces:**
- `loadSnapshot(): Promise<FactorSnapshot>` fetches `/data/factor-snapshot.json` relative to the Vite base path.
- `FactorSnapshot` models the Python contract without `any`.
- `App` renders a loading state, error state, or route page with the loaded snapshot.

- [ ] **Step 1: Add the minimal package and type contract**

Use React 18+, Vite 5+, TypeScript 5+, `echarts`, and `echarts-for-react`. Set Vite `base` to `process.env.BASE_PATH ?? '/'`; in Pages workflow pass `BASE_PATH=/${repository-name}/`.

- [ ] **Step 2: Add the generated demo JSON and loader**

Run `python scripts/build_factor_snapshot.py --demo --output site/public/data/factor-snapshot.json`, then implement `loadSnapshot()` with a checked `response.ok` branch and a JSON shape guard that reports the missing top-level key.

- [ ] **Step 3: Add the shell and explicit route handling**

Support `/`, `/factors/:name`, `/jumps`, and `/hermite` using `window.location.pathname` and links that work on static hosting. If an unknown path is opened, render a not-found view with a link back to `/`.

- [ ] **Step 4: Install dependencies and verify the production build**

Run: `cd site && npm install && npm run build`

Expected: Vite creates `site/dist` without TypeScript errors and includes `dist/data/factor-snapshot.json`.

- [ ] **Step 5: Commit the frontend scaffold**

```bash
git add site
git commit -m "feat: scaffold factor research site"
```

### Task 3: Implement overview and factor detail pages

**Files:**
- Create: `site/src/components/MetricCard.tsx`
- Create: `site/src/pages/OverviewPage.tsx`
- Create: `site/src/pages/FactorPage.tsx`
- Modify: `site/src/App.tsx`
- Modify: `site/src/styles.css`

**Interfaces:**
- `MetricCard({ label, value, note }: { label: string; value: string; note?: string })` renders a consistent summary card.
- `OverviewPage({ snapshot }: { snapshot: FactorSnapshot })` renders factor groups and data flow.
- `FactorPage({ snapshot, factorName }: { snapshot: FactorSnapshot; factorName: string })` renders metadata, quantiles, and series.

- [ ] **Step 1: Render overview cards from snapshot metadata**

Show dataset date range, ticker count, factor count, source badge, factor group cards, and the OHLCV → factors → Hermite → ML flow. Use data-driven mapping; do not duplicate counts in JSX.

- [ ] **Step 2: Render factor detail with safe missing-data behavior**

Resolve the factor by name, show module, family, formula, meaning, input, quantiles, implementation link, and representative series. For a factor without a series, show “暂无该因子的快照数据” while retaining metadata.

- [ ] **Step 3: Add responsive styling and research disclaimer**

Use a dark research-dashboard visual system with a warm accent, responsive two-column desktop layout collapsing to one column below 800px, visible focus states, and a footer saying “研究展示，不构成交易建议”。

- [ ] **Step 4: Verify pages in the production build**

Run: `cd site && npm run build`

Expected: build succeeds and the generated bundle contains overview and factor route text.

- [ ] **Step 5: Commit the overview/detail deliverable**

```bash
git add site/src
git commit -m "feat: add factor overview and detail pages"
```

### Task 4: Add jump and Hermite charts

**Files:**
- Create: `site/src/components/LineChart.tsx`
- Create: `site/src/components/BarChart.tsx`
- Create: `site/src/pages/JumpPage.tsx`
- Create: `site/src/pages/HermitePage.tsx`
- Modify: `site/src/App.tsx`
- Modify: `site/src/styles.css`

**Interfaces:**
- `LineChart({ dates, series }: { dates: string[]; series: Array<{ name: string; values: Array<number | null>; color: string }> })` renders an ECharts line chart with null gaps.
- `BarChart({ labels, values, colors }: { labels: string[]; values: Array<number | null>; colors: string[] })` renders a decomposition bar chart.
- `JumpPage({ snapshot }: { snapshot: FactorSnapshot })` renders the decomposition chain and selected example.
- `HermitePage({ snapshot }: { snapshot: FactorSnapshot })` renders ticker selection and synchronized metric lines.

- [ ] **Step 1: Add chart wrappers with disposal and empty states**

Initialize ECharts only when a container exists, dispose on unmount, resize on window changes, and render a plain empty message when all values are null or the input arrays are empty.

- [ ] **Step 2: Implement the jump decomposition page**

Render `RV → IVhat → RJV → RLJV / RSJV` as connected explanatory cards, then use `BarChart` for a representative ticker/date from `jump_decomposition`. Display the residual relation and never replace missing values with zero.

- [ ] **Step 3: Implement the Hermite page**

Use a native select populated from `snapshot.series`, default to the first ticker, and show h3, h4, ts closeness, and energy compression on a shared date axis. Include the interpretation “越接近 0 越接近高斯；越负表示偏离越明显”。

- [ ] **Step 4: Verify charts and routes**

Run: `cd site && npm run build`

Expected: build succeeds with no TypeScript errors; manually open `/jumps` and `/hermite` through the Vite preview server and verify the charts and select control render.

- [ ] **Step 5: Commit the chart deliverable**

```bash
git add site/src
git commit -m "feat: visualize jump and hermite factors"
```

### Task 5: Add GitHub Pages deployment and documentation

**Files:**
- Create: `.github/workflows/deploy-pages.yml`
- Modify: `README.md`

**Interfaces:**
- Workflow runs on pushes to `master` and manual dispatch, builds `site`, uploads `site/dist`, and deploys with the official Pages actions.
- README documents `python scripts/build_factor_snapshot.py --demo`, `cd site && npm run dev`, `npm run build`, and real data `--input-root` usage.

- [ ] **Step 1: Add the Pages workflow**

Configure `actions/configure-pages`, `actions/upload-pages-artifact`, and `actions/deploy-pages`; grant `pages: write` and `id-token: write`; set `BASE_PATH` from `${{ github.event.repository.name }}`; build the demo snapshot before `npm ci`/`npm run build`.

- [ ] **Step 2: Update README with local and deployment instructions**

Document that real Parquet stays outside Git, show the exact snapshot command, list the four routes, explain demo/source badges, and include the future Pages URL pattern without claiming it is live before deployment.

- [ ] **Step 3: Run the full verification suite**

Run:

```bash
python -m pytest tests/test_build_factor_snapshot.py -q
python scripts/build_factor_snapshot.py --demo --output site/public/data/factor-snapshot.json
cd site && npm ci && npm run build
```

Expected: Python tests pass, JSON parses, `site/dist` exists, no `.parquet` file appears under `site/dist`, and all Pages assets are emitted under the configured base path.

- [ ] **Step 4: Commit deployment and docs**

```bash
git add .github/workflows/deploy-pages.yml README.md site/public/data/factor-snapshot.json
git commit -m "ci: deploy factor research site to pages"
```

## Final Review Checklist

- [ ] Compare implementation against every section of the design spec.
- [ ] Run `git diff --check` and inspect `git status --short`.
- [ ] Confirm the existing Python factor modules are unchanged.
- [ ] Confirm the demo badge, research disclaimer, and missing-data states are visible.
- [ ] Report the actual test/build results and any remaining deployment configuration needed in the repository settings.
