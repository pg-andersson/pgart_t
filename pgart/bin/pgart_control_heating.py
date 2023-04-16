#!/usr/bin/python3
# This file is part of PGART_T (Pump Gradual Adjustment Room Temperature for Thermia Atlas).

# Copyright (C) 2023 PG Andersson <pg.andersson@gmail.com>.

# pgart_t is free software: you can redistribute it and/or modify it under the terms of GPL-3.0-or-later

# This program adjusts the indoor temperature based on rules in pg_control_thermia_heating.conf_se/en. See those files for explanations.

import sys
import platform
import os
import requests
import json
import time
import itertools
import ipaddress
import subprocess
import shutil

from pathlib import Path
from datetime import date,datetime,timedelta

import pgart_misc_func as f0
import pgart_env_func as f1
import pgart_get_smhi_forecasts_func as f2
import pgart_calc_hourly_rate_adj_func as f4
import pgart_thermia_online_genesis_func as f5
import pgart_thermia_modbus_func as f6
import pgart_read_control_params_func as f7
import pgart_lang_func as f8

g_lang = f8.get_language()
g_ui_text = f1.ui_texts(g_lang)
te = f1.get_pgart_env()


def save_settings(settings) :
    f = open(te["fi_settings_status"], "w", encoding="utf8")
    f.write(json.dumps(settings))
    f.close()


def get_settings() :
    fi = Path(te["fi_settings_status"])
    settings = {}
    if fi.is_file():
        f = open(te["fi_settings_status"], 'r' , encoding="utf8")
        settings = json.load(f)
        f.close()
    return(settings)


def get_setting(key, nr_fields) :
    settings = get_settings()
    fields = []
    fields.append("-")              # Initial values
    for i in range(nr_fields) :
        fields.append("0")

    if key in settings :
        s = settings[key].split(" ")
        i = 0
        nrs = len(s)
        while i < nrs:
            fields[i] = s[i]
            i += 1
    f0.log_action("Get "+key+":\n\t"+str(fields), False)
    return(fields)


def update_setting(key, val, log_txt) :
    dt = datetime.strftime(datetime.now(), "%Y-%m-%d")
    settings =  get_settings()
    settings[key] = dt+" "+val
    f0.log_action("Set "+key+":\n\t"+log_txt, False)
    save_settings(settings)


def remove_setting(key, log_txt) :
    settings = get_settings()
    if key in settings :
        settings.pop(key)
        save_settings(settings)
        f0.log_action("Del "+key+":\n\t"+log_txt, False)


def save_start_update(txt, hr, new_indoor_temp) :
    val = str(hr)+" "+str(new_indoor_temp)+" "+txt
    log_txt = txt
    update_setting("start_update", val, log_txt)


def get_last_start_update() :
    dt, hr, temp, s1, s2, s3, s4, s5, s6 = get_setting("start_update", 8)
    return(dt, int(hr), int(temp))


def remove_start_update(reason) :
    log_txt = g_ui_text["t19a"]
    remove_setting("start_update", log_txt)


def save_hourly_rate_setting(temp) :
    val = str(g_hour_now)+" "+str(temp)
    log_txt = g_ui_text["t1a"]+":"+str(temp)
    update_setting("hourly_rate", val, log_txt)


def get_last_hourly_rate_setting() :
    dt, hr, temp = get_setting("hourly_rate", 2)
    return(dt, int(hr), int(temp))


def remove_hourly_rate_setting(reason) :
    log_txt = g_ui_text["t19b"]+". "+g_ui_text["t19c"]+":"+reason
    remove_setting("hourly_rate", log_txt)


def save_top_rate_setting(temp) :
    val = str(g_hour_now)+" "+str(temp)
    log_txt = g_ui_text["t1a"]+":"+str(temp)
    update_setting("top_rate", val, log_txt)


def get_last_top_rate_setting() :
    dt, hr, temp = get_setting("top_rate", 2)
    return(dt, int(hr), int(temp))


def remove_top_rate_setting(reason) :
    log_txt = g_ui_text["t19b"]+". "+g_ui_text["t19c"]+":"+reason
    remove_setting("top_rate", log_txt)


def save_windchill_setting(evaluation_code, windchill_temp, temp_diff, temp_increase_final) :
    windchill_results = f1.get_windchill_evaluation_texts(g_lang)
    val = str(g_hour_now)+" "+str(evaluation_code)+" "+str(windchill_temp)+" "+str(temp_diff)+" "+str(temp_increase_final)

    log_txt = windchill_results[str(evaluation_code)]+" windchill_temp:"+str(windchill_temp)+ \
              " diff_real_windchill:"+str(temp_diff)+" pump_incr:"+str(temp_increase_final)

    update_setting("windchill", val, log_txt)


def get_last_windchill_setting() :
    dt, hr, a, b, c, temp = get_setting("windchill", 5)
    return(dt, int(hr), int(temp))


def remove_windchill_setting(reason) :
    log_txt = g_ui_text["t19b"]+". "+g_ui_text["t19c"]+":"+reason
    remove_setting("windchill", log_txt)


