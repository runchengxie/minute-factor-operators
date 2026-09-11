# Factor Explorer Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a shared, searchable factor catalog and research-oriented detail view while preserving the existing specialized pages and explicitly labeling snapshot limitations.

**Architecture:** Add a pure adapter layer that converts the three existing snapshot shapes into `FactorRecord` view models. Add `/factors` and route `/factors/:id` through those records, keeping Jump, Hermite, and Fundamentals pages as specialized views. Add snapshot-derived context and metadata without changing the raw-data or fundamental calculation pipeline.

**Tech Stack:** React 18, TypeScript, Vite, ECharts wrappers, existing static JSON snapshots, CSS in `site/src/styles.css`, Python unittest snapshot tests.

**Spec:** `docs/superpowers/specs/2026-09-11-factor-explorer-phase1-design.md`

## Global Constraints

- Do not add IC, IR, quantile-return, turnover, or trading recommendation claims.
- Do not connect GitHub Pages builds directly to `~/data`.
- Do not change the standardized operating-profit calculation.
- Missing optional diagnostics must remain unavailable, never become zero.
- Preserve the PIT vintage, availability-date, quarterly reconstruction, and complete-quarter caveats.
- Preserve existing specialized routes and render a readable not-found state for unknown factor IDs.
- Use URL-safe factor IDs and keep the existing `BASE_URL` behavior for GitHub Pages.

## File map

- Create `site/src/research.ts`: shared factor view model, metadata catalog, source adapters, context helpers, and pure explorer filtering/sorting functions.
- Modify `site/src/types.ts`: add shared research types while retaining source snapshot types used by specialized pages.
- Modify `site/src/data.ts`: validate and load the source snapshots needed by the adapter layer.
- Create `site/src/pages/FactorExplorerPage.tsx`: searchable/filterable catalog.
- Modify `site/src/pages/FactorPage.tsx`: render the shared detail grammar and ticker selector.
- Modify `site/src/pages/OverviewPage.tsx`: render the global snapshot context bar and link to the full explorer.
- Modify `site/src/App.tsx`: build the shared research model, route `/factors`, and pass context/model data to pages.
- Modify `site/src/styles.css`: add context bar, explorer table/filter, detail sections, unavailable states, and responsive layout styles.
- Modify `tests/test_fundamental_factor_catalog.py` or add `tests/test_research_snapshot_contract.py` only if the implementation exposes a snapshot-contract regression.

### Task 1: Add shared research types and metadata contracts

**Files:**
- Modify: `site/src/types.ts`
- Create: `site/src/research.ts`
- Test: `tests/test_research_snapshot_contract.py` only when a source snapshot contract needs a regression test; otherwise the pure TypeScript helpers are verified through the production type check and manual route checks in later tasks.

**Interfaces:**
- Produces `FactorStatus`, `FactorCoverage`, `FactorStatistics`, `FactorSeriesPoint`, `FactorRecord`, `ResearchContext`, `ExplorerFilters`, `ExplorerSort`, and `toResearchRecords()` for later tasks.

- [ ] **Step 1: Define the shared types**

  Add the types from the approved spec. Keep `Factor`, `Series`, `Snapshot`, `FundamentalFactor`, and existing source types intact so Jump/Hermite/Fundamentals pages do not require a simultaneous rewrite.

- [ ] **Step 2: Define metadata records for all source families**

  Add a metadata map keyed by factor ID. Every record must have a useful definition, family, frequency, status, formula or explicit formula-unavailable state, and source module. Use `descriptive` for existing snapshot-only factors and `experimental` for the initial PIT standardized operating-profit factor.

- [ ] **Step 3: Add deterministic adapter helpers**

  Implement:

  ```ts
  export function adaptMinuteAndHermite(snapshot: Snapshot): FactorRecord[]
  export function adaptFundamentals(catalog: FundamentalCatalog, snapshot: FundamentalSnapshot): FactorRecord[]
  export function toResearchRecords(snapshot: Snapshot, catalog: FundamentalCatalog, fundamental: FundamentalSnapshot): FactorRecord[]
  ```

  Minute/Hermite records should attach matching cross-sectional percentile rows and matching ticker series. Fundamental records should attach catalog semantics, the latest cross-section for standardized operating profit where available, and the representative series from the PIT snapshot.

- [ ] **Step 4: Add pure filter and sort helpers**

  Implement:

  ```ts
  export function filterResearchRecords(records: FactorRecord[], filters: ExplorerFilters): FactorRecord[]
  export function sortResearchRecords(records: FactorRecord[], sort: ExplorerSort): FactorRecord[]
  ```

  Search case-insensitively across ID, display names, family, definition, and input fields. Sort ties by ID so results are reproducible.

- [ ] **Step 5: Run the type check**

  Run `npm --prefix site run build`.

  Expected: the new types and research module compile without introducing a test-runner dependency.

