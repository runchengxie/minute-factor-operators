# Factor Research Observatory — Factor Explorer Phase 1

## 1. Goal

Upgrade the site from a set of attractive snapshot pages into a discoverable,
consistent factor research interface. Phase 1 focuses on factor discovery and
explanation, not predictive validation.

The phase delivers:

- a shared factor metadata model;
- a searchable and filterable `/factors` catalog;
- a unified factor detail page with data-quality and distribution context;
- a global snapshot context bar on the overview page;
- explicit boundaries around demo, descriptive, and PIT-derived data.

The phase does not add IC, IR, quantile-return, turnover, or trading claims.
Jump decomposition and Hermite chart redesign remain Phase 2 work.

## 2. Current constraints

The site consumes committed JSON snapshots generated outside the web build.
Minute and Hermite factors are represented by `factor-snapshot.json` while
fundamental factors are split between `fundamental-factor-catalog.json` and
`fundamental-snapshot.json`. The first implementation should adapt these
existing files rather than require a new backend or a new raw-data pipeline.

The local PIT fundamental snapshot currently describes a Tushare
`tushare.a_share.fundamentals.pit.v2` vintage. Standardized operating profit is
an initial all-market calculation using fiscal-year cumulative reports split
into quarters, with four complete quarters required for TTM and six prior TTM
values used for standardization. The UI must present this as a research
snapshot and not as a validated backtest result.

## 3. Proposed architecture

### 3.1 Shared view model

Add a view-model adapter layer that turns each source snapshot into a common
`FactorRecord`. The adapter is the only place that knows the source-specific
JSON shape. Existing specialized pages may continue using their source data,
but the new explorer and detail page consume the shared model.

The model contains:

```ts
type FactorStatus = 'descriptive' | 'experimental' | 'validated'

interface FactorRecord {
  id: string
  displayName: string
  displayNameCn?: string
  family: string
  subfamily?: string
  frequencyIn?: string
  frequencyOut?: string
  status: FactorStatus
  formula?: string
  formulaLatex?: string
  definition: string
  intuition?: string
  interpretationHigh?: string
  interpretationLow?: string
  inputFields?: string[]
  unit?: string
  transformHint?: string
  failureModes?: string[]
  sourceModule?: string
  coverage?: FactorCoverage
  statistics?: FactorStatistics
  series?: FactorSeriesPoint[]
}
```

Optional fields are intentional. A missing statistic is represented as absent
or unavailable, never as a fabricated zero.

### 3.2 Routes

- `/factors` — unified factor explorer.
- `/factors/:id` — unified detail page.
- `/jumps`, `/hermite`, `/fundamentals` — retained as specialized research
  pages and linked from the overview and factor records where relevant.
- Existing `/factors/<name>` behavior is migrated to the shared detail route;
  unknown IDs render a readable not-found state.

### 3.3 Overview context

Add a compact context bar near the top of the overview page. It should show
the available snapshot date or date range, data source, universe, frequency,
PIT status, and whether the current data is demo/descriptive/experimental.
Values come from snapshot metadata and are not hardcoded into the component.

## 4. Factor metadata contract

Every factor visible in the explorer must have a useful human-readable
definition. Generic fallbacks such as “derived OHLCV statistic” or “see
implementation module” are allowed only as a last-resort display fallback and
must be identifiable as incomplete metadata.

The metadata contract includes:

- identity: `id`, display names, family, and subfamily;
- research context: input/output frequency and status;
- interpretation: formula, definition, intuition, high/low direction;
- data semantics: inputs, unit, transform hint, and known failure modes;
- provenance: source module and snapshot/source label;
- optional diagnostics: coverage, percentile summary, and representative
  series.

For current minute factors, descriptions should be derived from the operator
definitions already present in the repository. For Hermite and fundamental
factors, wording must distinguish descriptive interpretation from a tested
return hypothesis.

## 5. Explorer behavior

The explorer presents a research-oriented table rather than an admin table.
Each row shows factor name, family, frequency, coverage when available, and
research status. It supports:

- free-text search over ID, display name, family, definition, and inputs;
- family filter;
- frequency filter;
- status filter;
- deterministic sorting by name, coverage, or status;
- row navigation to the detail page.

Filters should be URL-addressable where practical so a copied catalog view is
reproducible. Empty results should explain which filters are active and offer a
clear action.

## 6. Detail page behavior

The detail page follows a consistent research grammar:

1. Identity: name, family, frequency, and status.
2. Definition: formula, plain-language definition, inputs, unit, and
   intuition.
3. Data quality: coverage, valid/missing counts, source, snapshot date, and
   PIT notes when available.
4. Distribution: available percentile summary; do not imply a full historical
   distribution when only a cross-sectional snapshot exists.
5. Dynamics: a selectable ticker series when available. The default ticker is
   the first valid series in the snapshot, labeled as an example rather than a
   representative of the full universe.
6. Interpretation: high/low interpretation and failure modes.
7. Research boundary: descriptive/experimental status and an explicit note
   when predictive validation is not available.

The page must not call a single security representative of the market. If a
source has no series, show the metadata and an unavailable-data panel.

## 7. Data quality and error handling

- Snapshot loading errors render an in-page error state with the attempted
  source name.
- Unknown factor IDs render a not-found state with a link back to `/factors`.
- Missing optional fields render “not available” rather than zero or an empty
  chart.
- A malformed individual factor should not prevent valid factors from loading;
  adapters should skip or mark invalid records with a visible warning.
- The UI must retain the existing fundamental guardrails: PIT availability
  date, vintage, quarterly reconstruction rule, complete-quarter requirement,
  and the warning that formal backtest validation remains outstanding.

## 8. Testing and acceptance criteria

### Unit/data tests

- Each source snapshot adapts to at least one valid `FactorRecord`.
- Required metadata fields are present for all explorer-visible factors.
- Search and filter logic handles case-insensitive queries, empty filters, and
  no-result states.
- Optional diagnostics remain unavailable rather than becoming zero.
- Fundamental PIT caveat text is retained in the adapted record/context.

### Build verification

- Existing Python snapshot tests pass.
- TypeScript build passes.
- Vite production build passes.
- Existing routes and specialized pages still render.
- `npm audit` is run and any remaining advisory is reported separately from
  this feature.

## 9. Explicit non-goals

- No live connection to `~/data` from GitHub Pages.
- No change to fundamental calculation methodology in this phase.
- No automated claim that a factor is predictive or validated.
- No Jump/Hermite chart redesign.
- No backtest or portfolio recommendation UI.
