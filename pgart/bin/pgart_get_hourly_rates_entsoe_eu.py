#!/usr/bin/python3
# This file is part of PGART_T (Pump Gradual Adjustment Room Temperature for Thermia Atlas).

# Copyright (C) 2023 PG Andersson <pg.andersson@gmail.com>.

# pgart_t is free software: you can redistribute it and/or modify it under the terms of GPL-3.0-or-later

# This program retrieves the hourly prices from transparency.entsoe.eu
# "home"/pgart/var/local/hourly_rate_yyyymmdd.txt

import sys
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

g_lang = f8.get_language()
g_ui_text = f1.ui_texts(g_lang)
te = f1.get_pgart_env()

# transparency.entsoe.eu URLs for the Bidding Zones in the Nordic and Baltic countries.
url_start = "https://transparency.entsoe.eu/transmission-domain/r2/dayAheadPrices/show?name=&defaultValue=false&viewType=TABLE&areaType=BZN&atch=false&dateTime.dateTime="
url_timezone = {}
url_biddingZone = {}
url_timezone_long = {}

"""
-------------------------------------------------------------------------------------------------
Sweden
1
https://transparency.entsoe.eu/transmission-domain/r2/dayAheadPrices/show?name=&defaultValue=false&viewType=TABLE&areaType=BZN&atch=false&dateTime.dateTime=
17.03.2023+00:00|CET|DAY&biddingZone.values=
CTY|10YSE-1--------K!BZN|10Y1001A1001A44P&resolution.values=PT60M&
dateTime.timezone=CET_CEST&dateTime.timezone_input=CET+(UTC+1)+/+CEST+(UTC+2)
"""
url_timezone["SE1"] = "CET"
url_biddingZone["SE1"] = "CTY|10YSE-1--------K!BZN|10Y1001A1001A44P&resolution.values=PT60M&"
url_timezone_long["SE1"] = "dateTime.timezone=CET_CEST&dateTime.timezone_input=CET+(UTC+1)+/+CEST+(UTC+2)"
"""

2
"""
url_timezone["SE2"] = "CET"
url_biddingZone["SE2"] = "CTY|10YSE-1--------K!BZN|10Y1001A1001A45N&resolution.values=PT60M&"
url_timezone_long["SE2"] = "dateTime.timezone=CET_CEST&dateTime.timezone_input=CET+(UTC+1)+/+CEST+(UTC+2)"
"""

3
"""
url_timezone["SE3"] = "CET"
url_biddingZone["SE3"] = "CTY|10YSE-1--------K!BZN|10Y1001A1001A46L&resolution.values=PT60M&"
url_timezone_long["SE3"] = "dateTime.timezone=CET_CEST&dateTime.timezone_input=CET+(UTC+1)+/+CEST+(UTC+2)"
"""

4
"""
url_timezone["SE4"] = "CET"
url_biddingZone["SE4"] = "CTY|10YSE-1--------K!BZN|10Y1001A1001A47J&resolution.values=PT60M&"
url_timezone_long["SE4"] = "dateTime.timezone=CET_CEST&dateTime.timezone_input=CET+(UTC+1)+/+CEST+(UTC+2)"
"""
-------------------------------------------------------------------------------------------------

Denmark
1
https://transparency.entsoe.eu/transmission-domain/r2/dayAheadPrices/show?name=&defaultValue=false&viewType=TABLE&areaType=BZN&atch=false&dateTime.dateTime=
17.03.2023+00:00|CET|DAY&biddingZone.values=
CTY|10Y1001A1001A65H!BZN|10YDK-1--------W&resolution.values=PT60M&
dateTime.timezone=CET_CEST&dateTime.timezone_input=CET+(UTC+1)+/+CEST+(UTC+2)
"""
url_timezone["DK1"] = "CET"
url_biddingZone["DK1"] = "CTY|10Y1001A1001A65H!BZN|10YDK-1--------W&resolution.values=PT60M&"
url_timezone_long["DK1"] = "dateTime.timezone=CET_CEST&dateTime.timezone_input=CET+(UTC+1)+/+CEST+(UTC+2)"
"""

2
"""
url_timezone["DK2"] = "CET"
url_biddingZone["DK2"] = "CTY|10Y1001A1001A65H!BZN|10YDK-2--------M&resolution.values=PT60M&"
url_timezone_long["DK2"] = "dateTime.timezone=CET_CEST&dateTime.timezone_input=CET+(UTC+1)+/+CEST+(UTC+2)"
"""
-------------------------------------------------------------------------------------------------

Norway
1
https://transparency.entsoe.eu/transmission-domain/r2/dayAheadPrices/show?name=&defaultValue=false&viewType=TABLE&areaType=BZN&atch=false&dateTime.dateTime=
17.03.2023+00:00|CET|DAY&biddingZone.values=
CTY|10YNO-0--------C!BZN|10YNO-1--------2&resolution.values=PT60M&
dateTime.timezone=CET_CEST&dateTime.timezone_input=CET+(UTC+1)+/+CEST+(UTC+2)
"""
url_timezone["NO1"] = "CET"
url_biddingZone["NO1"] = "CTY|10YNO-0--------C!BZN|10YNO-1--------2&resolution.values=PT60M&"
url_timezone_long["NO1"] = "dateTime.timezone=CET_CEST&dateTime.timezone_input=CET+(UTC+1)+/+CEST+(UTC+2)"
"""

2
"""
url_timezone["NO2"] = "CET"
url_biddingZone["NO2"] = "CTY|10YNO-0--------C!BZN|10YNO-2--------T&resolution.values=PT60M&"
url_timezone_long["NO2"] = "dateTime.timezone=CET_CEST&dateTime.timezone_input=CET+(UTC+1)+/+CEST+(UTC+2)"
"""

2NSL
"""
url_timezone["NO2NSL"] = "CET"
url_biddingZone["NO2NSL"] = "CTY|10YNO-0--------C!BZN|50Y0JVU59B4JWQCU&resolution.values=PT60M&"
url_timezone_long["NO2NSL"] = "dateTime.timezone=CET_CEST&dateTime.timezone_input=CET+(UTC+1)+/+CEST+(UTC+2)"
"""

3
"""
url_timezone["NO3"] = "CET"
url_biddingZone["NO3"] = "CTY|10YNO-0--------C!BZN|10YNO-3--------J&resolution.values=PT60M&"
url_timezone_long["NO3"] = "dateTime.timezone=CET_CEST&dateTime.timezone_input=CET+(UTC+1)+/+CEST+(UTC+2)"
"""

4
"""
url_timezone["NO4"] = "CET"
url_biddingZone["NO4"] = "CTY|10YNO-0--------C!BZN|10YNO-4--------9&resolution.values=PT60M&"
url_timezone_long["NO4"] = "dateTime.timezone=CET_CEST&dateTime.timezone_input=CET+(UTC+1)+/+CEST+(UTC+2)"
"""

5
"""
url_timezone["NO5"] = "CET"
url_biddingZone["NO5"] = "CTY|10YNO-0--------C!BZN|10Y1001A1001A48H&resolution.values=PT60M&"
url_timezone_long["NO5"] = "dateTime.timezone=CET_CEST&dateTime.timezone_input=CET+(UTC+1)+/+CEST+(UTC+2)"
"""
-------------------------------------------------------------------------------------------------

Finland
Only 1
10YFI-1--------U
https://transparency.entsoe.eu/transmission-domain/r2/dayAheadPrices/show?name=&defaultValue=false&viewType=TABLE&areaType=BZN&atch=false&dateTime.dateTime=
19.03.2023+00:00|EET|DAY&biddingZone.values=
CTY|10YFI-1--------U!BZN|10YFI-1--------U&resolution.values=PT60M&
dateTime.timezone=EET_EEST&dateTime.timezone_input=EET+(UTC+2)+/+EEST+(UTC+3)
"""
url_timezone["FI"] = "EET"
url_biddingZone["FI"] = "CTY|10YFI-1--------U!BZN|10YFI-1--------U&resolution.values=PT60M&"
url_timezone_long["FI"] = "dateTime.timezone=EET_EEST&dateTime.timezone_input=EET+(UTC+2)+/+EEST+(UTC+3)"
"""
-------------------------------------------------------------------------------------------------

Estonia
https://transparency.entsoe.eu/transmission-domain/r2/dayAheadPrices/show?name=&defaultValue=false&viewType=TABLE&areaType=BZN&atch=false&dateTime.dateTime=
19.03.2023+00:00|EET|DAY&biddingZone.values=
CTY|10Y1001A1001A39I!BZN|10Y1001A1001A39I&resolution.values=PT60M&
dateTime.timezone=EET_EEST&dateTime.timezone_input=EET+(UTC+2)+/+EEST+(UTC+3)
"""
url_timezone["EE"] = "EET"
url_biddingZone["EE"] = "CTY|10Y1001A1001A39I!BZN|10Y1001A1001A39I&resolution.values=PT60M&"
url_timezone_long["EE"] = "dateTime.timezone=EET_EEST&dateTime.timezone_input=EET+(UTC+2)+/+EEST+(UTC+3)"
"""
-------------------------------------------------------------------------------------------------

Latvia
https://transparency.entsoe.eu/transmission-domain/r2/dayAheadPrices/show?name=&defaultValue=false&viewType=TABLE&areaType=BZN&atch=false&dateTime.dateTime=
19.03.2023+00:00|EET|DAY&biddingZone.values=
CTY|10YLV-1001A00074!BZN|10YLV-1001A00074&resolution.values=PT60M&
dateTime.timezone=EET_EEST&dateTime.timezone_input=EET+(UTC+2)+/+EEST+(UTC+3)
"""
url_timezone["LV"] = "EET"
url_biddingZone["LV"] = "CTY|10YLV-1001A00074!BZN|10YLV-1001A00074&resolution.values=PT60M&"
url_timezone_long["LV"] = "dateTime.timezone=EET_EEST&dateTime.timezone_input=EET+(UTC+2)+/+EEST+(UTC+3)"
"""
-------------------------------------------------------------------------------------------------

Lithuania
https://transparency.entsoe.eu/transmission-domain/r2/dayAheadPrices/show?name=&defaultValue=false&viewType=TABLE&areaType=BZN&atch=false&dateTime.dateTime
=19.03.2023+00:00|EET|DAY&biddingZone.values=
CTY|10YLT-1001A0008Q!BZN|10YLT-1001A0008Q&resolution.values=PT60M&
dateTime.timezone=EET_EEST&dateTime.timezone_input=EET+(UTC+2)+/+EEST+(UTC+3)
"""
url_timezone["LT"] = "EET"
url_biddingZone["LT"] = "CTY|10YLT-1001A0008Q!BZN|10YLT-1001A0008Q&resolution.values=PT60M&"
url_timezone_long["LT"] = "dateTime.timezone=EET_EEST&dateTime.timezone_input=EET+(UTC+2)+/+EEST+(UTC+3)"


