#!/usr/bin/env python3
"""Build the small JSON data contract consumed by the research site."""

from __future__ import annotations

import argparse
import json
import math
from datetime import date, timedelta
from pathlib import Path
from typing import Any


FACTOR_NAMES = [
    "volume_volatility", "ideal_swing_factor", "star_volatility", "log_volume_volatility",
    "illiquidity", "illiquidity_std", "price_elasticity", "diff_abs_mean_volume",
    "diff_abs_mean_amplitude", "peak_count_1std", "peak_count_2std", "vol_amplitude",
    "realized_variance", "realized_skewness", "realized_kurtosis", "rv_pos", "rv_neg",
    "ivhat", "rjv", "rjvp", "rjvn", "sj", "srjv", "gamma_threshold", "rljv",
    "rljvp", "rljvn", "srljv", "rsjv", "rsjvp", "rsjvn", "srsjv",
]
HERMITE_METRICS = ["ts_h3_60", "ts_h4_60", "ts_closeness_60", "energy_compression_20_60"]
TICKERS = ["000001", "000002", "600519"]


def _finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _dates(count: int = 42) -> list[str]:
    end = date(2026, 7, 3)
    return [(end - timedelta(days=count - index - 1)).isoformat() for index in range(count)]


def _factor_metadata() -> list[dict[str, Any]]:
    families = {
        "volume_volatility": ("波动率 / 跳跃", "分钟成交量的变异系数", "mf_volatility_32.py"),
        "star_volatility": ("波动率 / 跳跃", "成交量突变时的收益波动", "mf_volatility_32.py"),
        "illiquidity": ("流动性", "Amihud 风格的分钟非流动性", "mf_volatility_32.py"),
        "price_elasticity": ("流动性", "价格振幅相对成交额的弹性", "mf_volatility_32.py"),
        "realized_variance": ("已实现矩", "分钟对数收益平方和", "mf_volatility_32.py"),
        "realized_skewness": ("已实现矩", "分钟收益的已实现偏度", "mf_volatility_32.py"),
        "realized_kurtosis": ("已实现矩", "分钟收益的已实现峰度", "mf_volatility_32.py"),
        "ivhat": ("跳跃分解", "对跳跃稳健的 tripower variation 方差估计", "mf_volatility_32.py"),
        "rjv": ("跳跃分解", "已实现方差中的跳跃部分", "mf_volatility_32.py"),
        "rljv": ("跳跃分解", "超过阈值的大跳跃方差", "mf_volatility_32.py"),
        "rsjv": ("跳跃分解", "小跳跃方差残差", "mf_volatility_32.py"),
    }
    result = []
    for name in FACTOR_NAMES:
        family, meaning, module = families.get(
            name, ("微观结构", "分钟 OHLCV 的派生统计量", "mf_volatility_32.py")
        )
        result.append({
            "name": name,
            "family": family,
            "module": module,
            "formula": "见实现模块" if name not in {
                "realized_variance", "rjv", "rljv", "rsjv", "ivhat"
            } else {
                "realized_variance": "Σ rᵢ²",
                "ivhat": "Tripower variation",
                "rjv": "max(RV − IVhat, 0)",
                "rljv": "大跳跃方差分量",
                "rsjv": "RJV − RLJV",
            }[name],
            "meaning": meaning,
        })
    for alias in ["h_daily_close60", "vol_rv"]:
        for metric in HERMITE_METRICS:
            result.append({
                "name": f"{alias}_{metric}",
                "family": "Hermite 元因子",
                "module": "hermite_factor_meta.py",
                "formula": metric,
                "meaning": "滚动因子分布的非高斯性与稳定性指标",
            })
    return result


