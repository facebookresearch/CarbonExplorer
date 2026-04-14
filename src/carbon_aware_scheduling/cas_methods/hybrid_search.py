# Copyright (c) Meta Platforms, Inc. and affiliates.
# This source code is licensed under the CC-BY-NC license found in the
# LICENSE file in the root directory of this source tree.

import numpy as np
import pandas as pd


def cas_hybrid(
    df_all: pd.DataFrame, flexible_workload_ratio: float, max_capacity: float
):
    """
    Hybrid 24/7 search:
    1) compute total movable = ratio * sum(power)
    2) sort deficits descending, prefix‐sum to pick minimal set of donors
    3) sort surpluses by available capacity, greedy pour
    """
    balanced = []
    ratio = flexible_workload_ratio / 100.0

    for i in range(0, len(df_all), 24):
        day = df_all.iloc[i : i + 24]
        if len(day) < 24:
            break

        power = day["avg_dc_power_mw"].to_numpy()
        ren = day["tot_renewable"].to_numpy()
        deficits = np.maximum(0, power - ren)
        surpluses = np.maximum(0, ren - power)
        total_mov = power.sum() * ratio

        # pick minimal donors by prefix‐sum over sorted deficits
        def_idx = np.argsort(-deficits)
        cdef = np.cumsum(deficits[def_idx])
        k = np.searchsorted(cdef, total_mov, side="right") + 1
        donors = def_idx[:k]

        # compute available headroom per hour
        headroom = np.minimum(surpluses, max_capacity - power)
        recips = np.argsort(-headroom)

        # one‐pass pour from donors→recips
        moved = 0.0
        new_power = power.copy()
        for d in donors:
            can = min(deficits[d], total_mov - moved)
            if can <= 0:
                break
            for r in recips:
                space = headroom[r]
                if space <= 0:
                    continue
                amt = min(can, space)
                new_power[d] -= amt
                new_power[r] += amt
                moved += amt
                headroom[r] -= amt
                if moved >= total_mov:
                    break
            if moved >= total_mov:
                break

        out = day.copy()
        out["avg_dc_power_mw"] = new_power
        balanced.append(out)

    return pd.concat(balanced).sort_index()


def hybrid_cas_grid_mix(
    df_all: pd.DataFrame, flexible_workload_ratio: float, max_capacity: float
):
    """
    Hybrid grid‐mix search:
    1) compute total movable = ratio * sum(power)
    2) sort donor hours by carbon desc, recipient by carbon asc
    3) greedy pour limited by headroom
    """
    balanced = []
    ratio = flexible_workload_ratio / 100.0

    for i in range(0, len(df_all), 24):
        day = df_all.iloc[i : i + 24]
        if len(day) < 24:
            break

        power = day["avg_dc_power_mw"].to_numpy()
        ci = day["carbon_intensity"].to_numpy()
        total_mov = power.sum() * ratio

        donors = np.argsort(-ci)
        recips = np.argsort(ci)
        headroom = max_capacity - power
        headroom = np.where(headroom > 0, headroom, 0)

        moved = 0.0
        new_power = power.copy()
        for d in donors:
            can = min(power[d] * ratio, total_mov - moved)
            if can <= 0:
                continue
            for r in recips:
                space = headroom[r]
                if space <= 0:
                    continue
                amt = min(can, space)
                new_power[d] -= amt
                new_power[r] += amt
                moved += amt
                headroom[r] -= amt
                if moved >= total_mov:
                    break
            if moved >= total_mov:
                break

        out = day.copy()
        out["avg_dc_power_mw"] = new_power
        balanced.append(out)

    return pd.concat(balanced).sort_index()
