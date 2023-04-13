#!/usr/bin/python3
# This file is part of PGART_T (Pump Gradual Adjustment Room Temperature for Thermia Atlas).

# Copyright (C) 2023 PG Andersson <pg.andersson@gmail.com>.

# pgart_t is free software: you can redistribute it and/or modify it under the terms of GPL-3.0-or-later

# Functions to set the environment for pgart_t.

import json
import platform
import os
import glob
import requests

from pathlib import Path
from datetime import date,time,datetime,timedelta

import pgart_misc_func as f0

def get_url_thermia_api_azure_login() :
    thermia_api_config_url = "https://online-genesis.thermia.se/api/configuration"
    thermia_b2clogin_url = "https://thermialogin.b2clogin.com/thermialogin.onmicrosoft.com/b2c_1a_signuporsigninonline"
    thermia_login_redirect_uri = "https://online-genesis.thermia.se/login"
    thermia_client_id = "09ea4903-9e95-45fe-ae1f-e3b7d32fa385"
    thermia_scope = "09ea4903-9e95-45fe-ae1f-e3b7d32fa385"
    return(thermia_api_config_url, thermia_b2clogin_url, thermia_login_redirect_uri, thermia_client_id, thermia_scope)


def get_url_elbruk(el_area) :
    url_elbruk = {}
    url_elbruk["SE1"] = "https://www.elbruk.se/timpriser-se1-lulea#aktuella"
    url_elbruk["SE2"] = "https://www.elbruk.se/timpriser-se2-sundsvall#aktuella"
    url_elbruk["SE3"] = "https://www.elbruk.se/timpriser-se3-stockholm#aktuella"
    url_elbruk["SE4"] = "https://www.elbruk.se/timpriser-se4-malmo#aktuella"

    if el_area not in url_elbruk :
        f0.log_action("pgart_env_func.py get_url_elbruk:\n\t"+el_area+" unknown", True)

    return(url_elbruk[el_area])


def exit_if_el_area_missing(cty, el_area) :
    el_areas = {}

    if cty == "se" :
        el_areas = {"SE1":0, "SE2":1, "SE3":2, "SE4":3}

    if cty == "no" :
        el_areas = {'ost':0, 'sor':1, 'vest':2, 'midt':3, 'nord':4}

    if cty == "fi" :
        el_areas = {'finland':0}

    if el_area not in el_areas :
        f0.log_action("pgart_env_func.py exit_if_el_area_missing:\n\tcountry:"+cty+" el_area:"+el_area+" unknown", True)

    return(el_areas[el_area])


def get_url_minspotpris() :
    url_minspotpris = "https://minspotpris.no/detaljertstrompris/detaljert-beskrivelse-av-str%C3%B8mpris.html"
    return(url_minspotpris)


def get_url_herrforsnat() :
    url_herrforsnat = "https://www.herrforsnat.fi/sv/spotpriser/"
    return(url_herrforsnat)


def get_url_template_smhi() :
    url_template_smhi = "https://opendata-download-metfcst.smhi.se/api/category/pmp3g/version/2/geotype/point/lon/MY_LON/lat/MY_LAT/data.json"
    return(url_template_smhi)


