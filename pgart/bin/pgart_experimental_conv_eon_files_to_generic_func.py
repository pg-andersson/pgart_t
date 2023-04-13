#!/usr/bin/python3
# This file is part of PGART_T (Pump Gradual Adjustment Room Temperature for Thermia Atlas).

# Copyright (C) 2023 PG Andersson <pg.andersson@gmail.com>.

# pgart_t is free software: you can redistribute it and/or modify it under the terms of GPL-3.0-or-later
#
# Somewhat experimental.
# The functions here are used to convert the manually downloaded el-consumption CSV-files from EON to new files of a simple format.
# From your-user/pgart/var/local/eon_yyyymmdd.csv to hourly_consumption_"date".txt.
# Works only in Sweden because the parsing of the CSV-files are language dependent.

import getopt, sys
import platform
import os
import glob

from pathlib import Path
from datetime import date,time,datetime

import pgart_misc_func as f0
import pgart_env_func as f1
import pgart_lang_func as f8

g_lang = f8.get_language()
g_ui_text = f1.ui_texts(g_lang)
te = f1.get_pgart_env()

def convert_eon_csv_file_to_generic_file(fi_eon, fi_hourly_consumption):
    fi = Path(fi_eon)
    if fi.is_file():
        fo = open(fi_hourly_consumption, "w", encoding="utf8")
        f = open(fi_eon, 'r' , encoding="utf8")
        for rec in f:
            rec = rec.strip()
            if rec == "":
                continue
            if rec.find("Förbrukning") > -1 :
                continue
            if rec.find('Klockslag') > -1 :
                continue
            if rec.find('Summa') > -1 :
                continue

            # "01:00";0.422
            if rec.count(":") != 1 or rec.count(";") != 1 :
                info = fi_eon+". "+rec+". "+g_ui_text["tp5i"]
                f0.log_action(info, False)
                return(False, info)

            s = rec.split(";")
            hr = s[0].split(":")[0]             # "01:00" => 01
            hr = hr.replace('"', '')
            if not hr.isnumeric() :
                info = fi_eon+". "+rec+". "+g_ui_text["th2"]
                f0.log_action(info, False)
                return(False, info)

            if not ((int(hr) < 24) and (int(hr) >= 0)) :
                info = fi_eon+". "+rec+". "+g_ui_text["th3"]
                f0.log_action(info, False)
                return(False, info)

            if not f0.is_float(s[1]) :
                info = fi_eon+". "+rec+". "+g_ui_text["th4"]
                f0.log_action(info, False)
                return(False, info)

            kwh = float(s[1])                        # 0.422
            fo.write(str(hr)+":"+str(kwh) + "\n")

        f.close()
        fo.close()
    return(True, "")


def find_eon_csv_consumption_files(dt_from, dt_to) :
    fi_dates = []
    for fi in glob.glob(te["g_local_dir"]+"/eon_"+'*') :   # get all such files.
        print(fi)
        fi_dt = fi.split("_")[1].split(".")[0]
        fi_eon = te["g_local_dir"]+"/eon_"+fi_dt+".csv"
        fi_e = Path(fi_eon)
        if fi_e.is_file():
            if fi_dt >= dt_from and fi_dt <= dt_to :
                # Calculation possible.
                fi_dates.append(fi_dt)

    fi_dates.sort()
    return(fi_dates)


def convert_downloaded_eon_csv_files_to_generic_el_consumption_files(dt_from, dt_to) :
    fi_dates = find_eon_csv_consumption_files(dt_from, dt_to)
    if fi_dates == [] :
        return(True, "-EON_files")

    for dt in fi_dates :
        fi_eon=te["g_local_dir"]+"/eon_"+dt+".csv"
        fi_hourly_consumption=te["g_local_dir"]+"/hourly_consumption_"+dt+".txt"
        status, info = convert_eon_csv_file_to_generic_file(fi_eon, fi_hourly_consumption)
        if not status :
            return(status, info)

    return(True, len(fi_dates))
