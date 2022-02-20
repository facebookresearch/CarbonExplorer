# Copyright (c) Meta Platforms, Inc. and affiliates.
# This source code is licensed under the CC-BY-NC license found in the
# LICENSE file in the root directory of this source tree.

import numpy as np

class Battery:
    capacity = 0 # Max MWh storage capacity
    current_load = 0 # Current load in the battery, in MWh

    def __init__(self, capacity, current_load=0):
        self.capacity = capacity
        self.current_load = current_load

    # charge the battery based on an hourly load
    # returns the total load after charging with input_load
    def charge(self, input_load):
        self.current_load = self.current_load + input_load
        if(self.current_load > self.capacity):
            self.current_load = self.capacity
        return self.current_load

    # returns how much energy is discharged when
    # output_load is drawn from the battery in an hour
    def discharge(self, output_load):
        self.current_load = self.current_load - output_load
        if(self.current_load < 0): # not enough battery load
            lacking_amount = self.current_load
            self.current_load = 0
            return output_load + lacking_amount
        return output_load

    def is_full(self):
        return (self.capacity == self.current_load)
    
    # calculate the minimum battery capacity required
    # to be able to charge it with input_load
    # amount of energy within an hour and
    # expand the existing capacity with that amount
    def find_and_init_capacity(self, input_load):
        self.capacity = self.capacity + input_load
        
# Takes renewable supply and dc power as input dataframes
# returns how much battery capacity is needed to make
# dc operate on renewables 24/7
def calculate_247_battery_capacity(df_ren, df_dc_pow):
    battery_cap = 0 # return value stored here, capacity needed
    daily_net_load = 0 # for calculating infeasible cases
    b = Battery(0) # start with an empty battery

    for i in range(df_dc_pow.shape[0]):
        ren_mw = df_ren[i]
        df_dc = df_dc_pow["avg_dc_power_mw"][i]
        daily_net_load += ren_mw - df_dc

        if df_dc > ren_mw:  # if there's not enough renewable supply, need to discharge
            if(b.capacity == 0):
                b.find_and_init_capacity(df_dc - ren_mw) # find how much battery cap needs to be
            else:
                load_before = b.current_load
                if(load_before == 0):
                    b.find_and_init_capacity(df_dc - ren_mw)
                else:
                    b.discharge(df_dc - ren_mw)
                    load_after = b.current_load
                    if(load_after == 0):
                        b.find_and_init_capacity((df_dc - ren_mw) - load_before)
        else:  # there's excess renewable supply, charge batteries
            if b.capacity > 0:
                b.charge(ren_mw-df_dc)
            elif b.is_full():
                b = Battery(0)

        if b.capacity > 0 and battery_cap != np.nan:
            battery_cap = max(battery_cap, b.capacity)
 
        # daily check, battery impossible case
        # if the battery cannot be filled fully in 3 days, assume it's infeasible
        # return np.nan
        if (i + 1) % 72 == 0:
            if daily_net_load < 0:
                battery_cap = np.nan
                break
            else:
                daily_net_load = 0

    return battery_cap

# Takes battery capacity, renewable supply and dc power as input dataframes
# and calculates how much battery can increase renewable coverage
# returns the non renewable amount that battery cannot cover
def apply_battery(battery_capacity, df_ren, df_dc_pow):
    b = Battery(battery_capacity, battery_capacity)
    tot_non_ren_mw = 0 # store the mw amount battery cannot supply here

    for i in range(df_dc_pow.shape[0]):
        ren_mw = df_ren[i]
        df_dc = df_dc_pow["avg_dc_power_mw"][i]
        gap = df_dc - ren_mw
        # lack or excess renewable supply
        if gap > 0: #discharging from battery
            discharged_amount = b.discharge(gap)
            tot_non_ren_mw = tot_non_ren_mw + gap - discharged_amount
        else: # charging the battery
            b.charge(-gap)

    return tot_non_ren_mw

