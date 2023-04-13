#!/usr/bin/python3
# This file is part of PGART_T (Pump Gradual Adjustment Room Temperature for Thermia Atlas).

# Copyright (C) 2023 PG Andersson <pg.andersson@gmail.com>.

# pgart_t is free software: you can redistribute it and/or modify it under the terms of GPL-3.0-or-later

# This program is kind of experimental and it requires manual work.
# It creates a table with alternative costs for the el-consumption based on monthly rates, hourly rates and real el-consumption.

# The program converts csv-files which have been manually downloaded from an EON account and saved as
# your-user/pgart/var/local/eon_yyyymmdd.csv to your-user/pgart/var/local/hourly_consumption_"date".txt.
# The el-consumption is then taken from them.

import getopt, sys
import platform
import os
import glob

from pathlib import Path
from datetime import date,time,datetime

import pgart_misc_func as f0
import pgart_env_func as f1
import pgart_experimental_conv_eon_files_to_generic_func as f7
import pgart_lang_func as f8

g_lang = f8.get_language()
g_ui_text = f1.ui_texts(g_lang)
te = f1.get_pgart_env()

def get_monthly_rates():
    monthly_rates = {}
    fi = Path(te["fi_monthly_rates"])
    if fi.is_file():
        f = open(te["fi_monthly_rates"], 'r' , encoding="utf8")
        for rec in f:
            rec = rec.strip()
            if rec == "":
                continue
            s = rec.split(":")
            ym = s[0]
            rate = float(s[1])
            monthly_rates.update({ym:rate})

        f.close()
    return (monthly_rates)


def get_hourly_consumption(fi_hourly_consumption):
    hr_cons = {}

    fi = Path(fi_hourly_consumption)
    nr_rec = 0
    if fi.is_file():
        f = open(fi_hourly_consumption, 'r' , encoding="utf8")
        for rec in f:
            nr_rec = nr_rec +1
            rec = rec.strip()
            rec = "".join(rec.split())
            if rec.count(":") != 1 :    # 01:0.422
                info = fi_hourly_consumption+". "+rec+". "+g_ui_text["tp5d"]
                log_action(info, False)
                return(hr_cons)

            s = rec.split(":")
            if not s[0].isnumeric() :
                info = fi_hourly_consumption+". "+rec+". "+g_ui_text["th2"]
                log_action(info, False)
                return(hr_cons)

            if not f0.is_float(s[1]) :
                info = fi_hourly_consumption+". "+rec+". "+g_ui_text["th4"]
                log_action(info, False)
                return(hr_cons)

            hr_cons.update({int(s[0]): float(s[1])})

        f.close()
    return(hr_cons)


def get_el_statistics(fi_hourly_rate, fi_hourly_consumption):
    hr_rates = f0.get_hourly_rates(fi_hourly_rate)
    consumption_kwh = get_hourly_consumption(fi_hourly_consumption)

    return (hr_rates, consumption_kwh)


def calc_el_consumption(dt_from, dt_to, hr_rates, consumption_kwh, monthly_rate, dt) :
    hr_rate_cost = {}
    hr_mean_cost = {}
    sum_kwh = 0

    for h, r in hr_rates.items() :
        if h in consumption_kwh :
            nr_kwh = consumption_kwh[h]
            sum_kwh += nr_kwh
            hr_cost = nr_kwh * r
            hr_rate_cost.update({h:hr_cost})
            hr_mean = nr_kwh * monthly_rate
            hr_mean_cost.update({h:hr_mean})

    sum_hr_rate_cost = 0
    for h in hr_rate_cost:
        sum_hr_rate_cost += hr_rate_cost[h]

    sum_hr_mean_cost = 0
    for h in hr_mean_cost:
        sum_hr_mean_cost += hr_mean_cost[h]

    fi_charges = te["fi_el_charges"].split(".")[0]+"_"+dt_from+"_"+dt_to+".txt"
    f = open(fi_charges, "a", encoding="utf8")
    y = dt[0:4]
    m = dt[4:6]
    d = dt[6:8]
    ymd = y+"-"+m+"-"+d
    f.write("\n" + ymd + "\n")

    line = "Kl".ljust(3) +"kWh".rjust(6) + "tim".rjust(8) + "medel".rjust(8) + "timpris".rjust(9) +"medelpris".rjust(10)+"diff".rjust(8)
    f.write(line + "\n")
    line = "  ".ljust(3) +" ".rjust(6) + "pris".rjust(8) + "pris".rjust(8) + "kostnad".rjust(9) +"kostnad".rjust(10)+" ".rjust(8)
    f.write(line + "\n")

    for h, rc in hr_rate_cost.items() :
        mean = hr_mean_cost[h]
        kwh = consumption_kwh[h]
        r = hr_rates[h]
        diff = rc - mean
        costs = "{:02d} {:>6.3f} {:>7.2f} {:>7.2f} {:>8.2f} {:>9.2f} {:>7.2f}"
        line = costs.format(h, kwh, r/100, float(monthly_rate)/100, rc/100 , mean/100, diff/100 )
        f.write(line + "\n")

    s_sum_kwh = "{:.2f}".format(sum_kwh)
    s_sum_hr_rate_cost = "{:.2f}".format(sum_hr_rate_cost/100)
    s_sum_hr_mean_cost = "{:.2f}".format(sum_hr_mean_cost/100)
    s_perc = "{:.2f}".format((sum_hr_mean_cost/sum_hr_rate_cost -1)*100)

    f.write("Dygnets förbrukning: "+s_sum_kwh+" kWh\n")
    f.write("Kostnad för hela dygnet med timpriset: "+s_sum_hr_rate_cost+" kr, med månadspriset: "+s_sum_hr_mean_cost+" kr, skillnad: "+s_perc+"%\n")
    f.close()
    return(sum_kwh, sum_hr_rate_cost, sum_hr_mean_cost)