def get_pgart_env() :
    pgart_env = {}
    g_os = platform.system()
    try:
        g_home = os.getenv("HOME")      #debian/ubuntu
    except :
        g_home = os.path.expanduser("~")    #windows

    g_pgart_dir=g_home+'/pgart'
    g_bin_dir=g_pgart_dir+'/bin'
    g_etc_dir=g_pgart_dir+'/etc'
    g_var_dir=g_pgart_dir+'/var'
    g_local_dir=g_var_dir+'/local'
    g_log_dir=g_var_dir+'/log'
    g_stat_dir=g_var_dir+'/stat'

    fi_action_log=g_log_dir+"/action.log"
    fi_hourly_run_log=g_log_dir+"/hourly_run.log"
    fi_run_summary_log=g_log_dir+"/summary_run.log"
    fi_run_summary_log_explanations=g_local_dir+"/explanations_summary_run_log.txt"
    fi_last_log_rotate=g_var_dir+"/last_log_rotate.txt"
    fi_monthly_rates=g_local_dir+"/monthly_rates.txt"
    dt = datetime.strftime(datetime.now(), "%Y%m%d")
    fi_hourly_rate=g_local_dir+"/hourly_rate_"+dt+".txt"
    fi_indoor_temp_reading=g_local_dir+"/indoor_temp_reading.txt"
    fi_eon_monthly_rates=g_local_dir+"/eon_monthly_rates.txt"
    fi_el_charges=g_stat_dir+"/el_charges.txt"
    fi_smhi_forecast=g_var_dir+"/smhi_forecast.txt"
    fi_forecast_short=g_var_dir+"/forecast_short.txt"
    fi_forecast_temp_wind=g_var_dir+"/windchill_calculations.txt"

    fi_par=g_etc_dir+"/pgart_control_heating.conf"
    fi_mail_params=g_etc_dir+"/pgart_mail_params.conf"
    fi_language=g_etc_dir+"/pgart_language.conf"
    fi_windchill_stats=g_log_dir+"/windchill_stats.log"
    fi_settings_status=g_var_dir+"/settings_status.txt"

    pgart_env["g_bin_dir"] = g_bin_dir
    pgart_env["g_pgart_dir"] = g_pgart_dir
    pgart_env["g_var_dir"] = g_var_dir
    pgart_env["g_local_dir"] = g_local_dir
    pgart_env["g_log_dir"] = g_log_dir
    pgart_env["g_stat_dir"] = g_stat_dir
    pgart_env["fi_action_log"] = fi_action_log
    pgart_env["fi_hourly_run_log"] = fi_hourly_run_log
    pgart_env["fi_run_summary_log"] = fi_run_summary_log
    pgart_env["fi_run_summary_log_explanations"] = fi_run_summary_log_explanations
    pgart_env["fi_last_log_rotate"] = fi_last_log_rotate
    pgart_env["fi_monthly_rates"] = fi_monthly_rates
    pgart_env["fi_hourly_rate"] = fi_hourly_rate
    pgart_env["fi_indoor_temp_reading"] = fi_indoor_temp_reading
    pgart_env["fi_el_charges"] = fi_el_charges
    pgart_env["fi_eon_monthly_rates"] = fi_eon_monthly_rates
    pgart_env["fi_smhi_forecast"] = fi_smhi_forecast
    pgart_env["fi_forecast_short"] = fi_forecast_short
    pgart_env["fi_forecast_temp_wind"] = fi_forecast_temp_wind
    pgart_env["fi_windchill_stats"] = fi_windchill_stats
    pgart_env["fi_settings_status"] = fi_settings_status
    pgart_env["fi_mail_params"] = fi_mail_params
    pgart_env["fi_language"] = fi_language
    pgart_env["fi_par"] = fi_par

    pgart_env["el_area_se"] = "SE1,SE2,SE3,SE4"
    pgart_env["el_area_fi"] = "finland"
    pgart_env["el_area_no"] = "ost,sor,vest,midt,nord"

    return(pgart_env)