- [ ] **Step 6: Commit**

  ```bash
  git add site/src/types.ts site/src/research.ts
  git commit -m "feat: add shared factor research model"
  ```

### Task 2: Add snapshot context and data validation

**Files:**
- Modify: `site/src/data.ts`
- Modify: `site/src/research.ts`
- Modify: `site/src/types.ts`

**Interfaces:**
- Produces `buildResearchContext(snapshot, fundamental)` for the overview and footer.

- [ ] **Step 1: Extend source metadata types**

  Add optional metadata fields with safe defaults for dataset date range, universe label, and fundamental PIT notes. Do not require old demo snapshots to contain new fields.

- [ ] **Step 2: Implement context derivation**

  Build a `ResearchContext` containing source label, snapshot date/range, universe text, frequency text, PIT state, and status summary. Use `demo` for the main demo snapshot, `descriptive` for snapshot-only factor data, and `experimental` when the PIT fundamental validation object reports an initial or non-validated calculation.

- [ ] **Step 3: Validate factor source shape**

  Keep the existing required main snapshot validation and add explicit fundamental field checks that produce the current readable error message. Do not reject older optional metadata fields.

- [ ] **Step 4: Build and run existing tests**

  Run `python -m unittest discover -v` and `npm --prefix site run build`.

- [ ] **Step 5: Commit**

  ```bash
  git add site/src/data.ts site/src/research.ts site/src/types.ts
  git commit -m "feat: derive research snapshot context"
  ```

### Task 3: Add the Factor Explorer route and catalog UI

**Files:**
- Create: `site/src/pages/FactorExplorerPage.tsx`
- Modify: `site/src/App.tsx`
- Modify: `site/src/styles.css`

**Interfaces:**
- Consumes `FactorRecord[]`, `ResearchContext`, `filterResearchRecords`, and `sortResearchRecords` from Tasks 1–2.
- Produces `/factors` with URL-addressable `q`, `family`, `frequency`, `status`, and `sort` query parameters.

- [ ] **Step 1: Implement URL filter parsing**

  Parse `window.location.search` into `ExplorerFilters` with empty defaults. Keep the implementation compatible with the static Vite site; use normal anchor navigation rather than adding a router dependency.

- [ ] **Step 2: Render the catalog controls**

  Add search input, family/frequency/status selects, sort select, active-filter summary, and clear-filter action. The UI must show a no-results explanation when the filtered set is empty.

- [ ] **Step 3: Render research table rows**

  Show factor ID/display name, family, frequency, coverage, and status. Link each row to `factors/<encoded-id>` under `BASE_URL`. Show “未计算” or “不可用” for absent optional diagnostics.

- [ ] **Step 4: Add responsive styles**

  Add a horizontally scrollable table on narrow screens, preserve the existing dark research visual language, and use semantic status/family tokens rather than inline colors.

- [ ] **Step 5: Wire the route**

  In `App.tsx`, compute records once after loading and route `factors` to `FactorExplorerPage`. Keep existing `factors/<name>` detail routing intact until Task 4 replaces its implementation.

- [ ] **Step 6: Verify route behavior**

  Run `npm --prefix site run build` and use `npm --prefix site run dev -- --host 127.0.0.1` to check `/factors`, search, a no-result filter, and a factor link manually.

- [ ] **Step 7: Commit**

  ```bash
  git add site/src/pages/FactorExplorerPage.tsx site/src/App.tsx site/src/styles.css
  git commit -m "feat: add factor explorer catalog"
  ```

### Task 4: Replace the single-factor page with the shared detail grammar

**Files:**
- Modify: `site/src/pages/FactorPage.tsx`
- Modify: `site/src/App.tsx`
- Modify: `site/src/styles.css`

**Interfaces:**
- Consumes one `FactorRecord`, the full records list for ticker options, and `ResearchContext`.
- Produces a not-found state when the ID is absent and an unavailable panel when no series/statistics exist.

- [ ] **Step 1: Add record lookup and not-found handling**

  Change the page input from source `Snapshot` plus factor name to `factor: FactorRecord`, `seriesOptions`, and `context`. If no record is found, render a link back to `/factors`.

- [ ] **Step 2: Render identity and metadata sections**

  Render display name, ID, family, frequency, status, formula, definition, intuition, input fields, unit, and source module. Use explicit copy for descriptive/experimental status.

- [ ] **Step 3: Render quality and distribution sections**

  Render coverage, valid/missing counts, snapshot range, and percentile cards only when values are available. Add a visible PIT caveat for fundamental records. Do not infer skew, persistence, or predictive quality.

- [ ] **Step 4: Add selectable series**

  Select from available `(ticker, metric)` series and render the existing `LineChart`. Default to the first valid series and label it “示例序列”, not “代表股票”. If no series exists, render an unavailable-data panel.

