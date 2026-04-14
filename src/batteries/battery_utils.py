# Copyright (c) Meta Platforms, Inc. and affiliates.
# This source code is licensed under the CC-BY-NC license found in the
# LICENSE file in the root directory of this source tree.

from .battery_methods.hybrid_search import (
    _calculate_247_battery_capacity_b1_hybrid,
    _calculate_247_battery_capacity_b2_hybrid,
)
from .battery_methods.binary_search import (
    _calculate_247_battery_capacity_b1_bin,
    _calculate_247_battery_capacity_b2_bin,
)
from .battery_methods.sequential_search import (
    _calculate_247_battery_capacity_b1_seq,
    _calculate_247_battery_capacity_b2_seq,
)
from .battery import Battery2


# Takes renewable supply and dc power as input dataframes
# returns how much battery capacity is needed to make
# dc operate on renewables 24/7
def calculate_247_battery_capacity(
    df_ren, df_dc_pow, search="sequential", battery_type="b1", max_bsize=1000
):
    battery_cap = 0  # return value stored here, capacity needed

    match search:
        case "sequential":
            if battery_type == "b1":
                battery_cap = _calculate_247_battery_capacity_b1_seq(df_ren, df_dc_pow)
            else:
                battery_cap = _calculate_247_battery_capacity_b2_seq(df_ren, df_dc_pow)
        case "binary":
            if battery_type == "b1":
                battery_cap = _calculate_247_battery_capacity_b1_bin(
                    df_ren, df_dc_pow, max_bsize
                )
            else:
                battery_cap = _calculate_247_battery_capacity_b2_bin(
                    df_ren, df_dc_pow, max_bsize
                )
        case "hybrid":
            if battery_type == "b1":
                battery_cap = _calculate_247_battery_capacity_b1_hybrid(
                    df_ren, df_dc_pow, max_bsize
                )
            else:
                battery_cap = _calculate_247_battery_capacity_b2_hybrid(
                    df_ren, df_dc_pow, max_bsize
                )
            pass
        case _:
            raise ValueError(
                "Invalid search method. Choose 'sequential', 'binary', or 'hybrid'."
            )

    return battery_cap


# Takes battery capacity, renewable supply and dc power as input dataframes
# and calculates how much battery can increase renewable coverage
# returns the non renewable amount that battery cannot cover
def apply_battery(battery_capacity, df_ren, df_dc_pow):
    b = Battery2(battery_capacity, battery_capacity)
    tot_non_ren_mw = 0  # store the mw amount battery cannot supply here

    points_per_hour = 60
    for i in range(df_dc_pow.shape[0]):
        ren_mw = df_ren.iloc[i]
        df_dc = df_dc_pow["avg_dc_power_mw"].iloc[i]
        gap = df_dc - ren_mw
        discharged_amount = 0
        for j in range(points_per_hour):
            # lack or excess renewable supply
            if gap > 0:  # discharging from battery
                discharged_amount += b.discharge(gap, 1 / points_per_hour)
            else:  # charging the battery
                b.charge(-gap, 1 / points_per_hour)
                df_ren.iloc[i] += gap * (
                    1 / points_per_hour
                )  # decrease the available renewable energy
        if gap > 0:
            tot_non_ren_mw = tot_non_ren_mw + gap - discharged_amount
            df_ren.iloc[
                i
            ] += (
                discharged_amount  # increase the renewables available by the discharged
            )
    return tot_non_ren_mw, df_ren
