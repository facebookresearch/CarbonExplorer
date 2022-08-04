# Copyright (c) Meta Platforms, Inc. and affiliates.
# This source code is licensed under the CC-BY-NC license found in the
# LICENSE file in the root directory of this source tree.

import pandas as pd

# Carbon Aware Scheduling Algorithm, to optimize for 24/7
# takes a dataframe that contains renewable and dc power, dc_all
# applies cas within the flexible_workload_ratio, and max_capacity constraints
# returns the carbon balanced version of the input dataframe, balanced_df
def cas(df_all, flexible_workload_ratio, max_capacity):
    # work on 24 hour basis
    # sort the df in terms of ascending renewable en
    # take flexible_workload_ratio from the highest carbon intensity hours
    # to lowest ones if there is not enough renewables until max_capacity is hit
    balanced_df = []
    for i in range(0, df_all.shape[0], 24):
        sorted_df = df_all[i : i + 24].sort_values(
            by=["tot_renewable", "avg_dc_power_mw"]
        )
        start = 0
        end = 23
        if sorted_df.shape[0] < 23:
            break
        work_to_move = 0
        while start < end:
            renewable_surplus = (
                sorted_df["tot_renewable"].iloc[end]
                - sorted_df["avg_dc_power_mw"].iloc[end]
            )
            renewable_gap = (
                sorted_df["avg_dc_power_mw"].iloc[start]
                - sorted_df["tot_renewable"].iloc[start]
            )
            available_space = min(
                renewable_surplus,
                (max_capacity - sorted_df["avg_dc_power_mw"].iloc[end]),
            )
            if renewable_surplus <= 0:
                end = end - 1
                continue
            if renewable_gap <= 0:
                start = start + 1
                continue
            if work_to_move <= 0 and renewable_gap > 0:
                work_to_move = min(
                    renewable_gap,
                    (
                        flexible_workload_ratio
                        / 100
                        * sorted_df["avg_dc_power_mw"].iloc[start]
                    ),
                )

            if available_space > work_to_move:
                sorted_df["avg_dc_power_mw"].iloc[end] = (
                    sorted_df["avg_dc_power_mw"].iloc[end]
                    + work_to_move
                )
                sorted_df["avg_dc_power_mw"].iloc[start] = (
                    sorted_df["avg_dc_power_mw"].iloc[start]
                    - work_to_move
                )
                start = start + 1
                work_to_move = 0
            else:
                sorted_df["avg_dc_power_mw"].iloc[end] = (
                    sorted_df["avg_dc_power_mw"].iloc[end]
                    + available_space
                )
                sorted_df["avg_dc_power_mw"].iloc[start] = (
                    sorted_df["avg_dc_power_mw"].iloc[start]
                    - available_space
                )
                work_to_move = work_to_move - available_space
                end = end - 1
        balanced_df.append(sorted_df)

    final_balanced_df = pd.concat(balanced_df).sort_values(by=["index"])
    return final_balanced_df


# Carbon Aware Scheduling Algorithm, to optimize for Grid Carbon Mix
def cas_grid_mix(df_all, flexible_workload_ratio, max_capacity):
    # work on 24 hour basis
    # work on 24 hour basis
    # sort the df in terms of ascending carbon
    # take flexible_workload_ratio from the highest carbon intensity hours
    # to lowest ones until max_capacity is hit
    # until avg carbon is hit or shifting does not reduce
    balanced_df = []
    for i in range(0, df_all.shape[0], 24):
        sorted_df = df_all[i : i + 24].sort_values(by=["carbon_intensity", "avg_dc_power_mw"])
        start = 0
        end = 23
        if sorted_df.shape[0] < 23:
            break
        work_to_move = 0
        while start < end:
            available_space = max_capacity - sorted_df["avg_dc_power_mw"].iloc[start]
            if work_to_move <= 0:
                work_to_move = flexible_workload_ratio / 100 * sorted_df["avg_dc_power_mw"].iloc[end]
            if available_space > work_to_move:
                sorted_df["avg_dc_power_mw"].iloc[start] = (
                    sorted_df["avg_dc_power_mw"].iloc[start] + work_to_move
                )
                sorted_df["avg_dc_power_mw"].iloc[end] = sorted_df["avg_dc_power_mw"].iloc[end] - work_to_move
                end = end - 1
                work_to_move = 0
            else:
                sorted_df["avg_dc_power_mw"].iloc[start] = max_capacity
                sorted_df["avg_dc_power_mw"].iloc[end] = (
                    sorted_df["avg_dc_power_mw"].iloc[end] - available_space
                )
                work_to_move = work_to_move - available_space
                start = start + 1
        balanced_df.append(sorted_df)

    final_balanced_df = pd.concat(balanced_df).sort_values(by=["index"])
    return final_balanced_df

