# Copyright (c) Meta Platforms, Inc. and affiliates.
# This source code is licensed under the CC-BY-NC license found in the
# LICENSE file in the root directory of this source tree.

# return True if battery can meet all demand, False otherwise
from ..battery import Battery, Battery2
import numpy as np


def _calculate_247_battery_capacity_b1_seq(df_ren, df_dc_pow) -> float:
    battery_cap = 0  # return value stored here, capacity needed
    b = Battery(0, 0)

    for i in range(df_dc_pow.shape[0]):
        ren_mw = df_ren.iloc[i]
        df_dc = df_dc_pow["avg_dc_power_mw"].iloc[i]

        if df_dc > ren_mw:  # if there's not enough renewable supply, need to discharge
            if b.capacity == 0:
                b.find_and_init_capacity(
                    df_dc - ren_mw
                )  # find how much battery cap needs to be
            else:
                load_before = b.current_load
                if load_before == 0:
                    b.find_and_init_capacity(df_dc - ren_mw)
                else:
                    drawn_amount = b.discharge(df_dc - ren_mw)
                    if drawn_amount < (df_dc - ren_mw):
                        b.find_and_init_capacity((df_dc - ren_mw) - drawn_amount)
        else:  # there's excess renewable supply, charge batteries
            if b.capacity > 0:
                b.charge(ren_mw - df_dc)
            elif b.is_full():
                b = Battery(0)

        if b.capacity > 0 and battery_cap != np.nan:
            battery_cap = max(battery_cap, b.capacity)

    return battery_cap


def _calculate_247_battery_capacity_b2_seq(df_ren, df_dc_pow) -> float:
    points_per_hour = 60
    battery_cap = 0  # return value stored here, capacity needed
    b = Battery2(0, 0)

    for i in range(df_dc_pow.shape[0]):
        ren_mw = df_ren.iloc[i]
        df_dc = df_dc_pow["avg_dc_power_mw"].iloc[i]

        if df_dc > ren_mw:  # if there's not enough renewable supply, need to discharge
            if b.capacity == 0:
                b.find_and_init_capacity(
                    df_dc - ren_mw
                )  # find how much battery cap needs to be
            else:
                load_before = b.current_load
                if load_before == 0:
                    b.find_and_init_capacity(df_dc - ren_mw)
                else:
                    drawn_amount = b.discharge(df_dc - ren_mw, 1 / points_per_hour)
                    if drawn_amount < (df_dc - ren_mw):
                        b.find_and_init_capacity((df_dc - ren_mw) - drawn_amount)
        else:  # there's excess renewable supply, charge batteries
            if b.capacity > 0:
                b.charge(ren_mw - df_dc, 1 / points_per_hour)
            elif b.is_full():
                b = Battery2(0)

        if b.capacity > 0 and battery_cap != np.nan:
            battery_cap = max(battery_cap, b.capacity)

    return battery_cap
