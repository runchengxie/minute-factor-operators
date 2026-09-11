#!/usr/bin/env python3
"""Build a small, point-in-time fundamental snapshot for the research site."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def _finite(value: Any) -> float | None:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def _display_date(value: Any) -> str:
    text = str(value).replace("-", "")
    return f"{text[:4]}-{text[4:6]}-{text[6:8]}" if len(text) == 8 else str(value)


def _quarter_key(period: str) -> tuple[int, int]:
    period = str(period).replace("-", "")
    year, month = int(period[:4]), int(period[4:6])
    return year, (month - 1) // 3 + 1


def _quarter_period(year: int, quarter: int) -> str:
    return f"{year:04d}-{quarter * 3:02d}-{(31, 30, 30, 31)[quarter - 1]:02d}"


def _offset_quarter(key: tuple[int, int], offset: int) -> tuple[int, int]:
    absolute = key[0] * 4 + key[1] - 1 - offset
    return absolute // 4, absolute % 4 + 1


def _read_pit(input_root: Path, tickers: list[str] | None):
    try:
        import pyarrow.dataset as ds
    except ImportError as exc:
        raise RuntimeError("读取 PIT Parquet 需要 pyarrow；请使用 uv run --with pandas --with pyarrow") from exc
    pit_data = input_root / "pit" / "data"
    if not pit_data.exists():
        pit_data = input_root
    dataset = ds.dataset(pit_data, format="parquet", partitioning="hive")
    wanted = [
        "symbol", "trade_date", "report_period", "disclosure_date", "available_date",
        "operate_profit", "total_assets", "net_profit", "revenue", "roe", "roa",
        "net_profit_yoy", "revenue_yoy",
    ]
    columns = [column for column in wanted if column in dataset.schema.names]
    predicate = ds.field("symbol").isin(tickers) if tickers else None
    table = dataset.to_table(columns=columns, filter=predicate)
    if not table.num_rows:
        raise ValueError(f"PIT 数据中没有目标股票：{tickers}")
    frame = table.to_pandas()
    frame = frame[frame["symbol"].astype(str).str.match(r"^\d{6}\.(SZ|SH|BJ)$")].copy()
    if frame.empty:
        raise ValueError("PIT 数据过滤真实 A 股代码后为空")
    return frame


def _collapse_rows(frame):
    keys = ["symbol", "trade_date", "report_period", "disclosure_date", "available_date"]
    values = [column for column in frame.columns if column not in keys]
    return frame.groupby(keys, as_index=False, dropna=False, sort=False)[values].first()


def _standardized_op_series(frame):
    rows = frame[frame["operate_profit"].notna()].copy()
    rows["period_key"] = rows["report_period"].map(_quarter_key)
    rows = rows.sort_values(["symbol", "period_key", "available_date"])
    output = []
    for symbol, group in rows.groupby("symbol", sort=True):
        cumulative = {row.period_key: float(row.operate_profit) for row in group.itertuples()}
        ttms: dict[tuple[int, int], float] = {}
        for year, quarter in sorted(cumulative):
            current = cumulative.get((year, quarter))
            if current is None:
                continue
            quarterly = []
            for offset in range(4):
                q = quarter - offset
                y = year
                while q <= 0:
                    y -= 1
                    q += 4
                value = cumulative.get((y, q))
                if value is None:
                    quarterly = []
                    break
                previous = cumulative.get((y, q - 1)) if q > 1 else cumulative.get((y - 1, 4))
                quarterly.append(value - previous if previous is not None else value)
            if len(quarterly) == 4:
                ttms[(year, quarter)] = sum(quarterly)
        for row in group.itertuples():
            key = row.period_key
            current = ttms.get(key)
            history = [ttms.get(_offset_quarter(key, index + 1)) for index in range(6)]
            history = [value for value in history if value is not None]
            zscore = None
            if current is not None and len(history) == 6:
                mean = sum(history) / 6
                variance = sum((value - mean) ** 2 for value in history) / 6
                std = math.sqrt(variance)
                zscore = (current - mean) / std if std > 1e-12 else None
            output.append({"ticker": symbol, "report_period": _display_date(row.report_period), "available_date": _display_date(row.available_date), "op_ttm": _finite(current), "standardized_operating_profit": _finite(zscore)})
    return output


def build_snapshot(input_root: Path, output: Path, tickers: list[str], all_market: bool = False) -> dict[str, Any]:
    frame = _collapse_rows(_read_pit(input_root, None if all_market else tickers))
    op_rows = _standardized_op_series(frame)
    series = []
    for ticker in tickers:
        rows = [row for row in op_rows if row["ticker"] == ticker]
        rows = sorted(rows, key=lambda row: row["available_date"])
        series.append({"ticker": ticker, "metric": "standardized_operating_profit", "dates": [row["available_date"] for row in rows], "values": [row["standardized_operating_profit"] for row in rows]})
        for metric in ["roe", "roa", "net_profit_yoy", "revenue_yoy"]:
            metric_rows = frame[(frame["symbol"] == ticker) & frame[metric].notna()].sort_values("available_date") if metric in frame else frame.iloc[0:0]
            metric_rows = metric_rows.tail(24)
            if not metric_rows.empty:
                series.append({"ticker": ticker, "metric": metric, "dates": [_display_date(value) for value in metric_rows["available_date"].tolist()], "values": [_finite(value) for value in metric_rows[metric].tolist()]})
    available = frame["available_date"].dropna().astype(str).tolist()
    latest = {}
    for row in op_rows:
        if row["standardized_operating_profit"] is not None:
            latest[row["ticker"]] = row
    latest_values = [row["standardized_operating_profit"] for row in latest.values()]
    latest_values.sort()
    def quantile(fraction: float) -> float | None:
        if not latest_values:
            return None
        index = min(len(latest_values) - 1, int(round((len(latest_values) - 1) * fraction)))
        return latest_values[index]
    snapshot = {
        "schema_version": 1,
        "source": "local_pit_vintage",
        "vintage": "20260802",
        "dataset": "tushare.a_share.fundamentals.pit.v2",
        "coverage": {"date_start": _display_date(min(available)), "date_end": _display_date(max(available)), "tickers": tickers, "tickers_count": int(frame["symbol"].nunique()), "representative_tickers": tickers, "observations": int(len(frame))},
        "latest_cross_section": {"metric": "standardized_operating_profit", "count": len(latest_values), "missing": int(frame["symbol"].nunique() - len(latest_values)), "p01": quantile(0.01), "p25": quantile(0.25), "p50": quantile(0.5), "p75": quantile(0.75), "p99": quantile(0.99)},
        "validation": {"all_market_computed": all_market, "historical_ttm_window": 6, "complete_quarters_required": 4, "quarterly_rule": "Q1 cumulative; Q2/Q3 current cumulative minus prior quarter; Q4 annual minus Q3", "pit_date_field": "available_date", "report_period_field": "report_period", "universe_filter": "^[0-9]{6}\\.(SZ|SH|BJ)$"},
        "series": series,
        "notes": [
            "This snapshot is generated from a local point-in-time vintage and contains representative tickers only.",
            "The six-TTM standardized operating profit value is null until four complete quarters plus six historical TTM observations are available.",
            "The operating-profit TTM derivation treats reported values as cumulative fiscal-year values; validate this contract before using for backtests.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n")
    return snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--tickers", nargs="+", default=["000001.SZ", "600519.SH", "300750.SZ"])
    parser.add_argument("--all-market", action="store_true", help="compute the standardized operating profit cross-section for every PIT ticker")
    args = parser.parse_args()
    build_snapshot(args.input_root, args.output, args.tickers, all_market=args.all_market)


if __name__ == "__main__":
    main()
