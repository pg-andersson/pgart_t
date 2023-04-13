#!/usr/bin/python3
# This file is part of PGART_T (Pump Gradual Adjustment Room Temperature for Thermia Atlas).

# Copyright (C) 2023 PG Andersson <pg.andersson@gmail.com>.

# pgart_t is free software: you can redistribute it and/or modify it under the terms of GPL-3.0-or-later

# Functions to create an indoor temperature adjustments schedule based on hourly rates.

from pathlib import Path

import pgart_misc_func as f0

g_schedules = []

def get_price_per_hour_range(fi_hourly_rate, start_hr, stop_hr) :
    hr_rates = f0.get_hourly_rates(fi_hourly_rate)
    price_per_hour = []
    for h, r in hr_rates.items() :
        if h >= start_hr and h < stop_hr :
            price_per_hour.append(r)

    return(price_per_hour)


def add_schedule(a,b,c,d,e,f,g,h,i,j,k,l, first_hour, start_hr, stop_hr):
    global g_schedules
    nr_hours = stop_hr - start_hr
    total = a + b + c + d + e + f + g + h + i +j +k + l
    if total < nr_hours:        # Too few hours to cover the test range
        return

    s = []
    if first_hour == 0:         # Otherwise there would not be any range with a leading 0.
        s.append(0)

    for n in [ a, b, c, d, e, f, g, h, i, j, k, l ]:
        if n == 3:
            s.append(1)
            s.append(1)
            s.append(0)

        if n == 2:
            s.append(1)
            s.append(0)

    s = s[:nr_hours] # Keep only enough of hours to cover the range.
    g_schedules.append(s)


def create_hour_schedules(start_hr, stop_hr) :
    first_hour = 0
    for a in [2, 3]:
        for b in [2, 3]:
            for c in [2, 3]:
                for d in [2, 3]:
                    for e in [2, 3]:
                        for f in [2, 3]:
                            for g in [2, 3]:
                                for h in [2, 3]:
                                    for i in [2, 3]:
                                        for j in [2, 3]:
                                            for k in [2, 3]:
                                                for l in [2, 3]:
                                                    add_schedule(a,b,c,d,e,f,g,h,i,j,k,l, first_hour, start_hr, stop_hr)
                                                    if first_hour == 0:
                                                        first_hour = 1
                                                    else :
                                                        first_hour = 0


def create_no_dup_hour_maps() :
    i = 0
    hour_maps = {}
    for s in g_schedules:
        i += 1
        nr_set_hr = 0
        ss = ""
        for j in range(len(s)):
            if s[j] == 1 :
                nr_set_hr += 1

            if ss == "" :
                sep = ""
            else :
                sep = "."

            ss += sep+str(s[j])

        if hour_maps.get(ss, "0") == "0" :
            hour_maps[ss] = nr_set_hr

    return(hour_maps)


def get_top_hour_map(hour_maps, price_per_hour, start_hr, stop_hr, g_verbose_logging) :
    top_hour_map_price = {}
    top_hour_map = {}
    price_per_schedule = {}
    #print(price_per_hour)
    #print(hour_maps)
    for hour_map, nr_set_hr in hour_maps.items() :
        hrs = hour_map.split(".")
        price = 0
        hr_ix = -1
        for switch in hrs :
            hr_ix += 1
            if int(switch) > 0:
                price += price_per_hour[hr_ix]

        price = round(price, 2)
        price_per_schedule.update({hour_map: price})

    sorted_price_per_schedule = sorted(price_per_schedule.items(), key=lambda x: float(x[1]), reverse=True)

    f0.print_json_var(g_verbose_logging, 5, "sorted_price_per_schedule: "+str(start_hr)+"-"+ str(stop_hr), sorted_price_per_schedule)
    f0.print_json_var(g_verbose_logging, 4, "price_per_hour", price_per_hour)

    hour_map, price = list(sorted_price_per_schedule)[0]
    for i in range(0,24) :
        top_hour_map[i] = 0
        top_hour_map_price[i] = 0

    hrs = hour_map.split(".")
    hr_ix = -1
    for switch in hrs :
        hr_ix += 1
        if int(switch) > 0:
            top_hour_map[hr_ix+start_hr] = 1
            top_hour_map_price[hr_ix+start_hr] = price_per_hour[hr_ix]
        else :
            top_hour_map[hr_ix+start_hr] = 1
            top_hour_map_price[hr_ix+start_hr] = -1 # An hour in the range but the temp must not be decreased. A "paus" hour.

    #print(top_hour_map_price)
    return(top_hour_map, top_hour_map_price, price)


def create_top_hour_adj_maps(fi_hourly_rate, start_hr, stop_hr, g_verbose_logging) :
    global g_schedules
    g_schedules = []
    price_per_hour = get_price_per_hour_range(fi_hourly_rate, start_hr, stop_hr)
    create_hour_schedules(start_hr, stop_hr)
    hour_maps = create_no_dup_hour_maps()
    top_hour_map, top_hour_map_price, price = get_top_hour_map(hour_maps, price_per_hour, start_hr, stop_hr, g_verbose_logging)
    # This map has the optimal intervals when to decrease temp
    return(top_hour_map, top_hour_map_price, price)


