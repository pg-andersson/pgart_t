#!/usr/bin/python3
# This file is part of PGART_T (Pump Gradual Adjustment Room Temperature for Thermia Atlas).

# Copyright (C) 2023 PG Andersson <pg.andersson@gmail.com>.

# pgart_t is free software: you can redistribute it and/or modify it under the terms of GPL-3.0-or-later

# Functions to calculate the windchill effect based on SMHI wind and temperature forecast data.
#

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

g_lang = f8.get_language()
g_ui_text = f1.ui_texts(g_lang)
te = f1.get_pgart_env()


def create_smhi_url(my_lat, my_lon) :
    smhi_url = f1.get_url_template_smhi()
    smhi_url = smhi_url.replace("MY_LON", my_lon)
    smhi_url = smhi_url.replace("MY_LAT", my_lat)
    return(smhi_url)


def get_smhi_forecast(smhi_url, logreq, max_log_len) :
    json_smhi = ""
    try:
        response = requests.get(smhi_url)
    except requests.exceptions.ConnectionError:
        info ="get_smhi_forecast:\n\t"+g_ui_text["t26"]
        f0.log_action(info, False)
        return(False, json_smhi)

    f0.log_request("requests_get", response, logreq, max_log_len)

    if response.status_code != 200 :
        info = "get_smhi_forecast:\n\t"+g_ui_text["t27"]+" response:"+str(response.status_code)+" "+str(response.content)
        f0.log_action(info, False)
        return(False, json_smhi)

    json_smhi = json.loads(response.content)
    return(True, json_smhi)


def save_smhi_forecast_long(json_smhi) :
    json_formatted_str = json.dumps(json_smhi, indent=4)
    f = open(te["fi_smhi_forecast"] , "w", encoding="utf8")
    f.write(json_formatted_str)
    f.close()
    return(True)


def save_smhi_forecast_short(json_smhi_short) :
    f = open(te["fi_forecast_short"], "w", encoding="utf8")
    for dt in json_smhi_short :
        f.write(dt+":"+json_smhi_short[dt]+"\n")
    f.close()
    return(True)


def save_forecast_temp_wind(forecast_temp_wind) :
    f = open(te["fi_forecast_temp_wind"], "w", encoding="utf8")
    for dt in forecast_temp_wind :
        f.write(dt+":"+forecast_temp_wind[dt]+"\n")

    f.close()
    return(True)


def create_smhi_forecast_short(json_smhi) :
    dt_now = datetime.strftime(datetime.now(), "%Y-%m-%d")
    dt_tomorrow = datetime.strftime(datetime.now() + timedelta(1), "%Y-%m-%d")
    forecast_short = {}
    timeSeries = json_smhi['timeSeries']
    if timeSeries is None:
        info ="get_smhi_forecast_from_json_smhi:\n\t"+g_ui_text["t28"]
        f0.log_action(info, False)
    else :
        for timeSerie in json_smhi['timeSeries']:
            vt = timeSerie['validTime']
            dt = vt.split("T")
            ymd = dt[0]
            hh = dt[1].split("Z")[0]
            hh = hh.split(":")[0]
            if ymd == dt_now or ymd == dt_tomorrow  :
                params = timeSerie['parameters']
                for p in params :
                    #print(p['name'], p['values'][0])
                    if p['name'] == "t" :    # Temperature "unit": "Cel"
                        t =  p['values'][0]

                    if p['name'] == "ws" :   # Windchill "unit": "m/s"
                        ws =  p['values'][0]
                        par = ymd+"_"+hh
                        val = str(t)+","+str(ws)
                        forecast_short.update({par:val})
                        continue   # Found now

    return(forecast_short)


def calc_windchill_temp(t, ws) :
    t_windchill = 13.12 + 0.6215*t - 13.956*pow(ws, 0.16) + 0.48669*t*pow(ws, 0.16)
    t_diff = -(t - t_windchill)
    return(round(t_windchill, 1), round(t_diff, 1))


def create_forecast_temp_wind(json_smhi_short, windchill_wind_force_factor) :
    forecast_temp_wind = {}
    for par in json_smhi_short :
        buf = json_smhi_short[par].split(',')
        t = float(buf[0])
        ws = float(buf[1])
        ws =  round(ws * windchill_wind_force_factor, 1)   # Adjust the wind force if the forecast is not accurate enough.
        t_windchill = t
        t_diff = 0
        t_windchill, t_diff = calc_windchill_temp(t, ws)
        val = str(t)+" "+str(ws)+":"+str(t_windchill)+" "+str(t_diff)
        forecast_temp_wind.update({par:val})

    return(forecast_temp_wind)


def get_forecasts_from_smhi(my_lat, my_lon, windchill_wind_force_factor, logreq, max_log_len) :
    smhi_url = create_smhi_url(my_lat, my_lon)
    status, json_smhi = get_smhi_forecast(smhi_url, logreq, max_log_len)
    if not status :
        return(False)

    save_smhi_forecast_long(json_smhi)
    json_smhi_short = create_smhi_forecast_short(json_smhi)
    save_smhi_forecast_short(json_smhi_short)

    return(True)


def get_forecasts_from_file(windchill_wind_force_factor) :
    json_smhi_short = f0.get_forecast_short()
    if len(json_smhi_short) == 0 :
        return(json_smhi_short)

    forecast_temp_wind = create_forecast_temp_wind(json_smhi_short, windchill_wind_force_factor)
    save_forecast_temp_wind(forecast_temp_wind)

    return(forecast_temp_wind)