def _demo_snapshot() -> dict[str, Any]:
    dates = _dates()
    series: list[dict[str, Any]] = []
    for ticker_index, ticker in enumerate(TICKERS):
        for metric in ["vol_rv_ts_closeness_60", "h_daily_close60_ts_h3_60", "h_daily_close60_ts_h4_60"]:
            values = []
            for index in range(len(dates)):
                wave = math.sin((index + ticker_index * 3) / 5.0)
                values.append(round(-1.2 + wave * 0.55 - ticker_index * 0.25, 4) if "closeness" in metric else round(wave * 0.35, 4))
            series.append({"ticker": ticker, "metric": metric, "dates": dates, "values": values})

    jump_decomposition = []
    for ticker_index, ticker in enumerate(TICKERS):
        rv = round(0.00042 + ticker_index * 0.00014, 6)
        ivhat = round(rv * 0.63, 6)
        rjv = round(rv - ivhat, 6)
        rljv = round(rjv * 0.58, 6)
        rsjv = round(rjv - rljv, 6)
        jump_decomposition.append({
            "ticker": ticker, "date": dates[-1], "rv": rv, "ivhat": ivhat,
            "rjv": rjv, "rljv": rljv, "rsjv": rsjv,
        })

    return {
        "schema_version": 1,
        "generated_at": "2026-09-11T00:00:00Z",
        "source": "demo",
        "datasets": [{"name": "demo snapshot", "date_start": dates[0], "date_end": dates[-1], "trading_days": len(dates), "tickers": len(TICKERS)}],
        "factor_groups": [
            {"name": "mf_volatility_32", "label": "分钟波动率与跳跃", "count": 32},
            {"name": "hermite_factor_meta", "label": "Hermite 体制元因子", "count": 48},
        ],
        "factors": _factor_metadata(),
        "series": series,
        "cross_section": [{"metric": "vol_rv_ts_closeness_60", "date": dates[-1], "count": 3, "p01": -2.0, "p25": -1.6, "p50": -1.2, "p75": -0.8, "p99": -0.4}],
        "jump_decomposition": jump_decomposition,
    }


def _real_snapshot(input_root: Path) -> dict[str, Any]:
    if not input_root.exists():
        raise FileNotFoundError(input_root)
    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError("读取真实 Parquet 需要 pandas 和 pyarrow；当前环境请使用 --demo") from exc
    paths = sorted(input_root.rglob("*.parquet"))
    if not paths:
        raise FileNotFoundError(f"未找到 Parquet 文件：{input_root}")
    factors: list[dict[str, Any]] = []
    series: list[dict[str, Any]] = []
    cross_section: list[dict[str, Any]] = []
    all_dates: set[str] = set()
    tickers: set[str] = set()
    for path in paths:
        frame = pd.read_parquet(path)
        required = {"date", "ticker"}
        if not required <= set(frame.columns):
            raise ValueError(f"{path} 缺少列：{sorted(required - set(frame.columns))}")
        value_columns = [column for column in frame.columns if column not in required]
        if len(value_columns) != 1:
            raise ValueError(f"{path} 无法推断唯一因子列，实际列：{value_columns}")
        name = value_columns[0]
        clean = frame[["date", "ticker", name]].copy()
        clean["ticker"] = clean["ticker"].astype(str).str.zfill(6)
        clean[name] = pd.to_numeric(clean[name], errors="coerce")
        clean = clean.dropna(subset=[name])
        if clean.empty:
            continue
        clean["date_text"] = pd.to_datetime(clean["date"].astype(str)).dt.strftime("%Y-%m-%d")
        dates = sorted(clean["date_text"].unique())
        sample_ticker = sorted(clean["ticker"].unique())[0]
        sample = clean[clean["ticker"] == sample_ticker].sort_values("date_text").tail(120)
        series.append({"ticker": sample_ticker, "metric": name, "dates": sample["date_text"].tolist(), "values": [_finite(value) for value in sample[name]]})
        values = clean[name].tolist()
        quantiles = clean[name].quantile([0.01, 0.25, 0.5, 0.75, 0.99])
        cross_section.append({"metric": name, "date": dates[-1], "count": int(len(clean)), "p01": _finite(quantiles.iloc[0]), "p25": _finite(quantiles.iloc[1]), "p50": _finite(quantiles.iloc[2]), "p75": _finite(quantiles.iloc[3]), "p99": _finite(quantiles.iloc[4])})
        factors.append({"name": name, "family": "Hermite 元因子" if "hermite" in path.parts else "分钟因子", "module": path.name, "formula": "见实现模块", "meaning": "来自 Parquet 快照的因子输出"})
        all_dates.update(dates)
        tickers.update(clean["ticker"].unique())
    return {
        "schema_version": 1, "generated_at": date.today().isoformat() + "T00:00:00Z", "source": "parquet",
        "datasets": [{"name": str(input_root), "date_start": min(all_dates), "date_end": max(all_dates), "trading_days": len(all_dates), "tickers": len(tickers)}],
        "factor_groups": [{"name": "parquet_snapshot", "label": "Parquet 因子快照", "count": len(factors)}],
        "factors": factors, "series": series, "cross_section": cross_section, "jump_decomposition": [],
    }


def build_snapshot(input_root: Path | None, output: Path, demo: bool = False) -> dict[str, Any]:
    snapshot = _demo_snapshot() if demo else _real_snapshot(input_root or Path("factor_results"))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n")
    return snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, default=None)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    build_snapshot(args.input_root, args.output, demo=args.demo)


if __name__ == "__main__":
    main()