def create_hourly_rates_entsoe(el_area, logreq, max_log_len):
    dt = datetime.strftime(datetime.now(), "%d.%m.%Y")
    url_entsoe  = url_start \
                  + str(dt) + "+00:00|" \
                  + url_timezone[el_area] \
                  + "|DAY&biddingZone.values=" + url_biddingZone[el_area]  \
                  + url_timezone_long[el_area]

    print(url_entsoe)
    try:
        request = requests.get(url_entsoe)
    except requests.exceptions.ConnectionError:
        info ="create_hourly_rates_entsoe:\n\t"+g_ui_text["t29"]
        f0.log_action(info, False)
        return(False)

    f0.log_request("requests_get", request, logreq, max_log_len)

    if request.status_code != 200 :
        info = "create_hourly_rates_entsoe:\n\t"+g_ui_text["t30f"]+" response:"+str(request.status_code)
        f0.log_action(info, False)
        return(False)

    """
    <div id="dv-data-table" class="table-container">
    ...
        <tbody>
                <tr>
                    <td rowspan="1" class="first">00:00 - 01:00</td>

                    <td class="dv-value-cell"><span onclick="showDetail('eu.entsoe.emfip.transmission_domain.r2.presentation.entity.DayAheadPricesMongoEntity', '640f10df623a7286783ce949', '2023-03-14T23:00:00.000Z', 'PRICE', 'CET');" class="data-view-detail-link">59.83</span></td>

                </tr>

                <tr>
                    <td rowspan="1" class="first">01:00 - 02:00</td>

                    <td class="dv-value-cell"><span onclick="showDetail('eu.entsoe.emfip.transmission_domain.r2.presentation.entity.DayAheadPricesMongoEntity', '6410626168dcf1a5565e4f78', '2023-03-15T00:00:00.000Z', 'PRICE', 'CET');" class="data-view-detail-link">56.95</span></td>

                </tr>
        </tbody>
    """

    # "dv-data-table".
    if request.text.find("dv-data-table") == -1 :
        info = "create_hourly_rates_entsoe:\n\t"+g_ui_text["t30f"]
        f0.log_action(info, False)
        return(False)

    t_from = 'dv-data-table'
    t_to = "</tbody>"
    start_of_table = request.text.split(t_from, 1)[1]
    start_of_table = start_of_table.split("<tbody>")[1]
    the_table = start_of_table.split(t_to)[0]
    the_table = the_table.replace('<tr>', '')
    the_table = the_table.replace('\t', '')
    the_table = the_table.replace('\n', '')
    the_table = the_table.replace(' ', '')

    t_rows = the_table.split('</tr>')
    #print(t_rows)
    f = open(te["fi_hourly_rate"], "w", encoding="utf8")
    i=0
    for tr in t_rows :
        """
        ><td rowspan="1" class="first">00:00 - 01:00</td>
        <td class="dv-value-cell"><span onclick="showDetail('eu.entsoe.emfip.transmission_domain.r2.presentation.entity.DayAheadPricesMongoEntity',
        '6410626168dcf1a5565e4f78', '2023-03-15T23:00:00.000Z', 'PRICE', 'CET');" class="data-view-detail-link">32.98</span></td>
        """
        if len(tr) == 0 :
            continue

        #ix = tr.find("T")      # 2023-03-15T23:00:00+01:00  'CET'
        #h = tr[ix+1] + tr[ix+2]

        #<td rowspan="1" class="first">00:00 - 01:00</td>
        s = tr.split('"first">')[1]
        h = s.split(':')[0]

        s = tr.split('class="data-view-detail-link">')[1]
        rate = s.split('</span>')[0]
        rate = round(float(rate)/10, 3)    # MWh -> kWh  /1000  Euro -> cent *100
        f.write(h+":"+str(rate)+"\n")

    f.close()
    return(True)


el_area, logreq, max_log_len = f0.get_args_fi_cre_hourly_rates("pgart_get_hourly_rates_entsoe_eu.py")
print(el_area, logreq, max_log_len)

nr_trials = 1
more = True
while more :
    if create_hourly_rates_entsoe(el_area, logreq, max_log_len) :
        f0.print_hourly_rates()
        sys.stdout.flush()
        exit()
    else :
        if nr_trials == max_nr_get_request_trials :
            print("-ok")
            exit()
        time.sleep(55)       # Try once more after a while.

    nr_trials += 1