def save_indoor_temp_setting(change_types, new_indoor_temp, hr_rate_usage, hr_rate_temp_decrease, windchill_temp_usage, windchill_temp_increase) :
    val = str(g_hour_now)+" "+str(new_indoor_temp)

    if change_types[0] == -1 :
        txt = g_ui_text["t3"]             # Last run failed.
    else :
        if g_weekday_active == 1 :
            txt = g_ui_text["t3a"]
        else :
            txt = g_ui_text["t3b"]

        if change_types[0] == 1 :
            txt += " "+g_ui_text["t4a"]   # Scheduled change
        else:
            txt += " "+g_ui_text["t4b"]   # No scheduled change

        if change_types[1] == 1 :
            txt += " "+g_ui_text["t4c"]   # hr_rate_usage == "reset_hour"

        if change_types[2] == 1 :
            txt += " "+g_ui_text["t4d"]   # windchill_temp_usage == "reset_hour"

        if change_types[3] == 1 :
            txt += " "+g_ui_text["t4e"]   # hr_rate_usage == "set_hour"

        if change_types[4] == 1 :
            txt += " "+g_ui_text["t4f"]   # windchill_temp_usage == "set_hour"

        if change_types[5] == 1 :
            txt += " "+g_ui_text["t4g"]   # Temp set manually.

    log_txt = txt+" "+g_ui_text["t1"]+":"+str(new_indoor_temp)+", hr_rate_temp_decr/incr:"+str(hr_rate_temp_decrease)+ \
              ", windchill_temp_incr/decr:"+str(windchill_temp_increase)

    update_setting("indoor_temp", val, log_txt)


def get_last_indoor_temp_setting() :
    dt, hr, new_indoor_temp = get_setting("indoor_temp", 2)
    return(dt, int(hr), int(new_indoor_temp))


def remove_indoor_temp_setting(reason) :
    log_txt = g_ui_text["t19b"]+". "+g_ui_text["t19c"]+":"+reason
    remove_setting("indoor_temp", log_txt)


def remove_obsolete_indoor_temp_setting() :
    dt_saved, hr, new_indoor_temp = get_last_indoor_temp_setting()
    if dt_saved == "-" :
        return()

    dt_now = datetime.strftime(datetime.now(), "%Y-%m-%d")
    dt_diff = (datetime.strptime(dt_now, "%Y-%m-%d") - datetime.strptime(dt_saved, "%Y-%m-%d")).days
    if dt_diff > 0 :  # Valid only today.
        remove_indoor_temp_setting("too-old")


def remove_now_obsolete_settings(reason) :
    remove_hourly_rate_setting(reason)
    remove_top_rate_setting(reason)
    remove_windchill_setting(reason)


def save_run_summary(
                     call_id, change_types, outdoor_temp, room_temp, sensor_temp,
                     current_heating_effect, new_indoor_temp, hr_rate_usage, new_hr_rate_temp_decrease,
                     windchill_temp_usage, windchill_temp_increase) :

    fi = Path(te["fi_run_summary_log"])
    if not fi.is_file():
        # Copy the log explanations to the new summary log file.
        try:
            shutil.copy(te["fi_run_summary_log_explanations"], te["fi_run_summary_log"])
        except:
            print("Could not copy "+te["fi_run_summary_log_explanations"]+" => "+te["fi_run_summary_log"])

    f = open(te["fi_run_summary_log"], "a", encoding="utf8")
    dt = datetime.strftime(datetime.now(), "%Y-%m-%d_%H:%M")
    actions = ""
    for i in change_types :
        actions += str(i)

    if change_types[0] == 1 :
        ct = "New_schema"
    else :
        ct = "No_schema"

    if change_types[5] == 1 :
        ct = "Set_manually"
    """
    print(change_types, outdoor_temp, room_temp, sensor_temp,
                     current_heating_effect, new_indoor_temp, hr_rate_usage, new_hr_rate_temp_decrease,
                     windchill_temp_usage, windchill_temp_increase)
    """
    txt = "{:16s} {:2s} {:6s} {:12s} {:4s}{:<3d} {:5s}{:<3d} {:7s}{:3s} {:5s}{:<2d} {:4s}{:<2d} {:8s}{:01d} {:8s} {:10s}{:01d} {:10s}"
    line = txt.format(
                      dt, call_id, actions, ct, "out:", outdoor_temp, "room:", room_temp, "sensor:", sensor_temp, \
                      "pump:", current_heating_effect,  "new:", new_indoor_temp, "hr_rate:", new_hr_rate_temp_decrease, hr_rate_usage, \
                      "windchill:", windchill_temp_increase, windchill_temp_usage)

    f.write(line + "\n")
    f.close()


def create_hourly_settings_indoor_temp() :
    if g_week_day_nr in g_weekday_indoor_temp_hours :
        weekday_active=1
        set_indoor_temp_hours = g_weekday_indoor_temp_hours[g_week_day_nr]
    else :
        weekday_active=0
        set_indoor_temp_hours = g_general_pars['set_indoor_temp_hours']

    # Create a dict of set_indoor_temp_hours=20_14,06_20 => [20: 14, 06: 20]
    th=set_indoor_temp_hours.split(',')
    tmp_hours_to_set_new_heating_effect = {}
    for x in th :
        buf=x.split('_')
        tmp_hours_to_set_new_heating_effect.update({int(buf[0]): int(buf[1])})   # Shall be numeric

    return(weekday_active, tmp_hours_to_set_new_heating_effect)


def create_range_hourly_rate_temp_decrease() :
    hourly_rate_decrease_hours = g_general_pars['hourly_rate_decrease_hours']
    # Create a dict of hourly_rate_decrease_hours=06-20 => ["06": "20"]
    th=hourly_rate_decrease_hours.split(',')
    tmp_hours = {}
    for x in th :
        buf=x.split('-')
        tmp_hours.update({int(buf[0]): int(buf[1])})

    return(tmp_hours)


