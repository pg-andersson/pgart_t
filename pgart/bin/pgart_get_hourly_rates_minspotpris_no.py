#!/usr/bin/python3
# This file is part of PGART_T (Pump Gradual Adjustment Room Temperature for Thermia Atlas).

# Copyright (C) 2023 PG Andersson <pg.andersson@gmail.com>.

# pgart_t is free software: you can redistribute it and/or modify it under the terms of GPL-3.0-or-later

# This program retrieves hourly rates from minspotpris.no
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

def create_hourly_rates_minspotpris(el_area, logreq, max_log_len) :
    area_nr = f1.exit_if_el_area_missing("no", el_area)
    url_minspotpris  = f1.get_url_minspotpris()

    try:
        request = requests.get(url_minspotpris)
    except requests.exceptions.ConnectionError:
        info ="create_monthly_and_hourly_rates_minspotpris:\n\t"+g_ui_text["t29a"]
        f0.log_action(info, False)
        return(False)

    f0.log_request("requests_get", request, logreq, max_log_len)

    if request.status_code != 200 :
        info = "create_monthly_and_hourly_rates_minspotpris:\n\t"+g_ui_text["t30a"]+" response:"+str(request.status_code)
        f0.log_action(info, False)
        return(False)

    """
    <div id="utenavgifter"><br>
    <table id="eksAvgtd" class="liste timereg">
    <tr class="tdhighligth"><td>19/03/2023</td>
    <td>Øst</td><td>Sør</td><td>Vest</td><td>Midt</td><td>Nord</td></tr>

    The webpage drop the morning hours in the afternoon.
    <tr class="gray"><td class="w20 b">14 - 15</td>
    <td class="r green" title="105.399">131.749</td>
    <td class="r green" title="105.399">131.749</td>
    <td class="r green" title="105.399">131.749</td>
    <td class="r red" title="48.661">60.826</td>
    <td class="r green" title="28.586">28.586</td> </tr>
    ...
    <tr class="white i b"><td class="w20 b">23 - 24</td><td class="r green" title="108.713">135.891</td><td class="r green" title="108.713">135.891</td>

    The second "tdhighligth" is not presented in the morning.
    <tr class="tdhighligth"><td>20/03/2023</td><td>Øst</td><td>Sør</td><td>Vest</td><td>Midt</td><td>Nord</td></tr><tr class="white"><td class="w20 b">00 - 01</td><td clas

    This <tr><td colspan= is always there.
    """

    # From 20/03/2023 0 -> 23
    # <table id="eksAvgtd" class="liste timereg"><tr class="tdhighligth"><td>
    start_hour_price_table = request.text.split('<table id="eksAvgtd"', 1)[1]

    # Find today. <tr class="tdhighligth"><td>20/03/2023</td><td>Øst</td><td>Sør</td><td>Vest</td><td>Midt</td><td>Nord</td></tr>
    dt_now = datetime.strftime(datetime.now(), "%d/%m/%Y")
    date_search = '<tr class="tdhighligth"><td>'+dt_now+"</td>"
    if start_hour_price_table.find(date_search) == -1 :
        info ="create_monthly_and_hourly_rates_minspotpris:\n\t"+g_ui_text["t30a"]+" Missing date:"+dt_now
        f0.log_action(info, True)

    start_hour_price_table = start_hour_price_table.split(date_search, 1)[1]
    the_table = start_hour_price_table.split("<td colspan=")[0]   # Just after the one or two days table.

    if the_table.find('<tr class="tdhighligth"><td>') > -1 :
        # Tomorrow is already loaded. The entries for today might be missing the start hours
        the_table = the_table.split('<tr class="tdhighligth"><td>')[0]

    #<td>Øst</td><td>Sør</td><td>Vest</td><td>Midt</td><td>Nord</td></tr><tr class="gray"><tr class="white"><td class="w20 b">00 - 01</td><td class="r red" title="114.935">143.669</td><td class="r red" title="114.935">143.669</td>...</tr>
    cols = the_table.split("</tr>")

    f = open(te["fi_hourly_rate"], "w", encoding="utf8")

    i = 1       # Bypass the header line
    more = True
    while more :
        # col == <tr class="gray"><tr class="white"><td class="w20 b">00 - 01</td><td class="r red" title="114.935">143.669</td><td class="r red" title="114.935">143.669</td>...</tr>  Up until the last hour.
        col_part2 = cols[i].split('<td class="w20 b">')[1]

        # 00 - 01</td><td class="r red" title="114.935">143.669</td><td class="r red" title="114.935">143.669</td>
        s4 = col_part2.split("</td>", 1)

        # 00 - 01
        h = s4[0].split("-")[0].strip()         # Get the hour

        #<td class="r red" title="114.935">143.669</td><td class="r red" title="114.935">143.669</td>
        s5 = s4[1].split("</td>")

        """
        # <td class="r red" title="114.935">143.669   # Use the price with added costs 143.669.
        rate = s5[area_nr].split(">")[1]
        """

        #<td class="r red" title="114.935">143.669
        rtmp = s5[area_nr].split('title="')[1]      # Use the raw "title" price 114.935.

        # 114.935">143.669
        rate = rtmp.split('"')[0]

        f.write(h+":"+rate+"\n")

        i += 1
        if h == "23" :
            more = False

        if i == 25 :   # Avoid an infinite loop.
            more = False

    f.close()
    return(True)


max_nr_get_request_trials = 2
g_lang = f8.get_language()
g_ui_text = f1.ui_texts(g_lang)

el_area, logreq, max_log_len = f0.get_args_fi_cre_hourly_rates("pgart_get_hourly_rates_minspotpris_no.py")

nr_trials = 1
more = True
while more :
    if create_hourly_rates_minspotpris(el_area, logreq, max_log_len) :
        f0.print_hourly_rates()
        sys.stdout.flush()
        exit()
    else :
        if nr_trials == max_nr_get_request_trials :
            print("-ok")
            exit()
        time.sleep(55)       # Try once more after a while.

    nr_trials += 1