def default_config_parameters():
    def_conf_pars = {}
    def_conf_pars["pump_access_method"] = "a"
    def_conf_pars["pump_ip_address"] = "0.0.0.0"
    def_conf_pars["login_id"] = "x"
    def_conf_pars["password"] = "y"
    def_conf_pars["set_indoor_temp_months"] = "01,02,03,04,05,09,10,11,12" # Not any temperature adjustment in the summertime.
    def_conf_pars["set_indoor_temp_hours"] = "20_15, 05_18, 06_20" # hour_degree. Decreas in the evening and increase in two steps in the morning.
    def_conf_pars["set_indoor_temp_weekday_1"] = "1 20_15, 05_18, 06_20" # Just to have something here.
    def_conf_pars["set_indoor_temp_weekday_2"] = "1 20_15, 05_18, 06_20"
    def_conf_pars["set_indoor_temp_weekday_3"] = "1 20_15, 05_18, 06_20"
    def_conf_pars["set_indoor_temp_weekday_4"] = "1 20_15, 05_18, 06_20"
    def_conf_pars["set_indoor_temp_weekday_5"] = "1 20_15, 05_18, 06_20"
    def_conf_pars["set_indoor_temp_weekday_6"] = "1 20_15, 05_18, 06_20"
    def_conf_pars["set_indoor_temp_weekday_7"] = "1 20_15, 05_18, 06_20"
    def_conf_pars["weekday"] = "0"
    def_conf_pars["use_windchill_compensation"] = "y"
    def_conf_pars["windchill_min_apparent_temp_diff"] = "3"
    def_conf_pars["windchill_lower_limit_apparent_temp"] = "-25"
    def_conf_pars["windchill_max_indoor_temp_increase"] = "4"
    def_conf_pars["windchill_use_forecast_this_nr_hours_ahead"] = "1"
    def_conf_pars["windchill_adjust_only_when_set_indoor_temp_is_above"] = "18"
    def_conf_pars["windchill_wind_force_factor"] = "1.0"
    def_conf_pars["my_lat"] = "56.789"  # Kattegatt
    def_conf_pars["my_lon"] = "12.34"
    def_conf_pars["external_pgm_create_forecasts"] = ","
    def_conf_pars["external_pgm_create_hourly_rates"] = ","
    def_conf_pars["external_pgm_create_monthly_rates"] = ","
    def_conf_pars["create_monthly_rates_when"] = "e"
    def_conf_pars["pgm_create_hourly_rates"] = ","
    def_conf_pars["external_pgm_read_indoor_sensor"] = ","
    def_conf_pars["el_area"] = "SE4"
    def_conf_pars["rotate_log_files_this_weekday_nr"] = "1"
    def_conf_pars["keep_nr_rotated_log_files"] = "10"
    def_conf_pars["verbose_logging"] = "0"
    def_conf_pars["max_log_len"] = "10000"
    def_conf_pars["use_hourly_rates"] = "n"
    def_conf_pars["create_hourly_rates"] = "n"
    def_conf_pars["read_external_indoor_sensor"] = "n"
    def_conf_pars["hourly_rate_decrease_hours"] = "07_20"
    def_conf_pars["hourly_rate_only_decrease_when_rate_above"] = "2.00"
    def_conf_pars["hourly_rate_only_decrease_for_this_nr_consecutive_hours"] = "2"
    def_conf_pars["hourly_rate_min_halt_after_decrease"] = "1"
    def_conf_pars["hourly_rate_decrease_nr_grades"] = "2"
    def_conf_pars["hourly_rate_decrease_during_top_hours"] = "0"
    def_conf_pars["mail_user"] = "none"
    def_conf_pars["gmail_app_pwd"] = "x"
    def_conf_pars["mail_subject"] = "pgart_t"

    return(def_conf_pars)