def get_pump_info() :
    if g_general_pars['pump_access_method'] == "a" :        # Use Thermia online_genesis?
        # Get the configuration, request_headers, ID-number, heatingEffectRegister and heatingEffect (indoor temperature).
        info, configuration, request_headers = f5.thermia_api_login(g_general_pars['login_id'], g_general_pars['password'], logreq, g_general_pars['max_log_len'])
        f0.log_action("get_pump_info: thermia_api_login:\n\t"+info, False)
        f0.print_json_var(g_verbose_logging, 2, "Thermia_config", configuration)

        devices = f5.thermia_api_get_devices(configuration, request_headers, logreq, g_general_pars['max_log_len'])
        f0.print_json_var(g_verbose_logging, 3, "devices", devices)

        dev_info = f5.thermia_api_get_device_info(configuration, request_headers, devices[0]['id'], logreq, g_general_pars['max_log_len'])
        f0.print_json_var(g_verbose_logging, 3, "dev_info", dev_info)

        temp = dev_info["heatingEffect"]
        f0.log_action("thermia_api_get_heating_effect:\n\tstatus:ok. heating_effect:"+str(temp), False)

        return(dev_info["outdoorTemperature"], dev_info["indoorTemperature"], dev_info["heatingEffect"],
               devices[0]['id'], dev_info["heatingEffectRegisters"][1], configuration, request_headers )

    # Get the indoor temperatures via Modbus.
    current_heating_effect = f6.tcp_get_indoor_temperature(g_general_pars['pump_ip_address'], logreq)
    outdoor_temp = f6.tcp_get_outdoor_temperature(g_general_pars['pump_ip_address'], logreq)
    room_temp = f6.tcp_get_room_sensor_temperature(g_general_pars['pump_ip_address'], logreq)

    return(outdoor_temp, room_temp, current_heating_effect, "", "", "", "")


def set_pump_info(new_indoor_temp, device_id, heating_effect_register, configuration, request_headers) :
    if g_general_pars['pump_access_method'] == "a" :
        f5.thermia_api_set_indoor_temperature(
                                              request_headers, configuration, device_id, heating_effect_register,
                                              new_indoor_temp, logreq, g_general_pars['max_log_len'])
    else :
        f6.tcp_set_indoor_temperature(g_general_pars['pump_ip_address'], new_indoor_temp, logreq)


def get_indoor_external_sensor_temp() :
    dt = datetime.strftime(datetime.now(), "%Y-%m-%d_%H:%M:%S")
    sensor_temp = "-273"
    if g_general_pars['read_external_indoor_sensor'] == "y" :
        if g_general_pars['external_pgm_read_indoor_sensor'] != "," :
            cmd = "/usr/bin/python3 "+te["g_bin_dir"]+"/"+f0.get_exec_str(g_general_pars['external_pgm_read_indoor_sensor'])
        else :
            cmd = "/usr/bin/python3 "+te["g_bin_dir"]+"/pgart_get_indoor_temp_raspberry_pi.py"

        if not f0.exec_external_pgm("temp_reading", cmd) :
            txt = "get_indoor_external_sensor_temp:\n\tFailed to create:"+te["fi_indoor_temp_reading"]+" temperature reading not working."
            f0.log_action(txt, False)
            f0.send_mail(dt+" "+txt)
        else :
            status, info, dt, sensor_temp = f0.get_ext_temp_reading()
            if not status :
                print(info)

    return(sensor_temp)


