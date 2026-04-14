# Copyright (c) Meta Platforms, Inc. and affiliates.
# This source code is licensed under the CC-BY-NC license found in the
# LICENSE file in the root directory of this source tree.

import numpy as np


class Battery:
    capacity = 0  # Max MWh storage capacity
    current_load = 0  # Current load in the battery, in MWh

    def __init__(self, capacity, current_load=0):
        self.capacity = capacity
        self.current_load = current_load

    # charge the battery based on an hourly load
    # returns the total load after charging with input_load
    def charge(self, input_load):
        self.current_load = self.current_load + input_load
        if self.current_load > self.capacity:
            self.current_load = self.capacity
        return self.current_load

    # returns how much energy is discharged when
    # output_load is drawn from the battery in an hour
    def discharge(self, output_load):
        self.current_load = self.current_load - output_load
        if self.current_load < 0:  # not enough battery load
            lacking_amount = self.current_load
            self.current_load = 0
            return output_load + lacking_amount
        return output_load

    def is_full(self):
        return self.capacity == self.current_load

    # calculate the minimum battery capacity required
    # to be able to charge it with input_load
    # amount of energy within an hour and
    # expand the existing capacity with that amount
    def find_and_init_capacity(self, input_load):
        self.capacity = self.capacity + input_load


# Battery model that includes efficiency and
# linear charging/discharging rate limits with respect to battery capacity
# refer to C/L/C model in following reference for details:
# "Tractable lithium-ion storage models for optimizing energy systems."
# Energy Informatics 2.1 (2019): 1-22.
class Battery2:
    capacity = 0  # Max MWh storage capacity
    current_load = 0  # Current load in the battery, in MWh

    # charging and discharging efficiency, including DC-AC inverter loss
    eff_c = 1
    eff_d = 1

    c_lim = 3
    d_lim = 3

    # Maximum charging energy in one time step
    # is limited by (u * applied power) + v
    upper_lim_u = 0
    upper_lim_v = 1

    # Maximum discharged energy in one time step
    # is limited by (u * applied power) + v
    lower_lim_u = 0
    lower_lim_v = 0

    # NMC: eff_c = 0.98, eff_d = 1.05,
    #             c_lim = 3, d_lim = 3,
    #             upper_u = -0.125, upper_v = 1,
    #             lower_u = 0.05, lower_v = 0

    # defaults for lithium NMC cell
    def __init__(
        self,
        capacity,
        current_load=0,
        eff_c=0.97,
        eff_d=1.04,
        c_lim=3,
        d_lim=3,
        upper_u=-0.04,
        upper_v=1,
        lower_u=0.01,
        lower_v=0,
    ):
        self.capacity = capacity
        self.current_load = current_load

        self.eff_c = eff_c
        self.eff_d = eff_d
        self.c_lim = c_lim
        self.d_lim = d_lim
        self.upper_lim_u = upper_u
        self.upper_lim_v = upper_v
        self.lower_lim_u = lower_u
        self.lower_lim_v = lower_v

    def calc_max_charge(self, T_u):

        # energy content in current (next) time step: b_k (b_{k+1}, which is just b_k + p_k*eff_c)
        # charging power in current time step: p_k
        # b_{k+1} <= u * p_k + v is equivalent to
        # p_k <= (v - b_k) / (eff_c - u)
        max_charge = min(
            (self.capacity / self.eff_c) * self.c_lim,
            (self.upper_lim_v * self.capacity - self.current_load)
            / ((self.eff_c * T_u) - self.upper_lim_u),
        )
        return max_charge

    def calc_max_discharge(self, T_u):

        # energy content in current (next) time step: b_k (b_{k+1}, which is just b_k - p_k*eff_d)
        # charging power in current time step: p_k
        # b_{k+1} <= u * p_k + v is equivalent to
        # p_k <= (b_k - v) / (u + eff_d)
        max_discharge = min(
            (self.capacity / self.eff_d) * self.d_lim,
            (self.current_load - self.lower_lim_v * self.capacity)
            / (self.lower_lim_u + (self.eff_d * T_u)),
        )
        return max_discharge

    # charge the battery based on an hourly load
    # returns the total load after charging with input_load
    def charge(self, input_load, T_u):
        max_charge = self.calc_max_charge(T_u)
        self.current_load = self.current_load + (
            min(max_charge, input_load) * self.eff_c * T_u
        )
        return self.current_load

    # returns how much energy is discharged when
    # output_load is drawn from the battery over T_u hours (default T_u is 1/60)
    def discharge(self, output_load, T_u):
        max_discharge = self.calc_max_discharge(T_u)
        self.current_load = self.current_load - (
            min(max_discharge, output_load) * self.eff_d * T_u
        )
        if max_discharge < output_load:  # not enough battery load
            return max_discharge * T_u
        return output_load * T_u

    def is_full(self):
        return self.capacity == self.current_load

    # calculate the minimum battery capacity required
    # to be able to charge it with input_load
    # amount of energy within an hour and
    # expand the existing capacity with that amount
    def find_and_init_capacity(self, input_load):

        self.capacity = self.capacity + input_load * self.eff_d

        # increase the capacity until we can discharge input_load
        # TODO: find analytical value for this
        new_capacity = input_load * self.eff_d
        while True:
            power_lim = (new_capacity - self.lower_lim_v * self.capacity) / (
                self.lower_lim_u + self.eff_d
            )
            if power_lim < input_load:
                self.capacity += 0.1
                new_capacity += 0.1
            else:
                break



