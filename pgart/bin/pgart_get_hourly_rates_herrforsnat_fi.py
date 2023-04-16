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
import requests
import time

from pathlib import Path

import pgart_misc_func as f0
import pgart_env_func as f1
import pgart_lang_func as f8

te = f1.get_pgart_env()

def create_hourly_rates_herrforsnat(el_area, logreq, max_log_len):
    area_nr = f1.exit_if_el_area_missing("fi", el_area)
    url_herrforsnat  = f1.get_url_herrforsnat()

    try:
        request = requests.get(url_herrforsnat)
    except requests.exceptions.ConnectionError:
        info ="create_hourly_rates_herrforsnat:\n\t"+g_ui_text["t29"]
        f0.log_action(info, False)
        return(False)

    f0.log_request("requests_get", request, logreq, max_log_len)

    if request.status_code != 200 :
        info = "create_hourly_rates_herrforsnat:\n\t"+g_ui_text["t30"]+" response:"+str(request.status_code)
        f0.log_action(info, False)
        return(False)

    """
               <span class="text-uppercase">
                                PRIS Idag
                            </span>
            </li>
                <li>
                    <span>00 - 01</span>
                    <span>
                                    <pricedata class="today s-price" data-price="2.22">
                                        2.22
                                    </pricedata>
                                </span>
                </li>
                <li>
                    <span>01 - 02</span>
                    <span>
                                    <pricedata class="today s-price" data-price="2.75">
                                        2.75
                                    </pricedata>
                                </span>
                </li>
            <li></li>
    """

    # From "PRIS Idag".
    if request.text.find("PRIS Idag") == -1 :
        info = "create_hourly_rates_herrforsnat:\n\t"+g_ui_text["t30c"]
        f0.log_action(info, False)
        return(False)

    start_hour_price_table = request.text.split('today-spotprices-chart', 1)[1]
    start_hour_price_table = start_hour_price_table.split('PRIS Idag', 1)[1]
    s = start_hour_price_table.split("<li></li>", 1)[0]
    s = s.replace("<span>", "")
    s1 = s.replace("<li>", "")
    s2 = s1.split("</li>")

    #              01 - 02</span>
    #                                <pricedata class="today s-price" data-price="2.75">
    #                                    2.75
    #                                </pricedata>
    #                           </span>

    f = open(te["fi_hourly_rate"], "w", encoding="utf8")
    i = 1      # Bypass the first line
    while i < len(s2)-1 :
        s3 = s2[i].split("</span>", 1)[0]
        # 00 - 01
        h = s3.split("-")[0].strip()         # Get the hour
        s4 = s2[i].split("</pricedata>")[0]
        rate = s4.split('">')[1].strip()
        f.write(h+":"+rate+"\n")
        i += 1

    f.close()
    return(True)


g_lang = f8.get_language()
g_ui_text = f1.ui_texts(g_lang)
max_nr_get_request_trials = 2

el_area, logreq, max_log_len = f0.get_args_fi_cre_hourly_rates("pgart_get_hourly_rates_herrforsnat_fi.py")
print(el_area, logreq, max_log_len)

nr_trials = 1
more = True
while more :
    if create_hourly_rates_herrforsnat(el_area, logreq, max_log_len) :
        f0.print_hourly_rates()
        sys.stdout.flush()
        exit()
    else :
        if nr_trials == max_nr_get_request_trials :
            print("-ok")
            exit()
        time.sleep(55)       # Try once more after a while.

    nr_trials += 1
