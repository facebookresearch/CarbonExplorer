# Copyright (c) Meta Platforms, Inc. and affiliates.
# This source code is licensed under the CC-BY-NC license found in the
# LICENSE file in the root directory of this source tree.

from ..battery import Battery, Battery2
import numpy as np
from .binary_search import _sim_battery_247
import pandas as pd

# https://www.baeldung.com/cs/exponential-search


def _calculate_247_battery_capacity_b1_hybrid(
    df_ren: pd.DataFrame, df_dc_pow: pd.DataFrame, max_bsize: int
) -> float:

    # Battery empty
    if _sim_battery_247(df_ren, df_dc_pow, Battery(0, 0)):
        return 0.0

    lower_bound = 0.0
    upper_bound = 2.0

    # Iterate quickly to narrow search space
    while upper_bound < max_bsize and not _sim_battery_247(
        df_ren, df_dc_pow, Battery(upper_bound, upper_bound)
    ):
        lower_bound = upper_bound
        upper_bound *= 2

    # Cap the upper bound to max_bsize
    if upper_bound > max_bsize:
        upper_bound = max_bsize

    # If we hit max_bsize and still can't satisfy the demand
    if not _sim_battery_247(df_ren, df_dc_pow, Battery(upper_bound, upper_bound)):
        return np.nan

    # Binary search on smaller search space
    while upper_bound - lower_bound > 0.1:
        mid = (lower_bound + upper_bound) / 2.0
        if _sim_battery_247(df_ren, df_dc_pow, Battery(mid, mid)):
            upper_bound = mid
        else:
            lower_bound = mid

    return upper_bound


def _calculate_247_battery_capacity_b2_hybrid(
    df_ren: pd.DataFrame, df_dc_pow: pd.DataFrame, max_bsize: int
) -> float:

    # Battery empty
    if _sim_battery_247(df_ren, df_dc_pow, Battery2(0, 0)):
        return 0.0

    lower_bound = 0.0
    upper_bound = 1.0

    # Iterate quickly to narrow search space
    while upper_bound < max_bsize and not _sim_battery_247(
        df_ren, df_dc_pow, Battery2(upper_bound, upper_bound)
    ):
        lower_bound = upper_bound
        upper_bound *= 2

    # Cap the upper bound to max_bsize
    if upper_bound > max_bsize:
        upper_bound = max_bsize

    # If we hit max_bsize and still can't satisfy the demand
    if not _sim_battery_247(df_ren, df_dc_pow, Battery2(upper_bound, upper_bound)):
        return np.nan

    # Binary search on smaller search space
    while upper_bound - lower_bound > 0.1:
        mid = (lower_bound + upper_bound) / 2.0
        if _sim_battery_247(df_ren, df_dc_pow, Battery2(mid, mid)):
            upper_bound = mid
        else:
            lower_bound = mid

    return upper_bound