def valid_config_parameters():
    valid_conf_pars = {}
    valid_conf_pars["pump_access_method"] = "txt_single:a,m"
    valid_conf_pars["pump_ip_address"] = "ip:0.0.0.0"
    valid_conf_pars["login_id"] = "txt:1-30"
    valid_conf_pars["password"] = "txt:1-30"
    valid_conf_pars["set_indoor_temp_months"] = "int_range:1-12"
    valid_conf_pars["use_windchill_compensation"] = "txt_single:y,n"
    valid_conf_pars["windchill_min_apparent_temp_diff"] = "int_single:1-6"
    valid_conf_pars["windchill_lower_limit_apparent_temp"] = "-int_single:-20>-<-26"
    valid_conf_pars["windchill_max_indoor_temp_increase"] = "int_single:1-4"
    valid_conf_pars["windchill_use_forecast_this_nr_hours_ahead"] = "int_single:0-2"
    valid_conf_pars["windchill_adjust_only_when_set_indoor_temp_is_above"] = "int_single:15-22"
    valid_conf_pars["windchill_wind_force_factor"] = "float_single:0.5-1.5"
    valid_conf_pars["my_lat"] = "float_single:50.0-72.0"
    valid_conf_pars["my_lon"] = "float_single:5.0-31.0"
    valid_conf_pars["external_pgm_create_forecasts"] = "exec_path"
    valid_conf_pars["external_pgm_create_hourly_rates"] = "exec_path"
    valid_conf_pars["external_pgm_create_monthly_rates"] = "exec_path"
    valid_conf_pars["create_monthly_rates_when"] = "txt_single:d,e"
    valid_conf_pars["external_pgm_read_indoor_sensor"] = "exec_path"
    valid_conf_pars["pgm_create_hourly_rates"] = "txt:4-40"
    valid_conf_pars["el_area"] = "txt_single:SE1,SE2,SE3,SE4,ost,sor,vest,midt,nord,finland,*"
    valid_conf_pars["rotate_log_files_this_weekday_nr"] = "int_single:1-7"
    valid_conf_pars["keep_nr_rotated_log_files"] = "int_single:2-10"
    valid_conf_pars["verbose_logging"] = "int_range:0-6"
    valid_conf_pars["max_log_len"] = "int_range:1-10000000"
    valid_conf_pars["use_hourly_rates"] = "txt_single:y,n"
    valid_conf_pars["create_hourly_rates"] = "txt_single:y,n"
    valid_conf_pars["read_external_indoor_sensor"] = "txt_single:y,n"
    valid_conf_pars["hourly_rate_only_decrease_when_rate_above"] = "float_single:0.00-100.00"
    valid_conf_pars["hourly_rate_only_decrease_for_this_nr_consecutive_hours"] = "int_single:1-2"
    valid_conf_pars["hourly_rate_min_halt_after_decrease"] = "int_single:1-3"
    valid_conf_pars["hourly_rate_decrease_nr_grades"] = "int_single:1-5"
    valid_conf_pars["hourly_rate_decrease_during_top_hours"] = "int_single:0-24"
    valid_conf_pars["mail_user"] = "mailaddress"
    valid_conf_pars["gmail_app_pwd"] = "txt:16-16"
    valid_conf_pars["mail_subject"] = "txt:1-30"

    return(valid_conf_pars)


def get_windchill_evaluation_texts(lang_id):
    windchill_results = {}
    if lang_id == "en" :
        windchill_results["-4"] = "(-4) The current date-hour is not in the forecast file. Wrong time?"
        windchill_results["-2"] = "(-2) No contact with SMHI or response!=200."
        windchill_results["-1"] = "(-1) timeSeries is missing in the response from SMHI."
        windchill_results["1"] = "(1) Too low indoor temperature."
        windchill_results["2"] = "(2) The effect of the windchill is too small to request an increase of the indoor temperature."
        windchill_results["3"] = "(3) The temperature increase is acceptable."
        windchill_results["4"] = "(4) Reduced indoor temperature increase. It should have exceeded max_allowed_increase."
        windchill_results["5"] = "(5) Reduced indoor temperature increase. The supply line temperature would have been to high."
    else :
        windchill_results["-4"] = "(-4) Datorns aktuella tid finns inte i prognosfilen. Fel tid?"
        windchill_results["-3"] = "(-3) Externa prognosfilen saknas eller felaktigheter vid skapandet av den."
        windchill_results["-2"] = "(-2) Ingen kontakt med SMHI eller response!=200."
        windchill_results["-1"] = "(-1) Hittade inte timeSeries i svaret från SMHI."
        windchill_results["1"] = "(1) För låg inomhustemperatur."
        windchill_results["2"] = "(2) Vinden kyler inte nog för att motivera att temperaturen ska höjas inomhus."
        windchill_results["3"] = "(3) Temperaturhöjningen inom gränsvärdena."
        windchill_results["4"] = "(4) Begränsad höjning av börvärdet, skulle överskrida max_allowed_increase."
        windchill_results["5"] = "(5) Begränsad höjning av börvärdet, framledningstemperaturen skulle bli för hög."

    return(windchill_results)


