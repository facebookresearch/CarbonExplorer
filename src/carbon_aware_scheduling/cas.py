# Copyright (c) Meta Platforms, Inc. and affiliates.
# This source code is licensed under the CC-BY-NC license found in the
# LICENSE file in the root directory of this source tree.

import pandas as pd
from .cas_methods.sequential_search import cas_seq, seq_cas_grid_mix
from .cas_methods.binary_search import cas_binary, binary_cas_grid_mix
from .cas_methods.hybrid_search import cas_hybrid, hybrid_cas_grid_mix


def cas(
    df_all: pd.DataFrame,
    flexible_workload_ratio: float,
    max_capacity: float,
    objective: str = "renewable",
    search_method: str = "sequential",
) -> pd.DataFrame:
    """
        Factory function that selects the appropriate carbon aware scheduling method.
        The function takes a dataframe that contains renewable and dc power, dc_all
        applies cas within the flexible_workload_ratio, and max_capacity constraints
        returns the carbon balanced version of the input dataframe, balanced_df

    Args:
        df_all (pd.DataFrame): Dataframe containing renewable and dc power data.
        flexible_workload_ratio (float): Ratio of flexible workload to be moved.
        max_capacity (float): Maximum capacity for the scheduling.
        objective (str): Objective function to optimize for. Default is "renewable".
        search_method (str): Search method to use. Default is "sequential".
    Returns:
        pd.DataFrame: Carbon balanced version of the input dataframe.
    """

    if objective == "renewable":
        if search_method == "sequential":
            return cas_seq(df_all, flexible_workload_ratio, max_capacity)
        elif search_method == "binary":
            return cas_binary(df_all, flexible_workload_ratio, max_capacity)
        elif search_method == "hybrid":
            return cas_hybrid(df_all, flexible_workload_ratio, max_capacity)
        else:
            raise ValueError(
                "Invalid search method. Choose 'sequential', 'binary', or 'hybrid'."
            )
    elif objective == "grid_mix":
        if search_method == "sequential":
            return seq_cas_grid_mix(df_all, flexible_workload_ratio, max_capacity)
        elif search_method == "binary":
            return binary_cas_grid_mix(df_all, flexible_workload_ratio, max_capacity)
        elif search_method == "hybrid":
            return hybrid_cas_grid_mix(df_all, flexible_workload_ratio, max_capacity)
        else:
            raise ValueError(
                "Invalid search method. Choose 'sequential', 'binary', or 'hybrid'."
            )
    else:
        raise ValueError("Invalid objective. Choose 'renewable' or 'grid_mix'.")