def find_files_consumption(dt_from, dt_to) :
    fi_dates = []
    for fi in glob.glob(te["g_local_dir"]+"/hourly_consumption_"+'*') :   # get all such files.
        fi_dt = fi.split("_")[2].split(".")[0]
        fi_hourly_consumption=te["g_local_dir"]+"/hourly_consumption_"+fi_dt+".txt"
        fi_e = Path(fi_hourly_consumption)
        if fi_e.is_file():
            if fi_dt >= dt_from and fi_dt <= dt_to :
                # Calculation possible.
                fi_dates.append(fi_dt)

    fi_dates.sort()
    return(fi_dates)


def create_consumption_table(dt_from, dt_to) :
    tot_hr_rate_cost = 0
    tot_hr_mean_cost = 0
    tot_sum_kwh = 0

    fi = Path(te["fi_monthly_rates"])
    if fi.is_file():
        monthly_rates = get_monthly_rates()
    else :
        print(te["fi_monthly_rates"]+" Missing.")
        exit()

    #print(monthly_rates)
    fi_dates = find_files_consumption(dt_from, dt_to)
    if fi_dates == [] :
        return(False)

    nr_fi_hourly_rate = 0
    nr_fi_hourly_consumption = 0
    for dt in fi_dates :
        fi_hourly_rate=te["g_local_dir"]+"/hourly_rate_"+dt+".txt"
        fi_hourly_consumption=te["g_local_dir"]+"/hourly_consumption_"+dt+".txt"
        hr_rates, consumption_kwh = get_el_statistics(fi_hourly_rate, fi_hourly_consumption)
        print("\n"+str(dt))
        cont = False
        if len(hr_rates) == 0 :
            print(fi_hourly_consumption+" exists but "+fi_hourly_rate+" is missing. Thus no statistics.")
            cont = True
        else :
            nr_fi_hourly_rate += 1

        if len(consumption_kwh) == 0 :
            print(fi_hourly_consumption+" Missing. File empty?")    #Should not happen because fi_dates is a list from hourly_consumption* files.
            cont = True
        else :
            nr_fi_hourly_consumption +=1

        if cont :
            continue

        # Get the year and month. 20221110
        ym = dt[0:4] + "-" + dt[4:6]
        monthly_rate = monthly_rates[ym]
        sum_kwh, sum_hr_rate_cost, sum_hr_mean_cost = calc_el_consumption(dt_from, dt_to, hr_rates, consumption_kwh, monthly_rate, dt)
        tot_sum_kwh = tot_sum_kwh + sum_kwh
        tot_hr_rate_cost = tot_hr_rate_cost + sum_hr_rate_cost
        tot_hr_mean_cost = tot_hr_mean_cost + sum_hr_mean_cost

    print("nr_fi_hourly_rate:"+str(nr_fi_hourly_rate)+" nr_fi_hourly_consumption:"+str(nr_fi_hourly_consumption))
    if nr_fi_hourly_rate == 0 or nr_fi_hourly_consumption == 0 :
        return(False)

    s_tot_sum_kwh = "{:.2f}".format(tot_sum_kwh)
    s_tot_hr_rate_cost = "{:.2f}".format(tot_hr_rate_cost/100)
    s_tot_hr_mean_cost = "{:.2f}".format(tot_hr_mean_cost/100)
    s_perc = "{:.2f}".format((tot_hr_mean_cost/tot_hr_rate_cost -1)*100)

    fi_charges = te["fi_el_charges"].split(".")[0]+"_"+dt_from+"_"+dt_to+".txt"
    f = open(fi_charges, "a", encoding="utf8")
    f.write("\nTotal förbrukning för hela perioden: "+s_tot_sum_kwh+" kWh\n")
    f.write("Kostnad för hela perioden med timpriset: "+s_tot_hr_rate_cost+" kr, med månadspriset: "+s_tot_hr_mean_cost+" kr, skillnad: "+s_perc+"%\n")
    f.close()
    return(True)


def get_date_range() :
    argv = sys.argv[1:]     # Bypass my own name
    options = "f:t:"
    long_options = ["fromymd=", "toymd="]

    if len(argv) == 0:
        return("19700101", "20371231")   #Whatever there is around

    if len(argv) == 4 :
        try:
            args, values = getopt.getopt(argv, options, long_options)
            for arg, val in args :
                if arg in ("-f", "--fromymd") :
                    f = val
                elif arg in ("-t", "--toymd") :
                    t = val
        except getopt.error as err :
            print(str(err))
            exit()
    else :
        print("usage: pg_calc_cost.py -f <yyyymmdd> -t <yyyymmdd> or --fromymd <yyyymmdd> --toymd <yyyymmdd>")
        exit()

    return(f, t)


dt_from, dt_to = get_date_range()
print(dt_from, dt_to)

status, info = f7.convert_downloaded_eon_csv_files_to_generic_el_consumption_files(dt_from, dt_to)
if not status :
    print(info)
    exit()

if info == "-EON_files" :
    print("Not any EON CSV files to convert.")
else :
    print("Converted: "+str(info)+" EON CSV files")

if not create_consumption_table(dt_from, dt_to) :
    print("Not any matching date hourly_rate_* and hourly_consumption_* files.")

exit()

