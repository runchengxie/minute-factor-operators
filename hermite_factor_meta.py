#!/usr/bin/env python3
"""
Hermite factor-of-factors meta features.

For a selected set of existing alpha/microstructure panels, treat each stock's
recent factor time series as a local distribution around a Gaussian sector.
Rolling Hermite h3/h4 amplitudes describe non-Gaussian instability of that
factor state; closeness/compression features are intended as regime/stability
modulators for downstream ML models.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

GROUP_NAME = "hermite_factor_meta"
COLUMNS = ["returns"]

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FACTOR_ROOT = PROJECT_ROOT / "factor_results"

WINDOW_LONG = 60
WINDOW_SHORT = 20
MIN_LONG = 36
MIN_SHORT = 12

# Keep this deliberately compact: enough diversity for ML, without exploding
# candidate count or disk footprint.
SOURCE_FACTORS: list[tuple[str, str, str]] = [
    ("h_daily_close60", "hermite_information_rg", "hermite_gaussian_closeness_60"),
    ("h_l2_ret20", "mf_hermite_information_rg", "mf_hermite_ret_closeness_20"),
    ("h_l2_vwret20", "mf_hermite_information_rg", "mf_hermite_vwret_closeness_20"),
    ("h_l2_tail20", "mf_hermite_information_rg", "mf_hermite_tail_stability_20"),
    ("pv_down_amt", "mf_price_volume_pressure_24", "pv_down_amount_share"),
    ("pv_top_amt", "mf_price_volume_pressure_24", "pv_amount_concentration_top10"),
    ("vol_rv", "mf_volatility_32", "realized_variance"),
    ("vol_kurt", "mf_volatility_32", "realized_kurtosis"),
    ("dist_large_kurt", "mf_distribution_22", "large_volume_kurtosis"),
    ("order_cancel", "order_flow_20", "cancel_buy_sell_vol_imbalance_20d"),
    ("trade_active_buy", "trade_informed_flow_20", "active_buy_share_all_20d"),
    ("daily_tail_beta", "daily_alpha_6", "tail_beta"),
]


def _load_factor_panel(group: str, name: str) -> pd.DataFrame:
    path = FACTOR_ROOT / group / f"{name}.parquet"
    if not path.exists():
        raise FileNotFoundError(path)
    df = pd.read_parquet(path)
    if {"date", "ticker"}.issubset(df.columns):
        value_cols = [c for c in df.columns if c not in ("date", "ticker")]
        if len(value_cols) != 1:
            raise ValueError(f"Cannot infer value column for {path}")
        df = df.pivot(index="date", columns="ticker", values=value_cols[0])
    elif "value" in df.columns:
        df = df.set_index("value")
    df.index = pd.Index(df.index).astype(int)
    df.columns = pd.Index(df.columns).astype(str).str.zfill(6)
    df = df.loc[:, ~df.columns.duplicated()].sort_index()
    return df.replace([np.inf, -np.inf], np.nan).astype(np.float32)


def _rolling_zscore(panel: pd.DataFrame, window: int, min_periods: int) -> pd.DataFrame:
    mean = panel.rolling(window, min_periods=min_periods).mean()
    std = panel.rolling(window, min_periods=min_periods).std(ddof=0)
    std = std.where(std > 1e-8)
    return ((panel - mean) / std).clip(-8.0, 8.0)


def _hermite_energy(panel: pd.DataFrame, window: int, min_periods: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    z = _rolling_zscore(panel, window, min_periods)
    z2 = z * z
    h3_raw = (z * z2 - 3.0 * z) / np.sqrt(6.0)
    h4_raw = (z2 * z2 - 6.0 * z2 + 3.0) / np.sqrt(24.0)
    h3 = h3_raw.rolling(window, min_periods=min_periods).mean()
    h4 = h4_raw.rolling(window, min_periods=min_periods).mean()
    energy = h3.pow(2) + h4.pow(2)
    return h3, h4, energy


def compute_factors(data: dict) -> dict[str, pd.DataFrame]:
    returns = data["returns"]
    out: dict[str, pd.DataFrame] = {}

    for idx, (alias, group, name) in enumerate(SOURCE_FACTORS, start=1):
        print(f"  [{idx}/{len(SOURCE_FACTORS)}] {alias}: {group}/{name}")
        panel = _load_factor_panel(group, name)
        # Align to the common daily calendar so downstream labels line up.
        panel = panel.reindex(index=returns.index)

        h3_60, h4_60, energy_60 = _hermite_energy(panel, WINDOW_LONG, MIN_LONG)
        _, _, energy_20 = _hermite_energy(panel, WINDOW_SHORT, MIN_SHORT)

        out[f"{alias}_ts_h3_60"] = h3_60
        out[f"{alias}_ts_h4_60"] = h4_60
        out[f"{alias}_ts_closeness_60"] = -np.log1p(energy_60)
        out[f"{alias}_energy_compression_20_60"] = np.log1p(energy_60) - np.log1p(energy_20)

    return out