def set_new_indoor_temp() :
    change_types = [0,0,0,0,0,0]
    hr_rate_usage = "-"
    new_hr_rate_temp_decrease = 0
    current_heating_effect = 0
    windchill_temp_usage = "-"
    windchill_temp_increase = 0

    sensor_temp = get_indoor_external_sensor_temp()
    outdoor_temp, room_temp, current_heating_effect, device_id, heating_effect_register, configuration, request_headers = get_pump_info()  # On error no return.
    new_indoor_temp = current_heating_effect    # Use the current indoor temperature from the pump as default.

    if g_hour_now in g_hourly_settings_indoor_temp or hr_rates_decrease_active or windchill_increase_active :
        hr_rate_usage, hr_rate_temp_decrease, last_hr_rate_temp_decrease = get_temp_adj_rates()
        print("hr_rate_usage:", hr_rate_usage, hr_rate_temp_decrease, last_hr_rate_temp_decrease )

        windchill_temp_usage, windchill_temp_increase, last_windchill_temp_increase = get_temp_adj_windchill_effect(current_heating_effect)
        print("windchill_temp_usage:", windchill_temp_usage, windchill_temp_increase, last_windchill_temp_increase )

        # Set the temperature but only if it has not been manually set since the last run.
        # If the current_heating_effect is not the same as the saved one a manual change has been done. That is valid until the last run for a day.
        last_dt, last_hr, last_indoor_temp = get_last_indoor_temp_setting()

        last_hourly_setting_today = sorted(g_hourly_settings_indoor_temp.keys()).pop()  # The last setting for a day is the last hour.
        if g_hour_now == last_hourly_setting_today :
            # The last run today. Night run.
            remove_now_obsolete_settings("obsolete-because-last-run-of-the-day")
            remove_indoor_temp_setting("obsolete-because-last-run-of-the-day")
            hr_rate_temp_decrease = 0       # Must not impact a scheduled night run
            windchill_temp_increase = 0
            hr_rate_usage = "off"
            windchill_temp_usage = "off"
            f0.log_action("set_new_indoor_temp:\n\t"+g_ui_text["t17"]+str(current_heating_effect), False)

        else :  # Not the night run.
            if last_dt != "-" :
                # There is a saved heating_effect.
                if last_indoor_temp != current_heating_effect :
                    # Do not change a manually set indoor temperature.
                    remove_now_obsolete_settings("obsolete-because-manual-set-temp")
                    remove_start_update("obsolete-because-manual-set-temp")
                    f0.log_action(
                                  "set_new_indoor_temp:\n\t"+g_ui_text["t18"]+str(current_heating_effect)+
                                  ", "+g_ui_text["t18c"]+str(last_indoor_temp),
                                  False)

                    change_types[5] = 1 # Manual change
                    save_run_summary(
                                     "L1", change_types, outdoor_temp, room_temp, sensor_temp,
                                     current_heating_effect, current_heating_effect, hr_rate_usage, new_hr_rate_temp_decrease,
                                     windchill_temp_usage, windchill_temp_increase)
                    return()

        if g_hour_now in g_hourly_settings_indoor_temp :
            # There is a scheduled change for this hour.
            new_indoor_temp = g_hourly_settings_indoor_temp[g_hour_now]
            last_hr_rate_temp_decrease = 0      # Old values must not impact a new scheduled change.
            last_windchill_temp_increase = 0

            if hr_rate_usage.find("reset_hour") != -1  :     # A "reset_hour" => forget the history.
                remove_hourly_rate_setting("scheduled_change_reset_hour_obsolete")
                remove_top_rate_setting("scheduled_change_reset_hour_obsolete")
                change_types[1] = 1

            if windchill_temp_usage == "reset_hour" :
                remove_windchill_setting("scheduled_change_reset_hour_obsolete")
                change_types[2] = 1

            change_types[0] = 1
            f0.log_action("set_new_indoor_temp:\n\t"+g_ui_text["t18b"]+" "+str(new_indoor_temp), False)

        else :      # Not any scheduled change.
            change_types[0] = 0
            if hr_rate_usage.find("reset_hour") != -1 :
                # A "reset_hour" => apply an increase to get back to the normal temperature.
                new_indoor_temp = new_indoor_temp + hr_rate_temp_decrease
                remove_hourly_rate_setting("reset_back_to_normal")
                remove_top_rate_setting("reset_back_to_normal")
                change_types[1] = 1

            if windchill_temp_usage == "reset_hour" :
                # A "reset_hour" => apply a decrease to get back to the normal temperature.
                new_indoor_temp = new_indoor_temp - windchill_temp_increase
                remove_windchill_setting("reset_back_to_normal")
                change_types[2] = 1

        if hr_rate_usage.find("hour_rate_paus") != -1 :
            # No decrease now because it would have been more than two consecutive hours of decrease for the hour span.
            f0.log_action("set_new_indoor_temp:\n\t"+g_ui_text["t19d"], False)

        if hr_rate_usage.find("rate_too_low") != -1 :
            # No decrease
            rate = round(float(hr_rate_usage.split("=")[1]), 3)
            f0.log_action(
                          "set_new_indoor_temp:\n\t"+g_ui_text["t19e"]+" "+g_ui_text["t19f"]+":"+str(rate)+
                          " < hourly_rate_only_decrease_when_rate_above:"+str(g_general_pars["hourly_rate_only_decrease_when_rate_above"]),
                          False)

        if hr_rate_usage == "set_hour" :
            # Apply a new hourly_rate decrease or adjust an existing one.
            new_hr_rate_temp_decrease = abs(last_hr_rate_temp_decrease - hr_rate_temp_decrease)
            if new_hr_rate_temp_decrease == 0 :
                #if last_hr_rate_temp_decrease == hr_rate_temp_decrease :
                # the indoor temperature from the pump is still valid. It was hr_rate_temp_decrease before this hour.
                f0.log_action("set_new_indoor_temp:\n\t"+g_ui_text["t19g"]+" "+str(hr_rate_temp_decrease), False)

            if (last_hr_rate_temp_decrease != hr_rate_temp_decrease) and (last_hr_rate_temp_decrease > 0):
                # Only the + or - difference will be applied. Can only happen when the config "hourly_rate_decrease_nr_grades" has been changed between two runs.
                f0.log_action("set_new_indoor_temp:\n\t"+g_ui_text["t19h"]+" "+str(last_hr_rate_temp_decrease - hr_rate_temp_decrease), False)

            if last_hr_rate_temp_decrease == 0 :
                # the new hr_rate_temp_decrease will be applied
                f0.log_action("set_new_indoor_temp:\n\t"+g_ui_text["t19i"]+" "+str(hr_rate_temp_decrease), False)

            new_indoor_temp = new_indoor_temp + last_hr_rate_temp_decrease - hr_rate_temp_decrease
            change_types[3] = 1

        if windchill_temp_usage == "set_hour" :
            # Apply a new windchill increase or adjust an existing one.
            if last_windchill_temp_increase == windchill_temp_increase :
                # The indoor temperature from the pump is still valid. It was increased before this hour.
                f0.log_action("set_new_indoor_temp:\n\t"+g_ui_text["t18d"]+" "+str(windchill_temp_increase), False)

            if (last_windchill_temp_increase != windchill_temp_increase) and (last_windchill_temp_increase > 0) :
                # Only the + or - difference will be applied.
                f0.log_action("set_new_indoor_temp:\n\t"+g_ui_text["t18e"]+" "+str(windchill_temp_increase - last_windchill_temp_increase), False)

            if last_windchill_temp_increase == 0 :
                # the new windchill_temp_increase will be applied.
                f0.log_action("set_new_indoor_temp:\n\t"+g_ui_text["t18f"]+" "+str(windchill_temp_increase), False)

            new_indoor_temp = new_indoor_temp + windchill_temp_increase - last_windchill_temp_increase
            change_types[4] = 1

    else :
        # Nothing new to set but if there is an update that failed during the last run it shall be tried again now.
        failed_dt, failed_hr, failed_to_set_this_indoor_temp = get_last_start_update()
        if failed_dt != "-" :
            new_indoor_temp = failed_to_set_this_indoor_temp
            current_heating_effect = 0  # Is not known. No need either.
            change_types[0] = -1
            f0.log_action("set_new_indoor_temp:\n\t"+g_ui_text["t22"]+" "+failed_dt+" "+str(failed_hr)+" "+str(failed_to_set_this_indoor_temp), False)

        else :
            # There is nothing to do during this hour.
            if g_weekday_active == 1 :
                txt = g_ui_text["t3a"]
            else :
                txt = g_ui_text["t3b"]

            f0.log_action("set_new_indoor_temp:\n\t"+txt+" "+g_ui_text["t23"], False)
            save_run_summary(
                             "L2", change_types, outdoor_temp, room_temp, sensor_temp,
                             current_heating_effect, new_indoor_temp, hr_rate_usage, new_hr_rate_temp_decrease,
                             windchill_temp_usage, windchill_temp_increase)
            return()

    if new_indoor_temp > 25 :
        # Make sure the new temperature is not insane.
        f0.log_action("set_new_indoor_temp:\n\t"+g_ui_text["t20"]+": "+str(new_indoor_temp)+" max_indoor_temp: 25", False)
        new_indoor_temp = 25

    txt = "hr_rate_usage:"+hr_rate_usage+" hr_rate_temp_decr/incr:"+str(new_hr_rate_temp_decrease)+ \
          " windchill_temp_usage:"+windchill_temp_usage+" windchill_temp_incr/decr:"+str(windchill_temp_increase)+ \
          " if_new_failure_this_temp:"+str(new_indoor_temp)

    save_start_update(txt, g_hour_now, new_indoor_temp)

    if new_indoor_temp != current_heating_effect :
        set_pump_info(new_indoor_temp, device_id, heating_effect_register, configuration, request_headers)     # On error no return.
    else : # No need to access the pump.
       f0.log_action("set_new_indoor_temp:\n\t"+g_ui_text["t18a"]+str(new_indoor_temp), False)

    save_indoor_temp_setting(change_types, new_indoor_temp, hr_rate_usage, new_hr_rate_temp_decrease, windchill_temp_usage, windchill_temp_increase)

    save_run_summary(
                     "L3", change_types, outdoor_temp, room_temp, sensor_temp, current_heating_effect,
                     new_indoor_temp, hr_rate_usage, new_hr_rate_temp_decrease,
                     windchill_temp_usage, windchill_temp_increase)

    remove_start_update("Done")    # The start status file is obsolete now.


