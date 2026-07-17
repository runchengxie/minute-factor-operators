#!/usr/bin/env python3
"""
波动率 / 跳跃 / 流动性因子 (32因子) - 分钟频

来源:
  - kfall F1105 波动跳跃: volume_volatility, ideal_swing_factor, star_volatility, log_volume_volatility
  - kfall F1107 流动性:   illiquidity, illiquidity_std, price_elasticity
  - kfall misc:           diff_abs_mean_volume, diff_abs_mean_amplitude, peak_count_1std/2std, vol_amplitude
  - base_stats 已实现波动率: realized_variance, realized_skewness, realized_kurtosis
  - jump_34 跳跃因子:     rv_pos, rv_neg, ivhat, rjv, rjvp, rjvn, sj, srjv,
                           gamma_threshold, rljv, rljvp, rljvn, srljv, rsjv, rsjvp, rsjvn, srsjv

使用方式:
    calc minute mf_volatility
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import warnings
import numpy as np
from math import gamma as math_gamma, sqrt, pi

warnings.filterwarnings('ignore')

from factor_utils import detect_backend

GROUP_NAME = 'mf_volatility_32'
COLUMNS = ['ticker', 'timestamp', 'open', 'high', 'low', 'close', 'volume']
HISTORY_DAYS = 0

MU_2_3 = (2 ** (1 / 3)) * math_gamma(5 / 6) / sqrt(pi)  # ≈ 0.8309

_FACTOR_NAMES = [
    # F1105 波动跳跃
    'volume_volatility', 'ideal_swing_factor', 'star_volatility', 'log_volume_volatility',
    # F1107 流动性
    'illiquidity', 'illiquidity_std', 'price_elasticity',
    # misc
    'diff_abs_mean_volume', 'diff_abs_mean_amplitude',
    'peak_count_1std', 'peak_count_2std', 'vol_amplitude',
    # 已实现波动率
    'realized_variance', 'realized_skewness', 'realized_kurtosis',
    # 跳跃因子
    'rv_pos', 'rv_neg', 'ivhat', 'rjv', 'rjvp', 'rjvn', 'sj', 'srjv',
    'gamma_threshold', 'rljv', 'rljvp', 'rljvn', 'srljv',
    'rsjv', 'rsjvp', 'rsjvn', 'srsjv',
]


# ══════════════════════════════════════════════════════════════════
#  单股因子计算
# ══════════════════════════════════════════════════════════════════

def _compute_stock(opn, high, low, close, volume):
    n = len(close)
    f = {}

    log_close = np.log(np.maximum(close, 1e-10))
    r = np.empty(n)
    r[0] = np.nan
    r[1:] = log_close[1:] - log_close[:-1]

    vol_valid = volume.copy()
    vol_valid[vol_valid <= 0] = np.nan
    vol_mean = np.nanmean(vol_valid)
    vol_std = np.nanstd(vol_valid)

    # ── F1105 波动跳跃 ────────────────────────────────────────────

    # 1. volume_volatility: CV of volume
    f['volume_volatility'] = float(vol_std / vol_mean) if vol_mean > 0 else np.nan

    # 2. ideal_swing_factor
    sorted_close = np.sort(close[~np.isnan(close)])
    nc = len(sorted_close)
    if nc >= 4:
        q = nc // 4
        bot25 = sorted_close[:q]
        top25 = sorted_close[-q:]
        swing_bot = bot25[-1] - bot25[0]
        swing_top = top25[-1] - top25[0]
        denom = swing_top + swing_bot
        f['ideal_swing_factor'] = float((swing_top - swing_bot) / denom) if denom > 0 else np.nan
    else:
        f['ideal_swing_factor'] = np.nan

    # 3. star_volatility: std of returns at star positions (vol_diff > mean + std)
    vol_diff = np.empty(n)
    vol_diff[0] = np.nan
    vol_diff[1:] = vol_valid[1:] - vol_valid[:-1]
    vd_valid = vol_diff[~np.isnan(vol_diff)]
    if len(vd_valid) > 1:
        vd_mean = np.mean(vd_valid)
        vd_std = np.std(vd_valid)
        star_mask = vol_diff > (vd_mean + vd_std)
        star_mask = star_mask & ~np.isnan(r)
        if np.sum(star_mask) > 1:
            f['star_volatility'] = float(np.std(r[star_mask]))
        else:
            f['star_volatility'] = np.nan
    else:
        f['star_volatility'] = np.nan

    # 4. log_volume_volatility
    log_vol = np.log(vol_valid + 10)
    lv = log_vol[~np.isnan(log_vol)]
    f['log_volume_volatility'] = float(np.std(lv)) if len(lv) > 1 else np.nan

    # ── F1107 流动性 ──────────────────────────────────────────────

    amount = close * volume
    amount_safe = np.where((amount > 0) & ~np.isnan(amount), amount, np.nan)

    spread = 2.0 * (high - low) - np.abs(close - opn)
    illiq_bar = spread / amount_safe
    illiq_vals = illiq_bar[~np.isnan(illiq_bar)]

    # 5. illiquidity
    f['illiquidity'] = float(np.mean(illiq_vals)) if len(illiq_vals) > 0 else np.nan
    # 6. illiquidity_std
    f['illiquidity_std'] = float(np.std(illiq_vals)) if len(illiq_vals) > 1 else np.nan

    # 7. price_elasticity
    hl_range = high - low
    pe_bar = hl_range / amount_safe
    pe_vals = pe_bar[~np.isnan(pe_bar)]
    f['price_elasticity'] = float(np.mean(pe_vals)) if len(pe_vals) > 0 else np.nan

    # ── misc ──────────────────────────────────────────────────────

    # 8. diff_abs_mean_volume
    d_vol = np.abs(np.diff(vol_valid))
    dv = d_vol[~np.isnan(d_vol)]
    f['diff_abs_mean_volume'] = float(np.mean(dv) / vol_mean) if (len(dv) > 0 and vol_mean > 0) else np.nan

    # 9. diff_abs_mean_amplitude
    amp = high - low
    amp_mean = np.nanmean(amp)
    d_amp = np.abs(np.diff(amp))
    da = d_amp[~np.isnan(d_amp)]
    f['diff_abs_mean_amplitude'] = float(np.mean(da) / amp_mean) if (len(da) > 0 and amp_mean > 0) else np.nan

    # 10/11. peak_count_1std, peak_count_2std
    for k_std, name in [(1, 'peak_count_1std'), (2, 'peak_count_2std')]:
        thr = vol_mean + k_std * vol_std
        if np.isnan(thr):
            f[name] = np.nan
            continue
        above = vol_valid > thr
        above = np.where(np.isnan(above), False, above)
        peaks = 0
        in_peak = False
        for i in range(n):
            if above[i]:
                if not in_peak:
                    peaks += 1
                    in_peak = True
            else:
                in_peak = False
        f[name] = float(peaks)

    # 12. vol_amplitude: std(high - low)
    amp_vals = amp[~np.isnan(amp)]
    f['vol_amplitude'] = float(np.std(amp_vals)) if len(amp_vals) > 1 else np.nan

    # ── 已实现波动率 ──────────────────────────────────────────────

    r_valid = r[~np.isnan(r)]
    N = len(r_valid)

    r2_sum = np.sum(r_valid ** 2)
    r3_sum = np.sum(r_valid ** 3)
    r4_sum = np.sum(r_valid ** 4)

    # 13. realized_variance
    f['realized_variance'] = float(r2_sum) if N > 0 else np.nan

    # 14. realized_skewness
    if N > 0 and r2_sum > 0:
        f['realized_skewness'] = float(sqrt(N) * r3_sum / (r2_sum ** 1.5))
    else:
        f['realized_skewness'] = np.nan

    # 15. realized_kurtosis
    if N > 0 and r2_sum > 0:
        f['realized_kurtosis'] = float(N * r4_sum / (r2_sum ** 2))
    else:
        f['realized_kurtosis'] = np.nan

    # ── 跳跃因子 (jump_34, alpha=4) ──────────────────────────────

    rv = r2_sum

    r_pos = np.where(r_valid > 0, r_valid, 0.0)
    r_neg = np.where(r_valid < 0, r_valid, 0.0)
    rv_pos = float(np.sum(r_pos ** 2))
    rv_neg = float(np.sum(r_neg ** 2))
    f['rv_pos'] = rv_pos
    f['rv_neg'] = rv_neg

    # ivhat: tripower variation
    if N >= 3:
        abs_r = np.abs(r_valid)
        abs_r_23 = abs_r ** (2.0 / 3.0)
        tri_sum = np.sum(abs_r_23[2:] * abs_r_23[1:-1] * abs_r_23[:-2])
        ivhat = float(tri_sum / (MU_2_3 ** 3))
    else:
        ivhat = np.nan
    f['ivhat'] = ivhat

    rjv = max(rv - ivhat, 0.0) if not np.isnan(ivhat) else np.nan
    rjvp = max(rv_pos - 0.5 * ivhat, 0.0) if not np.isnan(ivhat) else np.nan
    rjvn = max(rv_neg - 0.5 * ivhat, 0.0) if not np.isnan(ivhat) else np.nan
    sj = rv_pos - rv_neg

    f['rjv'] = rjv
    f['rjvp'] = rjvp
    f['rjvn'] = rjvn
    f['sj'] = sj
    f['srjv'] = (rjvp - rjvn) if not (np.isnan(rjvp) or np.isnan(rjvn)) else np.nan

    # large jump decomposition (alpha=4)
    alpha = 4.0
    if N > 0 and not np.isnan(ivhat) and ivhat >= 0:
        gamma = alpha * (N ** (-0.49)) * sqrt(ivhat)
    else:
        gamma = np.nan
    f['gamma_threshold'] = gamma

    if not np.isnan(gamma):
        large_mask = np.abs(r_valid) >= gamma
        rljv_raw = float(np.sum(r_valid[large_mask] ** 2))
        rljv = min(rjv, rljv_raw) if not np.isnan(rjv) else np.nan

        large_pos_mask = r_valid >= gamma
        rljvp_raw = float(np.sum(r_valid[large_pos_mask] ** 2))
        rljvp = min(rjvp, rljvp_raw) if not np.isnan(rjvp) else np.nan

        large_neg_mask = r_valid <= -gamma
        rljvn_raw = float(np.sum(r_valid[large_neg_mask] ** 2))
        rljvn = min(rjvn, rljvn_raw) if not np.isnan(rjvn) else np.nan
    else:
        rljv = rljvp = rljvn = np.nan

    f['rljv'] = rljv
    f['rljvp'] = rljvp
    f['rljvn'] = rljvn
    f['srljv'] = (rljvp - rljvn) if not (np.isnan(rljvp) or np.isnan(rljvn)) else np.nan

    rsjv = (rjv - rljv) if not (np.isnan(rjv) or np.isnan(rljv)) else np.nan
    rsjvp = (rjvp - rljvp) if not (np.isnan(rjvp) or np.isnan(rljvp)) else np.nan
    rsjvn = (rjvn - rljvn) if not (np.isnan(rjvn) or np.isnan(rljvn)) else np.nan

    f['rsjv'] = rsjv
    f['rsjvp'] = rsjvp
    f['rsjvn'] = rsjvn
    f['srsjv'] = (rsjvp - rsjvn) if not (np.isnan(rsjvp) or np.isnan(rsjvn)) else np.nan

    return f


# ══════════════════════════════════════════════════════════════════
#  框架入口
# ══════════════════════════════════════════════════════════════════

def compute_factor(df, date: int, history: dict) -> dict:
    results = {k: {} for k in _FACTOR_NAMES}

    backend = detect_backend(df)
    if backend != 'pandas':
        pdf = df.to_pandas()
    else:
        pdf = df

    pdf = pdf.sort_values(['ticker', 'timestamp']).reset_index(drop=True)

    for ticker, grp in pdf.groupby('ticker', sort=False):
        if len(grp) < 10:
            continue
        opn = grp['open'].values.astype(np.float64)
        high = grp['high'].values.astype(np.float64)
        low = grp['low'].values.astype(np.float64)
        close = grp['close'].values.astype(np.float64)
        volume = grp['volume'].values.astype(np.float64)

        stock_factors = _compute_stock(opn, high, low, close, volume)
        for k, v in stock_factors.items():
            results[k][ticker] = v

    return results
