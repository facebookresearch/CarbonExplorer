# Copyright (c) Meta Platforms, Inc. and affiliates.
# This source code is licensed under the CC-BY-NC license found in the
# LICENSE file in the root directory of this source tree.

from ..battery import Battery, Battery2
import numpy as np


# return True if battery can meet all demand, False otherwise
def _sim_battery_247(df_ren, df_dc_pow, b):
    points_per_hour = 60

    for i in range(df_dc_pow.shape[0]):
        ren_mw = df_ren.iloc[i]
        df_dc = df_dc_pow["avg_dc_power_mw"].iloc[i]
        net_load = ren_mw - df_dc

        actual_discharge = 0
        # Apply the net power points_per_hour times
        for j in range(points_per_hour):
            # surplus, charge
            if net_load > 0:
                if isinstance(b, Battery):
                    b.charge(net_load)
                else:
                    b.charge(net_load, 1 / points_per_hour)
            else:
                # deficit, discharge
                if isinstance(b, Battery):
                    actual_discharge += b.discharge(-net_load)
                else:
                    actual_discharge += b.discharge(-net_load, 1 / points_per_hour)

        # check if actual dicharge was sufficient to meet net load (with some tolerance for imprecision)
        if net_load < 0 and actual_discharge < -net_load - 0.0001:
            return False  # Early termination - no need to continue simulation

    return True


# binary search for smallest battery size that meets all demand
def _calculate_247_battery_capacity_b2_bin(df_ren, df_dc_pow, max_bsize):

    # first check special case, no battery:
    if _sim_battery_247(df_ren, df_dc_pow, Battery2(0, 0)):
        return 0.0

    l = 0
    u = max_bsize
    while u - l > 0.1:
        med = (u + l) / 2.0
        if _sim_battery_247(df_ren, df_dc_pow, Battery2(med, med)):
            u = med
        else:
            l = med

    # check if max size was too small
    if u == max_bsize:
        return np.nan
    return u


# binary search for smallest battery size that meets all demand
def _calculate_247_battery_capacity_b1_bin(df_ren, df_dc_pow, max_bsize):

    # first check special case, no battery:
    if _sim_battery_247(df_ren, df_dc_pow, Battery(0, 0)):
        return 0.0

    l = 0
    u = max_bsize
    while u - l > 0.1:
        med = (u + l) / 2.0
        if _sim_battery_247(df_ren, df_dc_pow, Battery(med, med)):
            u = med
        else:
            l = med

    # check if max size was too small
    if u == max_bsize:
        return np.nan
    return u