def get_windchill_temp_adjustment(current_heating_effect) :
    forecast_temp = 0
    forecast_wind = 0
    windchill_temp = 0
    temp_diff = 0
    temp_increase_wanted = 0
    temp_increase_final = 0
    forecast_temp_wind = {}
    dt = datetime.strftime(datetime.now(), "%Y-%m-%d_%H:%M:%S")

    # Calculations must be done from the last scheduled temperature. Not the actual temperature which is affected by the last adjustment.
    k = sorted(g_hourly_settings_indoor_temp.keys()).pop()  # Get the last entry of the day.
    indoor_temp = g_hourly_settings_indoor_temp[k]          # This will be the temperature between 24 and the first one in the morning.
    for k in sorted(g_hourly_settings_indoor_temp.keys(), reverse=True) : # Get the last scheduled temperature
        if g_hour_now >= k :
            indoor_temp = g_hourly_settings_indoor_temp[k]
            break

    # If the new indoor temperature will be less than windchill_adjust_only_when_set_indoor_temp_is_above => no action
    if indoor_temp < int(g_general_pars['windchill_adjust_only_when_set_indoor_temp_is_above']) :
        f0.log_action(
                      "get_windchill_temp_adjustment:\n\tindoor_temp:"+str(indoor_temp)+
                      " < windchill_adjust_only_when_set_indoor_temp_is_above:"+str(g_general_pars['windchill_adjust_only_when_set_indoor_temp_is_above']),
                      False)
        return(1, indoor_temp, forecast_temp, forecast_wind, windchill_temp, temp_diff, temp_increase_wanted, temp_increase_final)

    if windchill_use_smhi:
        cmd = "/usr/bin/python3  "+te['g_bin_dir']+"/pgart_get_smhi_forecasts.py"+\
              " --lat "+g_general_pars['my_lat']+" --lon "+g_general_pars['my_lon']+\
              " --windfact "+g_general_pars['windchill_wind_force_factor']+\
              " --logreq "+str(logreq)+" --maxlog "+g_general_pars['max_log_len']

        if not f0.exec_external_pgm("forecast", cmd) : # SMHI not available.
            txt = "get_windchill_temp_adjustment:\n\tFailed to create:"+te["fi_forecast_short"]+" SMHI forecasts not working."
            f0.log_action(txt, False)
            f0.send_mail(dt+" "+txt)
            return(-2, indoor_temp, forecast_temp, forecast_wind, windchill_temp, temp_diff, temp_increase_wanted, temp_increase_final)
    else :
        cmd =  "/usr/bin/python3  "+te["g_bin_dir"]+"/"+f0.get_exec_str(g_general_pars['external_pgm_create_forecasts'])
        if not f0.exec_external_pgm("forecast", cmd) :
            txt = "get_windchill_temp_adjustment:\n\tFailed to create:"+te["fi_forecast_short"]+" forecasts not working."
            f0.log_action(txt, False)
            f0.send_mail(dt+" "+txt)
            return(-3, indoor_temp, forecast_temp, forecast_wind, windchill_temp, temp_diff, temp_increase_wanted, temp_increase_final)

    forecast_temp_wind = f2.get_forecasts_from_file( float(g_general_pars['windchill_wind_force_factor']))
    if len(forecast_temp_wind) == 0 : # SMHI or other returned an empty answer. Let it be
        return(-1, indoor_temp, forecast_temp, forecast_wind, windchill_temp, temp_diff, temp_increase_wanted, temp_increase_final)

    f0.print_json_var(g_verbose_logging, 7, "forecast_temp_wind", forecast_temp_wind)

    # Increase the current_heating_effect if the difference between forecast and windchill temperatures is big enough.
    # (diff greater than windchill_min_apparent_temp_diff for the hour pointed to by windchill_use_forecast_this_nr_hours_ahead)
    nr_hours_ahead = int(g_general_pars['windchill_use_forecast_this_nr_hours_ahead'])

    # Get the forecast information from the forecast_temp_wind structure for the wanted hour.
    hr_forecast = g_hour_now + nr_hours_ahead
    if hr_forecast >=24 :
        hr_forecast = hr_forecast - 24     # Start at 0 instead of 24 => next day.
        dt_tomorrow = datetime.strftime(datetime.now() + timedelta(1), "%Y-%m-%d")
        dt_hr_forecast = dt_tomorrow+"_{:02d}".format(hr_forecast)
    else :
        dt_today = datetime.strftime(datetime.now(), "%Y-%m-%d")
        dt_hr_forecast = dt_today+"_{:02d}".format(hr_forecast)

    # forecast_temp_wind structure:
    # key = dt_hr_forecast
    # val = forecast_temp forecast_wind : apparent_temp diff(forecast_temp apparent_temp)
    # key = 2022-11-24_01
    # val = 2.7 3.3:-0.5 -3.2

    if not dt_hr_forecast in forecast_temp_wind :
       return(-4, indoor_temp, forecast_temp, forecast_wind, windchill_temp, temp_diff, temp_increase_wanted, temp_increase_final)

    s = forecast_temp_wind[dt_hr_forecast].split(":")    # 2.7 3.3:-0.5 -3.2
    forecast_temp = float(s[0].split(" ")[0])    # 2.7
    forecast_wind = float(s[0].split(" ")[1])    # 3.3
    windchill_temp = float(s[1].split(" ")[0])   # -0.5
    temp_diff = float(s[1].split(" ")[1])        # -3.2

    # Is the wind cooling enough to maintain an existing increased temperature or to increase the current indoor temperature?
    if abs(temp_diff) < abs(float(g_general_pars['windchill_min_apparent_temp_diff'])) :
       f0.log_action(
                     "get_windchill_temp_adjustment:\n\ttemp_diff:"+str(abs(temp_diff))+
                     " < windchill_min_apparent_temp_diff:"+str(abs(float(g_general_pars['windchill_min_apparent_temp_diff']))),
                     False)
       return(2, indoor_temp, forecast_temp, forecast_wind, windchill_temp, temp_diff, temp_increase_wanted, temp_increase_final)

    # Now. Increase the current_heating_effect by a number based on the temp_diff.
    # The heat curve on the pump shows that:
    # - when the outdoor temperature decreases by 1 degree the supply line temperature will increase by roughly 1 degree.
    # - an increase of the indoor temperature by 1 degree will increase the supply line temperature by 2.5 degrees.
    # This will give the following rules:
    # For each -2.5 degree the windchill temperature is below the outdoor temperature the current_heating_effect shall be increased by 1 degree.
    # This new current_heating_effect must not exceed windchill_max_indoor_temp_increase and the simulated outdoor
    # temperature must not get below -25 degrees.

    # Get the maximum allowed indoor temperature increase that will still keep the supply line temperature below 60 degrees.
    max_allowed_increase = 25 - abs(forecast_temp)/2.5

    # Calculate the expected increase of the indoor temperature depending on the difference between the windchill and the outdoor temperatures.
    temp_increase_wanted = abs(temp_diff)/2.5
    temp_increase_final = temp_increase_wanted

    evaluation_code = 3
    # If temp_increase_wanted is above max_allowed_increase the final increase must be reduced.
    if temp_increase_final > max_allowed_increase :
        temp_increase_final = max_allowed_increase
        evaluation_code = 4

    # As above but for windchill_max_indoor_temp_increase.
    if temp_increase_final > int(g_general_pars['windchill_max_indoor_temp_increase']) :
        temp_increase_final = int(g_general_pars['windchill_max_indoor_temp_increase'])
        evaluation_code = 5

    return(evaluation_code, indoor_temp, forecast_temp, forecast_wind, windchill_temp, temp_diff, temp_increase_wanted, temp_increase_final)


