# Copyright (c) Meta Platforms, Inc. and affiliates.
# This source code is licensed under the CC-BY-NC license found in the
# LICENSE file in the root directory of this source tree.

import pandas as pd
import numpy as np


def cas_binary(
    df_all: pd.DataFrame,
    flexible_workload_ratio: float,
    max_capacity: float,
):
    """
    Carbon Aware Scheduling Algorithm using binary search.
    Optimizes for 24/7 carbon-aware scheduling.

    Args:
        df_all (pd.DataFrame): Dataframe containing renewable and dc power data.
        flexible_workload_ratio (float): Ratio of flexible workload to be moved.
        max_capacity (float): Maximum capacity for the scheduling.

    Returns:
        pd.DataFrame: Carbon balanced version of the input dataframe.
    """
    balanced_days = []
    ratio = flexible_workload_ratio / 100.0

    for i in range(0, len(df_all), 24):
        day = df_all.iloc[i : i + 24]
        if len(day) < 24:
            break

        power = day["avg_dc_power_mw"].to_numpy()
        ren = day["tot_renewable"].to_numpy()
        # total workload we want to move
        total_movable = power.sum() * ratio

        # deficits (donors) and surpluses (recipients)
        deficits = np.maximum(0, power - ren)
        surpluses = np.maximum(0, ren - power)  # available renewable headroom

        # sort donor hours by largest deficit
        donor_idx = np.argsort(-deficits)
        cum_def = np.cumsum(deficits[donor_idx])
        # find minimal number of donors to cover total_movable
        k = np.searchsorted(cum_def, total_movable, side="right") + 1
        selected_donors = donor_idx[:k]

        # sort recipient hours by largest surplus and capacity
        # note: capacity also limited by max_capacity - current_power
        cap_space = np.minimum(surpluses, max_capacity - power)
        recip_idx = np.argsort(-cap_space)

        # now move work
        moved = 0.0
        new_power = power.copy()
        for d in selected_donors:
            can_move = min(deficits[d], total_movable - moved)
            if can_move <= 0:
                break
            # pour into recipients
            for r in recip_idx:
                space = cap_space[r]
                if space <= 0:
                    continue
                amt = min(can_move, space)
                new_power[d] -= amt
                new_power[r] += amt
                moved += amt
                cap_space[r] -= amt
                if moved >= total_movable:
                    break
            if moved >= total_movable:
                break

        day_balanced = day.copy()
        day_balanced["avg_dc_power_mw"] = new_power
        balanced_days.append(day_balanced)

    return pd.concat(balanced_days).sort_index()


def binary_cas_grid_mix(df_all, flexible_workload_ratio, max_capacity):
    """Binary search approach for carbon intensity optimization"""
    ratio = flexible_workload_ratio / 100.0
    balanced = []

    for i in range(0, len(df_all), 24):
        day = df_all.iloc[i : i + 24]
        if len(day) < 24:
            break

        power = day["avg_dc_power_mw"].to_numpy()
        ci = day["carbon_intensity"].to_numpy()

        # how much each hour _could_ move out
        movable = power * ratio

        # donor hours: highest carbon first
        donors = np.argsort(-ci)
        # recipient hours: lowest carbon first
        recips = np.argsort(ci)

        new_power = power.copy()

        # greedy move from donors→recips
        for d in donors:
            to_move = movable[d]
            if to_move <= 0:
                continue
            for r in recips:
                headroom = max_capacity - new_power[r]
                if headroom <= 0:
                    continue
                amt = min(to_move, headroom)
                new_power[d] -= amt
                new_power[r] += amt
                to_move -= amt
                if to_move <= 0:
                    break
            # if we moved everything possible, stop early
            if new_power[d] <= power[d] * (1 - ratio):
                continue

        # write back
        day_balanced = day.copy()
        day_balanced["avg_dc_power_mw"] = new_power
        balanced.append(day_balanced)

    return pd.concat(balanced).sort_index()
