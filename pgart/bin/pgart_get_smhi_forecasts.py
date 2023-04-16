#!/usr/bin/python3
# This file is part of PGART_T (Pump Gradual Adjustment Room Temperature for Thermia Atlas).

# Copyright (C) 2023 PG Andersson <pg.andersson@gmail.com>.

# pgart_t is free software: you can redistribute it and/or modify it under the terms of GPL-3.0-or-later

# Downloads forecasts from SMHI

import os
import sys

import pgart_misc_func as f0
import pgart_get_smhi_forecasts_func as f2
import time

max_nr_get_request_trials = 2

my_lat, my_lon, wind_force_factor, logreq, max_log_len = f0.get_args_forecasts_from_smhi()
print(my_lat, my_lon, wind_force_factor, logreq, max_log_len)

nr_trials = 1
more = True
while more :
    if f2.get_forecasts_from_smhi(my_lat, my_lon, wind_force_factor, logreq, max_log_len) :
        f0.print_forecast_short()
        sys.stdout.flush()
        exit()
    else :
        if nr_trials == max_nr_get_request_trials :
            print("-ok")
            exit()
        time.sleep(55)       # Try once more after a while.

    nr_trials += 1
