#!/usr/bin/python3
# This file is part of PGART_T (Pump Gradual Adjustment Room Temperature for Thermia Atlas).

# Copyright (C) 2023 PG Andersson <pg.andersson@gmail.com>.

# pgart_t is free software: you can redistribute it and/or modify it under the terms of GPL-3.0-or-later
#
# Functions to get the parameters from pg_control_thermia_heating.conf.

import sys
import platform
import os
from pathlib import Path
from datetime import date,datetime,timedelta
import time
import ipaddress

import pgart_misc_func as f0
import pgart_env_func as f1
import pgart_lang_func as f8

g_lang = f8.get_language()
g_ui_text = f1.ui_texts(g_lang)
te = f1.get_pgart_env()

def is_hr_temp_valid(hr_temp) :
    # hr_temp: 20_14,06_20
    hours_set = []
    for i in range(24) :
        hours_set.append(0)

    th=hr_temp.split(',')
    for x in th :
        x = x.strip()
        if len(x) != 5 :
            return(False, g_ui_text["tp1"]+": "+str(x))

        if x.count("_") != 1 :
            return(False, g_ui_text["tp1"]+": "+str(x))

        if x[2] != "_" :
            return(False, g_ui_text["tp1"]+": "+str(x))

        buf=x.split('_')
        if not (buf[0].isnumeric() and buf[1].isnumeric()) :
            return(False, g_ui_text["tp2"]+": "+str(buf))

        hr = int(buf[0])
        if not(hr in range(0, 24)) :
            return(False, g_ui_text["tp3"]+": "+str(hr))

        temp = int(buf[1])
        if not(temp in range(5, 26)) :
            return(False,  g_ui_text["tp4"]+": "+str(temp))

        if hours_set[hr] == 1 :         # Overlapping hours?
            return(False, g_ui_text["tp3c"]+": "+str(hr)+" "+str(x))
        hours_set[hr] = 1

    return(True, "")


def is_hr_hr_valid(hr_hr) :
    # hr_hr: 8-15,20-22
    hours_set = []
    for i in range(24) :
        hours_set.append(0)

    th=hr_hr.split(',')
    for x in th :
        x = x.strip()
        if x.count("-") != 1 :
            return(False, g_ui_text["tp1a"]+": "+str(x))

        if x.startswith("-") or x.endswith("-") :
            return(False, g_ui_text["tp1a"]+": "+str(x))

        buf=x.split('-')
        if not (buf[0].isnumeric() and buf[1].isnumeric()) :
            return(False, g_ui_text["tp2a"]+": "+str(buf))

        hr1 = int(buf[0])
        if not(hr1 in range(0, 25)) :
            return(False, g_ui_text["tp3"]+": "+str(hr1))

        hr2 = int(buf[1])
        if not(hr2 in range(0, 25)) :
            return(False,  g_ui_text["tp3"]+": "+str(hr2))

        if hr1 > hr2  :
            return(False,  g_ui_text["tp3a"]+": "+str(x))

        for i in range(hr1, hr2+1) :        # Overlapping hours?
            if hours_set[i] == 1 :
                return(False, g_ui_text["tp3b"]+": "+str(x))
            hours_set[i] = 1

    return(True, "")

def is_exec_path_valid(rec_orig) :
    par, val = rec_orig.split("=", 1)
    print(par, val)

    if val == "," :
        return(True, val)

    if val.count(",") == 0 :
        # Just the program. Not any args.
        pgm = val
    else :
        pgm = val.split(',')[0]

    filepath = Path(te["g_bin_dir"]+"/"+pgm)
    if not filepath.is_file():
        return(False,  par+":"+val+" "+pgm+" "+g_ui_text["tp17"]+" "+te["g_bin_dir"])

    return(True, val)


def is_ip_valid(address):
    try:
        ip = ipaddress.ip_address(address)
        return(True)
    except ValueError:
        return(False)


