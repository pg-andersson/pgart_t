#!/usr/bin/python3
# This file is part of PGART_T (Pump Gradual Adjustment Room Temperature for Thermia Atlas).

# Copyright (C) 2023 PG Andersson <pg.andersson@gmail.com>.

# pgart_t is free software: you can redistribute it and/or modify it under the terms of GPL-3.0-or-later

# This program downloads the last 12 months monthly rates from elbruk.se.
# monthly_rates.txt.

import sys
import json
import platform
import os
import requests
from pathlib import Path
from datetime import date,datetime,timedelta
import time

import pgart_misc_func as f0
import pgart_env_func as f1
import pgart_lang_func as f8

te = f1.get_pgart_env()


def create_monthly_rates_elbruk(el_area, logreq, max_log_len):
    url_elbruk  = f1.get_url_elbruk(el_area)
    months =['Januari', 'Februari', 'Mars', 'April', 'Maj', 'Juni', 'Juli', 'Augusti', 'September', 'Oktober', 'November', 'December']
    try:
        request = requests.get(url_elbruk)
    except requests.exceptions.ConnectionError:
        info ="create_monthly_rates_elbruk:\n\t"+g_ui_text["t29"]
        f0.log_action(info, False)
        return(False)

    f0.log_request("requests_get", request, logreq, max_log_len)

    if request.status_code != 200 :
        info = "create_monthly_rates_elbruk:\n\t"+g_ui_text["t30"]+" response:"+str(request.status_code)
        f0.log_action(info, False)
        return(False)

    # Månadstabellen
    # Sedan 2023-02-21. Moms tillkommit och inte &nbsp; längre. Den andra tabellen.
    #<table class="table data-table mb30"><thead><tr><th>Månad</th>

    t_from = 'data-table mb30"><thead><tr><th>Månad</th>'
    t_to = "</tbody>"
    start_of_table = request.text.split(t_from)[1]
    start_of_table = start_of_table.split(t_to)[0]

    # (SE4)</th></tr></thead><tbody><tr><td>November 2022 *</td><td>47,33 öre/kWh</td></tr> ... </td></tr>
    the_table = start_of_table.split("<tbody>")[1]
    the_table = the_table.replace(' öre/kWh', '')
    the_table = the_table.replace('*', '')         # Use the preliminary instead of a final value.

    t_rows = the_table.split('<tr')     # <tr><td>November 2022</td><td>47,33</td></tr> => ><td>November 2022</td><td>47,33</td></tr>
    fi = Path(te["fi_monthly_rates"])
    f = open(te["fi_monthly_rates"], "w", encoding="utf8")
    for tr in t_rows :
        if tr == "" :
            continue;

        tmp_my_r = tr.split('</td><td>')       # ><td>November 2022</td><td>47,33</td></tr> => ><td>November 2022 and 47,33</td></tr>
        tmp_my = tmp_my_r[0].split('<td>')[1]  # ><td>November 2022 => November 2022
        my = tmp_my.split(' ')              # November 2022 => November and 2022
        month = my[0]
        y = my[1]
        r = tmp_my_r[1].split('<')[0]          # 47,33</td></tr> => 47,33
        r = r.replace(",", ".")
        m = months.index(month) + 1
        m2dig = "{:02d}"
        m2 = m2dig.format(m)
        f.write(y+"-"+m2+":"+r+"\n")

    f.close()
    return(True)


g_lang = f8.get_language()
g_ui_text = f1.ui_texts(g_lang)
max_nr_get_request_trials = 2

el_area, logreq, max_log_len = f0.get_args_fi_cre_hourly_rates("pgart_get_monthly_rates_elbruk_se.py")
print(el_area, logreq, max_log_len)

nr_trials = 1
more = True
while more :
    if create_monthly_rates_elbruk(el_area, logreq, max_log_len) :
        f0.print_monthly_rates()
        sys.stdout.flush()
        exit()
    else :
        if nr_trials == max_nr_get_request_trials :
            print("-ok")
            exit()
        print("Will sleep for 55s before the next try.")
        time.sleep(55)       # Try once more after a while.

    nr_trials += 1