def log_windchill_statistics(indoor_temp, forecast_temp, forecast_wind, windchill_temp, temp_diff, temp_increase_wanted,
                            temp_increase_final, evaluation_code) :
    windchill_results = f1.get_windchill_evaluation_texts(g_lang)
    dt = datetime.strftime(datetime.now(), "%Y-%m-%d_%H:%M")
    f = open(te["fi_windchill_stats"], "a", encoding="utf8")

    stats = "{} h:{:>2d} last_indoor_t:{:>2d} forec_t:{:>4.1f} forec_wind:{:>4.1f} factor:{:>2.1f} windchill_t:{:>4.1f} diff:{:>4.1f} wanted_inc:{:>4.1f} got_inc:{:>4.1f} {}"
    line = stats.format(
                        dt, g_hour_now, indoor_temp,
                        forecast_temp, forecast_wind,
                        float(g_general_pars['windchill_wind_force_factor']), windchill_temp,
                        temp_diff, temp_increase_wanted,
                        temp_increase_final, windchill_results[str(evaluation_code)])
    f.write(line+"\n")
    f.close()


def get_temp_adj_windchill_effect(current_heating_effect) :
    if g_general_pars['use_windchill_compensation'] == "n" :
        return("off", 0, 0)

    # Time to increase the indoor temperature because of the windchill effect?
    # Time to set back to ordinary temperature if a previous increase is not valid any more?
    windchill_temp_usage = "off"
    evaluation_code, indoor_temp, forecast_temp, forecast_wind, windchill_temp, temp_diff, temp_increase_wanted, temp_increase_final = get_windchill_temp_adjustment(current_heating_effect)

    last_windchill_dt, last_windchill_hr, last_windchill_temp_increase = get_last_windchill_setting()
    if evaluation_code in [ -1, -2, -3, -4, 1, 2] :
        # Not any new change but an old one could be around.
        if last_windchill_dt != "-" :    # There is a status file. The previously increased temperature shall be decreased now.
            windchill_temp_usage = "reset_hour"
            temp_increase_final = last_windchill_temp_increase

    else :  # evaluation_code: 3, 4, 5
        # New indoor temperature to be set.
        temp_increase_final = int(round(temp_increase_final + 0.001))  # 0.001 because round off behaviour
        save_windchill_setting(evaluation_code, windchill_temp, temp_diff, temp_increase_final)
        windchill_temp_usage = "set_hour"

    if evaluation_code < 0 :        # evaluation_codes -1, -2, -3, -4. No contact or other error, can not do any new adjustment.
        return(windchill_temp_usage, temp_increase_final, last_windchill_temp_increase)

    log_windchill_statistics(indoor_temp, forecast_temp, forecast_wind, windchill_temp, temp_diff, temp_increase_wanted,
        temp_increase_final, evaluation_code)

    return(windchill_temp_usage, temp_increase_final, last_windchill_temp_increase)