def is_par_valid(par, val) :
    valid_par = f1.valid_config_parameters()
    if not (par in valid_par) :
        return(False, par+": "+val)

    valid_pars = valid_par[par].split(':')
    if valid_pars[0] == "txt_single" :
        valids = valid_pars[1].split(',')
        if "*" in valids :          # Fix för yet unknown el_areas
            return(True, val)

        if not (val in valids) :
            return(False, par+": "+val+". "+g_ui_text["tp14"]+": "+valid_pars[1])

        return(True, val)

    elif valid_pars[0] == "int_range" :
        ir = valid_pars[1].split('-')
        vals = val.split(',')
        for i in vals :
            if not i.isnumeric() :
                return(False, par+": "+val+". "+g_ui_text["tp14"]+": "+valid_pars[1])

            i = int(i)
            if ((i < int(ir[0])) or (i > int(ir[1]))) :
                return(False, par+": "+val+". "+g_ui_text["tp14"]+": "+valid_pars[1])

        return(True, val)

    elif valid_pars[0] == "int_single" :
        ir = valid_pars[1].split('-')
        if not val.isnumeric() :
            return(False, par+": "+val+". "+g_ui_text["tp14"]+": "+valid_pars[1])

        if ((int(val) < int(ir[0])) or (int(val) > int(ir[1]))) :
            return(False, par+": "+val+". "+g_ui_text["tp14"]+": "+valid_pars[1])

        return(True, val)

    elif valid_pars[0] == "-int_single" :
        ir = valid_pars[1].split('>-<')
        if val[0] != "-" :
            return(False, par+": "+val+". "+g_ui_text["tp14"]+": "+valid_pars[1])

        if not val[1:].isnumeric() :
            return(False, par+": "+val+". "+g_ui_text["tp14"]+": "+valid_pars[1])

        if ((int(val) < int(ir[1])) or (int(val) > int(ir[0]))) :
            return(False, par+": "+val+". "+g_ui_text["tp14"]+": "+valid_pars[1])

        return(True, val)

    elif valid_pars[0] == "float_single" :
        fs = valid_pars[1].split('-')
        if not f0.is_float(val) :
            return(False, par+": "+val+". "+g_ui_text["tp14"]+": "+valid_pars[1])

        val = float(val)
        if not ( val >= float(fs[0]) and val <= float(fs[1])) :
            return(False, par+": "+str(val)+". "+g_ui_text["tp14"]+": "+valid_pars[1])

        return(True, val)

    elif valid_pars[0] == "ip" :
        if not is_ip_valid(val) :
            return(False, par+": "+val+". "+g_ui_text["tp15"])

    return(True, val)


def get_parameters():
    l_general_pars = f1.default_config_parameters()
    used_general_pars = {}
    l_weekday_indoor_temp_hours = {}

    fi_par = te["fi_par"]+"_"+g_lang
    ret_stat = "ok"
    filepath = Path(fi_par)
    if filepath.is_file():
        f = open(fi_par, "r", encoding="utf8")
        for rec in f:
            rec = rec.strip()
            if rec == "" or rec == "^M" :
                continue

            if rec.find("#", 0 , 1) == 0:
                continue

            if rec.find("#") >-1:              # Clean the rec from any comment at the end.
                rec1 = rec.split("#")
                rec = rec1[0]

            rec = rec.strip()
            if rec.find("=") == -1 :
                ret_stat = fi_par+". "+rec+". "+g_ui_text["tp5"]
                break

            if rec.endswith("=") :
                ret_stat = fi_par+". "+rec+". "+g_ui_text["tp5c"]
                break

            rec_orig = rec
            rec = "".join(rec.split())
            buf = rec.split("=", 1)
            par = buf[0]
            val = buf[1]
            if val.find(",,") != -1 :
                ret_stat = fi_par+" "+par+": "+val+". "+g_ui_text["tp5a"]
                break

            if  val.startswith(",") or val.endswith(",") :
                ret_stat = fi_par+" "+par+": "+val+". "+g_ui_text["tp5b"]
                break

            if not (par in l_general_pars) :
                ret_stat = fi_par+" parameter: "+par+" :"+val+": "+g_ui_text["tp10"]
                break

            if par.startswith("set_indoor_temp_weekday_"):
                buf = par.split("set_indoor_temp_weekday_",1)  # Get the weekday. set_indoor_temp_weekday_1 = 09_17,12_18,14_20,20_15
                week_day_nr = buf[1]
                status, result = is_hr_temp_valid(val)
                if not status :
                    ret_stat = fi_par+" "+par+": "+result
                    break

                l_weekday_indoor_temp_hours.update({int(week_day_nr): val})

            elif par == "set_indoor_temp_hours" :
                status, result = is_hr_temp_valid(val)
                if not status :
                    ret_stat = fi_par+" "+par+": "+result
                    break

            elif par == "hourly_rate_decrease_hours" :
                status, result = is_hr_hr_valid(val)
                if not status :
                    ret_stat = fi_par+" "+par+": "+result
                    break

            elif par == "external_pgm_create_hourly_rates" or par == "external_pgm_create_forecasts" :
                status, result = is_exec_path_valid(rec_orig)
                val = result
                if not status :
                    ret_stat = fi_par+" "+par+": "+result
                    break
            else:
                status, result = is_par_valid(par, val)

            if not status :
                ret_stat = fi_par+" "+result
                break

            # Check for duplicates.
            if par in used_general_pars :
                ret_stat = fi_par+". "+g_ui_text["td1"]+par+": "+str(val)
                break

            used_general_pars.update({par: str(val)})
            l_general_pars.update({par: str(val)})
    else:
        ret_stat = fi_par+" "+g_ui_text["t5"]

    # Check if the mail parameter file is valid.
    mail_pars = f0.get_mail_params()        # No return if an error.

    return(ret_stat, l_general_pars, l_weekday_indoor_temp_hours)