- [ ] **Step 5: Add interpretation and failure modes**

  Render high/low interpretation and failure modes as optional sections; if not available, show the metadata status rather than empty cards.

- [ ] **Step 6: Wire unified detail route**

  Update `App.tsx` to resolve the decoded ID from shared records and pass the selected record into `FactorPage`. Preserve all existing specialized routes.

- [ ] **Step 7: Verify detail states**

  Build and manually check a minute factor, a Hermite factor, the standardized operating-profit factor, a factor with no series, and an unknown ID.

- [ ] **Step 8: Commit**

  ```bash
  git add site/src/pages/FactorPage.tsx site/src/App.tsx site/src/styles.css
  git commit -m "feat: add unified factor detail view"
  ```

### Task 5: Add the global context bar and explorer navigation

**Files:**
- Modify: `site/src/pages/OverviewPage.tsx`
- Modify: `site/src/App.tsx`
- Modify: `site/src/styles.css`

**Interfaces:**
- Consumes `ResearchContext` and factor count/family count derived from `FactorRecord[]`.

- [ ] **Step 1: Add the context bar**

  Render source, snapshot range, universe, frequency, PIT state, and descriptive/experimental labeling near the overview hero. Use the derived context, not hardcoded dates.

- [ ] **Step 2: Add observatory metrics**

  Replace or supplement the existing hardcoded factor metrics with counts derived from records: total factors, family count, available coverage summary, and number of experimental records. Keep existing metrics that remain accurate.

- [ ] **Step 3: Link the full catalog**

  Add a clear “浏览全部因子” link from the Factor Atlas area to `/factors` while retaining the existing family cards and specialist links.

- [ ] **Step 4: Verify responsive layout**

  Build and inspect desktop and narrow viewport layouts; context items should wrap without horizontal overflow.

- [ ] **Step 5: Commit**

  ```bash
  git add site/src/pages/OverviewPage.tsx site/src/App.tsx site/src/styles.css
  git commit -m "feat: add observatory context bar"
  ```

### Task 6: Complete metadata coverage and documentation copy

**Files:**
- Modify: `site/src/research.ts`
- Modify: `README.md` if the public route list or data caveat is incomplete
- Modify: `docs/superpowers/specs/2026-09-11-factor-explorer-phase1-design.md` only if implementation reveals a resolved contract difference

- [ ] **Step 1: Audit every factor family**

  Enumerate all IDs emitted by the current snapshots and ensure each has a non-generic definition, family, frequency, status, and source label. Use a visible “metadata incomplete” marker only for records that cannot be described from repository code.

- [ ] **Step 2: Add fundamental caveat copy**

  Include the current standardized-operating-profit caveat: three representative series are for display, the all-market PIT snapshot is an initial calculation, fiscal-year cumulative reports are reconstructed into quarters, and formal backtest validation remains outstanding.

- [ ] **Step 3: Update README route documentation**

  Document `/factors`, the descriptive-only status of the explorer, and the distinction between local PIT snapshot generation and the static GitHub Pages artifact.

- [ ] **Step 4: Commit**

  ```bash
  git add site/src/research.ts README.md docs/superpowers/specs/2026-09-11-factor-explorer-phase1-design.md
  git commit -m "docs: complete factor research metadata"
  ```

### Task 7: Full verification and delivery handoff

**Files:**
- Verify all changed files; no new source file is expected unless a test exposes a specific defect.

- [ ] **Step 1: Run Python tests**

  Run `python -m unittest discover -v` from the worktree.

  Expected: all existing data/snapshot tests pass.

- [ ] **Step 2: Run the production build**

  Run `npm --prefix site run build`.

  Expected: TypeScript and Vite both exit successfully.

- [ ] **Step 3: Run dependency audit**

  Run `npm --prefix site audit --omit=dev` and record the actual result. Do not force-upgrade dependencies as part of this feature.

- [ ] **Step 4: Check the generated artifact**

  Confirm `site/dist/index.html` and `site/dist/404.html` are generated when using the repository workflow-compatible build path. Confirm no raw `~/data` path is bundled into the site.

- [ ] **Step 5: Review the diff**

  Run `git diff origin/master...HEAD --check` and inspect `git diff --stat origin/master...HEAD`. Confirm no unrelated files or generated raw data are included.

- [ ] **Step 6: Commit any final test-only fix**

  If verification finds a defect, add a focused fix commit with the failing command and corrected behavior documented in the commit message. If clean, make no empty commit.

- [ ] **Step 7: Prepare PR handoff**

  Push `feat/factor-explorer-phase1`, create a PR targeting `master`, and report the PR URL, validation commands, audit result, and any remaining limitations. Merge and clean up only after required checks and review are complete.