def get_temp_adj_top_hourly_rate() :
    hr_rate_usage = "off"
    hr_rate_temp_decrease = 0

    last_dt, last_hr, last_hr_rate_temp_decrease = get_last_top_rate_setting()
    hr_rates = f0.get_hourly_rates(te["fi_hourly_rate"])
    sorted_hr_rates = sorted(hr_rates.items(), key=lambda x: float(x[1]), reverse=True)
    top_hours = {}
    for i in range(0, int(g_general_pars["hourly_rate_decrease_during_top_hours"]) ) :
        k, v = list(sorted_hr_rates)[i]
        top_hours[k] = v

    f0.print_json_var(g_verbose_logging, 4, "hr_rates", hr_rates)
    f0.print_json_var(g_verbose_logging, 4, "top_hours", top_hours)

    if top_hours.get(g_hour_now, "0") != "0" : # I this hour a top hour?
        a = float(g_general_pars["hourly_rate_only_decrease_when_rate_above"]) * 100
        b = top_hours.get(g_hour_now)
        if a < b : # Decrease temp?
            hr_rate_temp_decrease = int(g_general_pars['hourly_rate_decrease_nr_grades'])
            save_top_rate_setting(hr_rate_temp_decrease)
            hr_rate_usage = "set_hour"

    if hr_rate_usage == "off" :
        if last_hr_rate_temp_decrease > 0 :                        # Is there a saved temp_decrement?
            hr_rate_temp_decrease = last_hr_rate_temp_decrease     # Increase again
            hr_rate_usage = "reset_hour"

    return(hr_rate_usage, hr_rate_temp_decrease, last_hr_rate_temp_decrease)


def get_temp_adj_hourly_rate() :
    hr_rate_usage = "off"
    hr_rate_temp_decrease = 0
    hour_price = {}

    for i in range(0,24) :
        hour_price[i] = 0

    decr_range = create_range_hourly_rate_temp_decrease()
    for start_hr, stop_hr in decr_range.items() :
        hour_map, tmp_map_price, price = f4.create_top_hour_adj_maps(te["fi_hourly_rate"], start_hr, stop_hr, g_verbose_logging)
        for i in range(0,24) :
            if tmp_map_price[i] != 0 :
                hour_price[i] = tmp_map_price[i]

    f0.print_json_var(g_verbose_logging, 4, "hour_price", hour_price)

    last_dt, last_hr, last_hr_rate_temp_decrease = get_last_hourly_rate_setting()

    rate_too_low = False
    if hour_price[g_hour_now] > 0 :
        if float(g_general_pars["hourly_rate_only_decrease_when_rate_above"]) * 100 < hour_price[g_hour_now] : # Decrease temp?
            hr_rate_temp_decrease = int(g_general_pars['hourly_rate_decrease_nr_grades'])
            save_hourly_rate_setting(hr_rate_temp_decrease)
            hr_rate_usage = "set_hour"
        else :
            rate_too_low = True

    if hr_rate_usage == "off" :
        if hour_price[g_hour_now] == -1 :       # A paus hour. Not an hourly rate decrease this hour.
            hr_rate_usage = "hour_rate_paus"

        if last_hr_rate_temp_decrease > 0 :                     # Is there an hr_rate_temp_decrease.
            hr_rate_temp_decrease = last_hr_rate_temp_decrease  # Increase again
            if hr_rate_usage == "hour_rate_paus" :
                hr_rate_usage = "reset_hour:hour_rate_paus"
            else :
                hr_rate_usage = "reset_hour"

        if rate_too_low :
            hr_rate_usage += ":rate_too_low="+str(round(hour_price[g_hour_now]/100, 2))

    return(hr_rate_usage, hr_rate_temp_decrease, last_hr_rate_temp_decrease)


def get_temp_adj_rates() :
    hr_rate_usage = "off"
    hr_rate_temp_decrease = 0
    last_hr_rate_temp_decrease = 0
    if hr_rates_decrease_active :  # Only run rate adjustments if the hourly_rate values was loaded.
        if int(g_general_pars['hourly_rate_decrease_during_top_hours']) > 0 : # Is top hour rates adjustment in use?
            hr_rate_usage, hr_rate_temp_decrease, last_hr_rate_temp_decrease = get_temp_adj_top_hourly_rate()

        if g_general_pars['use_hourly_rates'] == "y" :
            hr_rate_usage, hr_rate_temp_decrease, last_hr_rate_temp_decrease = get_temp_adj_hourly_rate()

    return(hr_rate_usage, hr_rate_temp_decrease, last_hr_rate_temp_decrease)


def is_last_day_this_month() :
    today = datetime.now()
    tomorrow = today + timedelta(1)
    return(True)
    return ( today.month != tomorrow.month )


