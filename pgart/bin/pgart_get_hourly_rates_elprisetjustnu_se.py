#!/usr/bin/python3
# This file is part of PGART_T (Pump Gradual Adjustment Room Temperature for Thermia Atlas).

# Copyright (C) 2023 PG Andersson <pg.andersson@gmail.com>.

# pgart_t is free software: you can redistribute it and/or modify it under the terms of GPL-3.0-or-later

# This program downloads hourly rates from elprisetjustnu.se
# "home"/pgart/var/local/hourly_rate_yyyymmdd.txt

import sys
import os
import json
import platform
import os
import requests
import time

from pathlib import Path
from datetime import date,datetime,timedelta

import pgart_misc_func as f0
import pgart_env_func as f1
import pgart_lang_func as f8

te = f1.get_pgart_env()


def save_hr_rate(json_justnu) :
    f = open(te["fi_hourly_rate"], "w", encoding="utf8")
    for hr_rt in json_justnu:
        #{'SEK_per_kWh': 0.82607, 'EUR_per_kWh': 0.07291, 'EXR': 11.330006, 'time_start': '2023-03-15T23:00:00+01:00', 'time_end': '2023-03-16T00:00:00+01:00'}
        rate = hr_rt['SEK_per_kWh']
        rate = round(rate*100, 2)       # öre
        ix = hr_rt['time_start'].find("T")      # 2023-03-15T23:00:00+01:00
        h = hr_rt['time_start'][ix+1] + hr_rt['time_start'][ix+2]
        f.write(h+":"+str(rate)+"\n")

    f.close()
    return(True)


def create_hourly_rates_justnu(el_area, logreq, max_log_len):
    # "https://www.elprisetjustnu.se/api/v1/prices/2023/03-15_SE4.json"
    dt = datetime.strftime(datetime.now(), "%Y/%m-%d")
    area_nr = f1.exit_if_el_area_missing("se", el_area)

    url_justnu = "https://www.elprisetjustnu.se/api/v1/prices/"+dt+"_"+el_area+".json"
    print(url_justnu)
    json_justnu = ""

    try:
        response = requests.get(url_justnu)
    except requests.exceptions.ConnectionError:
        info ="create_hourly_rates_justnu:\n\t"+g_ui_text["t29c"]
        f0.log_action(info, False)
        return(False)

    f0.log_request("requests_get", response, logreq, max_log_len)

    if response.status_code != 200 :
        info = "create_hourly_rates_justnu:\n\t"+g_ui_text["t30e"]+" response:"+str(response.status_code)
        f0.log_action(info, False)
        return(False)

    json_justnu = json.loads(response.content)

    save_hr_rate(json_justnu)
    return(True)


g_lang = f8.get_language()
g_ui_text = f1.ui_texts(g_lang)
max_nr_get_request_trials = 2

el_area, logreq, max_log_len = f0.get_args_fi_cre_hourly_rates("pgart_get_hourly_rates_herrforsnat_fi.py")
print(el_area, logreq, max_log_len)

nr_trials = 1
more = True
while more :
    if create_hourly_rates_justnu(el_area, logreq, max_log_len) :
        f0.print_hourly_rates()
        sys.stdout.flush()
        exit()
    else :
        if nr_trials == max_nr_get_request_trials :
            print("-ok")
            exit()
        time.sleep(55)       # Try once more after a while.

    nr_trials += 1