def ui_texts(lang_id) :
    if lang_id == "en" :
        lang_ix = 1
    else :
        lang_ix = 0

    ui_text = {}

    ui_text["t1"] = \
    ["Börvärdet satt till",
    "Indoor temperature set to"]

    ui_text["t1a"] = \
    ["Börvärdet sänks med",
    "Indoor temperature will be decreased by"]

    ui_text["t1b"] = \
    ["Börvärdet ökas med",
    "The indoor temperature will be increased by:"]

    ui_text["t3"] = \
    ["Försöker igen med värden från förra körningen som misslyckades.",
    "Will rerun with the values from the previously failed run."]

    ui_text["t3a"] = \
    ["Veckodagens schema.",
    "The weekday schema."]

    ui_text["t3b"] = \
    ["Generella schemat.",
    "The common schema."]

    ui_text["t4a"] = \
    ["Schemalagd ändring.",
    "A scheduled change."]

    ui_text["t4b"] = \
    ["Ingen schemalagd ändring.",
    "No scheduled change."]

    ui_text["t4c"] = \
    ["Timpris tempåterställning.",
    "Temperature reset, hour-rate."]

    ui_text["t4d"] = \
    ["Vindkyle tempåterställning.",
    "Temperature reset, windchill."]

    ui_text["t4e"] = \
    ["Timpris tempsänkning.",
    "Temperature decrease, hour-rate."]

    ui_text["t4f"] = \
    ["Vindkyle temphöjning.",
    "Temperature increase, windchill."]

    ui_text["t4g"] = \
    ["Temperaturen manuellt satt.",
    "Temperature set manually."]

    ui_text["t5"] = \
    ["Konfigfilen saknas",
    "The configuration file is missing"]

    ui_text["t5a"] = \
    ["Konfigfilen för mail är tom. Felmeddelanden blir inte levererade",
    "The configuration file for the mail address is empty. Error message delivery inhibited"]

    ui_text["t6"] = \
    ["online-genesis, kunde inte hämta konfigurationen. Förmodligen nätverksfel.",
    "online-genesis, could not get the configuration. Network error."]

    ui_text["t7"] = \
    ["online-genesis, kunde inte hämta konfigurationen, response:",
    "online-genesis, could not get the configuration, response:"]

    ui_text["t8"] = \
    ["online-genesis, Azure authentication misslyckades. Förmodligen nätverksfel.",
    "online-genesis, Azure authentication failed. Network error."]

    ui_text["t8a"] = \
    ["online-genesis, Azure authentication misslyckades.",
    "online-genesis, Azure authentication failed."]

    ui_text["t8b"] = \
    ["online-genesis, Azure self_asserted misslyckades. Förmodligen nätverksfel.",
    "online-genesis, Azure self_asserted failed. Network error."]

    ui_text["t8c"] = \
    ["online-genesis, Azure misslyckades, fel login_id/password.",
    "online-genesis, Azure failed, error in login_id/password."]

    ui_text["t8d"] = \
    ["online-genesis, Azure misslyckades, Svaret saknar SETTINGS.",
    "online-genesis, Azure failed, the response has no SETTINGS."]

    ui_text["t8e"] = \
    ["online-genesis, Azure CombinedSigninAndSignup misslyckades.",
    "online-genesis, Azure CombinedSigninAndSignup failed."]

    ui_text["t8f"] = \
    ["online-genesis, Azure request token misslyckades, fel login_id/password.",
    "online-genesis, Azure request token failed, error in login_id/password."]

    ui_text["t10"] = \
    ["online-genesis, inloggad.",
    "online-genesis, Signed in."]

    ui_text["t11"] = \
    ["online-genesis, kunde inte hämta devices. Förmodligen nätverksfel.",
    "online-genesis, could not get the devices info. Network error."]

    ui_text["t12"] = \
    ["online-genesis, kunde inte hämta devices.",
    "online-genesis, could not get the devices info."]

    ui_text["t13"] = \
    ["online-genesis, kunde inte hämta status. Förmodligen nätverksfel.",
    "online-genesis, could not get the status. Network error."]

    ui_text["t14"] = \
    ["online-genesis, kunde inte hämta status.",
    "online-genesis, could not get the status."]

    ui_text["t15"] = \
    ["online-genesis, heatingEffectRegisters_index. Förmodligen nätverksfel.",
    "online-genesis, something wrong with heatingEffectRegisters_index. Network problem."]

    ui_text["t16"] = \
    ["online-genesis, fel med heatingEffectRegisters_index",
    "online-genesis, something wrong with heatingEffectRegisters_index"]

    ui_text["t17"] = \
    ["Natten börjar. Temperaturen skrivs över. Pumpens temp:",
    "The night starts. A forced temperature changed will be done. Pump temp:"]

    ui_text["t18"] = \
    ["Temperaturen ändras inte eftersom den är manuellt satt. Pumpens temp:",
    "The temperature is manually changed and will thus not be touched. Pump temp:"]

    ui_text["t18a"] = \
    ["Samma temperatur nu som förra gången. Pumpen uppdateras inte. Temp:",
    "The same temperature as last time. The pump will not be updated. Temp:"]

    ui_text["t18c"] = \
    ["senast satta:",
    "last value:"]

    ui_text["t18b"] = \
    ["Schemalagd temperatur:",
    "Scheduled temperature:"]

    ui_text["t18d"] = \
    ["Samma vindkylepåverkan nu som förra gången. Börvärdet blev då ökat med:",
    "The same windchill impact as the last time. The indoor temperature was then increased by:"]

    ui_text["t18e"] = \
    ["Bara skillnaden mellan aktuella och förra windchill_temp_incr justerar börvärdet:",
    "Only the difference between current and last windchill_temp_incr will be applied to the indoor temperature:"]

    ui_text["t18f"] = \
    ["windchill_temp_incr ökar börvärdet med:",
    "windchill_temp_incr will increase the indoor temperature by:"]

    ui_text["t19a"] = \
    ["Uppdateringen avslutad.",
    "The update finished."]

    ui_text["t19b"] = \
    ["borttagen",
    "removed"]

    ui_text["t19c"] = \
    ["Anledning",
    "Reason"]

    ui_text["t19d"] = \
    ["Temperaturen sänks inte. Paustimme i timprissänkningen.",
    "The temperature will not be decreased. Pause hour."]

    ui_text["t19e"] = \
    ["Temperaturen sänks inte. Inte dyrt nog denna timme.",
    "The temperature will not be decreased. The price is not high enough."]

    ui_text["t19f"] = \
    ["Timpriset",
    "Hourly-rate"]

    ui_text["t19g"] = \
    ["Börvärdet sänktes redan förra gången. Det blev då minskat med:",
    "The indoor temperature was already decreased at the last run. It was then decreased by:"]

    ui_text["t19h"] = \
    ["Bara skillnaden mellan aktuella och förra timprissänkningen justerar börvärdet:",
    "Only the difference between current and last hourly rate will be applied to the indoor temperature:"]

    ui_text["t19i"] = \
    ["Timprissänkningen sänker börvärdet med:",
    "The hourly rate will decrease the indoor temperature by:"]

    ui_text["t20"] = \
    ["Börvärdet satt till maxvärdet eftersom den beräknat nya temperaturen blev för hög",
    "The indoor temperature restricted to the maximum allowed value. The calculated temperature would have been too high"]

    ui_text["t21"] = \
    ["start.",
    "start."]

    ui_text["t22"] = \
    ["En misslyckad uppdatering finns",
    "A previous failure exists"]

    ui_text["t23"] = \
    ["Inget att reglera denna timme",
    "Nothing to change in this hour"]

    ui_text["t24"] = \
    ["Det är nog sommar. Ingen reglering alls",
    "Summertime. No adjustment at all"]

    ui_text["t25"] = \
    ["end.",
    "end."]

    ui_text["t26"] = \
    ["Kunde inte hämta utsikterna från SMHI. Förmodligen nätverksfel.",
    "Could not get the the forecasts from SMHI. Network problem."]

    ui_text["t27"] = \
    ["Kunde inte hämta utsikterna från SMHI.",
    "Could not get the the forecasts from SMHI."]

    ui_text["t28"] = \
    ["Hittade inte timeSeries i svaret från SMHI.",
    "Could not find timeSeries in the response from SMHI."]

    ui_text["t29"] = \
    ["Kunde inte hämta priserna från elbruk.se. Förmodligen nätverksfel.",
    "Failed to get prices from elbruk.se. Network problem."]

    ui_text["t29a"] = \
    ["Kunde inte hämta priserna från minspotpris.no. Förmodligen nätverksfel.",
    "Failed to get prices from minspotpris.no. Network problem."]

    ui_text["t29b"] = \
    ["Kunde inte hämta priserna från herrforsnat.fi. Förmodligen nätverksfel.",
    "Failed to get prices from herrforsnat.fi. Network problem."]

    ui_text["t29c"] = \
    ["Kunde inte hämta priserna från elprisetjustnu.se. Förmodligen nätverksfel.",
    "Failed to get prices from elprisetjustnu.se. Network problem."]

    ui_text["t30"] = \
    ["Kunde inte hämta priserna från elbruk.se.",
    "Failed to get prices from elbruk.se."]

    ui_text["t30a"] = \
    ["Kunde inte hämta priserna från minspotpris.no.",
    "Failed to get prices from minspotpris.no."]

    ui_text["t30b"] = \
    ["Kunde inte hämta priserna från herrforsnat.fi.",
    "Failed to get prices from herrforsnat.fi."]

    ui_text["t30c"] = \
    ["herrforsnat.fi har problem. Det går inte att hämta priserna.",
    "herrforsnat.fi has problems. Failed to get prices."]

    ui_text["t30e"] = \
    ["Kunde inte hämta priserna från elprisetjustnu.se.",
    "Failed to get prices from elprisetjustnu.se."]

    ui_text["t30f"] = \
    ["entsoe.eu har problem. Det går inte att hämta priserna.",
    "entsoe.eu has problems. Failed to get prices."]

    ui_text["t30g"] = \
    ["pgart_control_heating_se/en. pgm_create_hourly_rates saknas.",
    "pgart_control_heating_se/en. pgm_create_hourly_rates missing."]

    ui_text["t30h"] = \
    ["pgart_control_heating_se/en. Kunde inte skapa timpriserna.",
    "pgart_control_heating_se/en. Failed to create the hourly rates."]

    ui_text["t31"] = \
    ["Requestet är för stort för loggning:",
    "The request is too big to be logged:"]

    ui_text["tp1"] = \
    ["Fel format. Skall vara timme_gradtal t.ex 06_20",
    "Wrong format. Must be hour_temperature, like 06_20"]

    ui_text["tp1a"] = \
    ["Fel format. Skall vara timme-timme t.ex 08-15",
    "Wrong format. Must be hour-hour, like 08-15"]

    ui_text["tp2"] = \
    ["Timmen och graderna skall vara numeriska i timme_gradtal",
    "The hour and temperature must be numeric in hour-temperature"]

    ui_text["tp2a"] = \
    ["Timmarna skall vara numeriska i timme-timme",
    "The hours must be numerid in hour-hour"]

    ui_text["tp3"] = \
    ["Timmen skall vara 0-24",
    "the hour must be 1-24"]

    ui_text["tp3a"] = \
    ["Tid framåt, inte bakåt",
    "Time ahead, not backwards"]

    ui_text["tp3b"] = \
    ["Tiderna överlappar varandra",
    "Time spans overlap"]

    ui_text["tp3c"] = \
    ["Timmen finns redan",
    "The hour already set"]

    ui_text["tp4"] = \
    ["gradtalet skall vara 5-25",
    "The temperatur must be 1-25"]

    ui_text["tp5"] = \
    ["Parameterraden saknar =",
    "Missing = in the parameter line"]

    ui_text["tp5a"] = \
    ["Dubbla (,,) skiljetecken",
    "Duplicated (,,) delimiter"]

    ui_text["tp5b"] = \
    ["Felplacerat (,) skiljetecken",
    "Misplaced (,) delimiter"]

    ui_text["tp5c"] = \
    ["Data saknas efter =",
    "Empty after the ="]

    ui_text["tp5d"] = \
    ["Raden ska ha ett :",
    "Must have one :"]

    ui_text["tp5d1"] = \
    ["Raden ska ha ett ,",
    "Must have one ,"]

    ui_text["tp5d2"] = \
    ["Raden ska ha ett -",
    "Must have one -"]

    ui_text["tp5e"] = \
    ["Fel datum-timme format. Skall se ut som: 2023-01-17_20",
    "Wrong date-hour format. Should be like: 2023-01-17_20"]

    ui_text["tp5f"] = \
    ["Fel datum format. Skall se ut som: 2023-01-17",
    "Wrong date format. Should be like: 2023-01-17"]

    ui_text["tp5f1"] = \
    ["Fel datum format. Skall se ut som: 2023-01-17_14:02:01",
    "Wrong date format. Should be like: 2023-01-17_14:02:01"]

    ui_text["tp5g"] = \
    ["Fel temp vind format. Skall se ut som: 0.8,6.8",
    "Wrong temp wind format. Should be like: 0.8,6.8"]

    ui_text["tp5h"] = \
    ["Fel temp vind format. Skall vara tal med decimalpunkt, som: 0.8,6.8",
    "Wrong temp wind format. Should be numbers with a dot, like: 0.8,6.8"]

    ui_text["tp5i"] = \
    ["Fel format. Raden ska ha ett : och ett ;",
    "Wrong format. Must have one : and one ;"]

    ui_text["tp5j"] = \
    ["Fel format. Skall se ut som:",
    "Wrong format. Should be like: "]

    ui_text["tp6"] = \
    ["Veckodagen skall vara numerisk 1-7",
    "The weekday must be mnumeric 1-7"]

    ui_text["tp7"] = \
    ["Veckodagen skall vara 1-7",
    "The weekday must be 1-7"]

    ui_text["tp8"] = \
    ["set_temp_months skall vara 1-12",
    "set_temp_months must be 1-12"]

    ui_text["tp10"] = \
    ["är okänd. Felstavad?",
    "is unknown. Spelling?"]

    ui_text["tp11"] = \
    ["månaden skall vara numerisk",
    "The month must be numeric"]

    ui_text["tp12"] = \
    ["månaden skall vara 1-12",
    "The month must be 1-12"]

    ui_text["tp13"] = \
    ["Inte numeriskt",
    "Not numeric"]

    ui_text["tp14"] = \
    ["Giltiga värden",
    "Valid values"]

    ui_text["tp15"] = \
    ["Ogiltig IP adress",
    "Invalid IP address"]

    ui_text["tp17"] = \
    ["finns inte i",
    "missing in"]

    ui_text["tp18"] = \
    ["Sökvägen finns inte",
    "The path does not exist"]

    ui_text["tp19"] = \
    ["ogiltig emailadress",
    "invaled mail address"]

    ui_text["th1"] = \
    ["saknas. Ingen timpris styrning",
    " missing. Hourly rate control off"]

    ui_text["th2"] = \
    ["Timmen ska vara numerisk",
    "The hour must be numeric"]

    ui_text["th2b"] = \
    ["År och månad ska vara numeriska",
    "The year and month must be numeric"]

    ui_text["th3"] = \
    ["Timmen ska vara 0-23",
    "The hour must be 0-23"]

    ui_text["th3b"] = \
    ["Månaden ska vara 1-12",
    "The month must be 1-12"]

    ui_text["th4"] = \
    ["Fel format. Skall vara tal med decimalpunkt, som: 1.23",
    "Wrong format. Must be a number with a dot, like: 1.23"]

    ui_text["th5"] = \
    ["Det ska vara 24 timprisrader i filen.",
    "There shall be 24 hourly_rate lines in the file."]

    ui_text["th5b"] = \
    ["Det ska vara minst 1 rad i filen.",
    "There shall be at least 1 line in the file."]

    ui_text["td1"] = \
    ["Parametern finns mer än en gång: ",
    "The parameetr is a duplicate: "]

    ui = {}
    for x, y in ui_text.items():
        ui[x] = y[lang_ix]

    return(ui)