def create_monthly_rates() :
    dt = datetime.strftime(datetime.now(), "%Y-%m-%d_%H:%M:%S")
    if is_last_day_this_month() or (g_general_pars['create_monthly_rates_when'] == "d"):
        fi = Path(te["fi_monthly_rates"])
        cre_new = True
        if fi.is_file() :
            # Is the file from today?
            created = datetime.strftime(datetime.fromtimestamp(os.path.getctime(fi)), "%Y-%m-%d")
            if created == datetime.strftime(datetime.now(), "%Y-%m-%d") :
                cre_new = False

        if cre_new :
            cmd = "/usr/bin/python3 "+te["g_bin_dir"]+"/"+f0.get_exec_str(g_general_pars['external_pgm_create_monthly_rates']) \
                  +" -a "+g_general_pars['el_area']+" -l "+str(logreq)+" -m "+g_general_pars['max_log_len']
            if not f0.exec_external_pgm("monthly_rates", cmd) :
                txt = "create_monthly_rates:\n\tFailed to create:"+te["fi_monthly_rates"]+" monthly rates not working."
                f0.log_action(txt, False)
                f0.send_mail(dt+" "+txt)


def create_hourly_rates(exit_if_failure) :
    dt = datetime.strftime(datetime.now(), "%Y-%m-%d_%H:%M:%S")
    fi = Path(te["fi_hourly_rate"])
    if fi.is_file():
        return(True)

    # Not any file yet.
    if g_general_pars['pgm_create_hourly_rates'] != "," :
        pgm = g_general_pars['pgm_create_hourly_rates']
    else :
        f0.log_action("create_hourly_rates:\n\t"+g_ui_text["t30g"], False)
        f0.log_action("create_hourly_rates:\n\t"+g_ui_text["t30h"], True)

    el_area = g_general_pars['el_area']
    if not f0.exec_hourly_rate_pgm(pgm, el_area, logreq, g_general_pars['max_log_len']) :
        f0.log_action("create_hourly_rates:\n\t"+g_ui_text["t30h"], exit_if_failure)
        # A failure but the hourly rates are only used for statistics. No show stopper.
        txt ="create_hourly_rates:\n\t"+g_ui_text["t30i"]
        f0.log_action(txt, False)
        f0.send_mail(dt+" "+txt)
        return(False)

    return(True)


#### Main ######

dt = datetime.strftime(datetime.now(), "%Y-%m-%d_%H:%M:%S")
f0.log_action("", False)
f0.log_action("main: "+g_ui_text["t21"], False)

ret_stat, g_general_pars, g_weekday_indoor_temp_hours = f7.get_parameters()
if ret_stat != "ok" :
    f0.log_action("main: "+ret_stat, True)

g_verbose_logging = []
logs = g_general_pars['verbose_logging'].split(',')
for log in logs :
    g_verbose_logging.append(int(log))

f0.print_json_var(g_verbose_logging, 1, "general_pars", g_general_pars)
logreq = 0
if 6 in g_verbose_logging :
    logreq = 1

g_month_now = int(datetime.strftime(datetime.now(), "%m"))
g_hour_now = int(datetime.strftime(datetime.now(), "%H"))
g_week_day_nr = int(datetime.today().weekday() + 1)  # 0-6 => 1-7)
print("g_hour_now:", g_hour_now)

g_set_indoor_temp_months = []
mons = g_general_pars['set_indoor_temp_months'].split(',')
for mon in mons :
    g_set_indoor_temp_months.append(int(mon))

if g_week_day_nr == int(g_general_pars['rotate_log_files_this_weekday_nr']) :
    f0.rotate_log_files(int(g_general_pars["keep_nr_rotated_log_files"]))

hr_rates_decrease_active = False
if g_general_pars['use_hourly_rates'] == "y" or int(g_general_pars['hourly_rate_decrease_during_top_hours']) > 0 :
    if g_general_pars['external_pgm_create_hourly_rates'] != "," :
        fi = Path(te["fi_hourly_rate"])
        if not fi.is_file() :
           cmd = "/usr/bin/python3 "+te["g_bin_dir"]+"/"+f0.get_exec_str(g_general_pars['external_pgm_create_hourly_rates'])
           hr_rates_decrease_active = f0.exec_external_pgm("hourly_rates", cmd)
    else :
        hr_rates_decrease_active = create_hourly_rates(True)    # Must stop if the rates cannot be loaded.

else :
    if g_general_pars['create_hourly_rates'] == "y" :
        # Just to get the file with rates.
        create_hourly_rates(False)   # Do not stop if it failes to get them.

if g_general_pars['external_pgm_create_monthly_rates'] != "," :
    create_monthly_rates()

# Cleanup status files
if g_general_pars['use_hourly_rates'] == "y" :
    g_general_pars['hourly_rate_decrease_during_top_hours'] = 0         # Disable top_hours because hourly rates has priority.
else :
    remove_hourly_rate_setting("cleanup_not_active")

if int(g_general_pars['hourly_rate_decrease_during_top_hours'])== 0 :   # Top hour rates adjustment not in use.
    remove_top_rate_setting("cleanup_not_active")

if g_general_pars['use_windchill_compensation'] == "n" :
    remove_windchill_setting("cleanup_not_active")
    windchill_increase_active = False
else :
    windchill_increase_active = True
    windchill_use_smhi = True
    if g_general_pars['external_pgm_create_forecasts'] != "," :
        windchill_use_smhi = False

remove_obsolete_indoor_temp_setting()

# Set temp now.
if g_month_now in g_set_indoor_temp_months:
    g_weekday_active, g_hourly_settings_indoor_temp = create_hourly_settings_indoor_temp()
    set_new_indoor_temp()
else :
    f0.log_action("main: "+g_ui_text["t24"], False)

f0.log_action("main: "+g_ui_text["t25"], False)

exit()

