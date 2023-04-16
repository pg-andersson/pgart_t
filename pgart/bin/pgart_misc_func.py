#!/usr/bin/python3
# This file is part of PGART_T (Pump Gradual Adjustment Room Temperature for Thermia Atlas).

# Copyright (C) 2023 PG Andersson <pg.andersson@gmail.com>.

# pgart_t is free software: you can redistribute it and/or modify it under the terms of GPL-3.0-or-later

# 2023 PG Andersson

import getopt
import sys
import platform
import os
import glob
import subprocess
import smtplib
import re
import time
import json

from email.mime.text import MIMEText
from pathlib import Path
from datetime import date,datetime,timedelta

import pgart_env_func as f1
import pgart_lang_func as f8

g_lang = f8.get_language()
g_ui_text = f1.ui_texts(g_lang)
te = f1.get_pgart_env()


def is_float(s) :
    try:
        float(s)
        return(True)
    except ValueError:
        return(False)


def exec_external_pgm(exec_type, exec_path) :
    # Uses os.system(). The calling program will thus not be aborted by a not catched error.
    fi_forecast = Path(te["fi_forecast_short"])
    fi_mon = Path(te["fi_monthly_rates"])
    fi_hr = Path(te["fi_hourly_rate"])
    fi_indoor_temp = Path(te["fi_indoor_temp_reading"])

    dt = datetime.strftime(datetime.now(), "%Y-%m-%d_%H:%M:%S")
    print(dt+" Begin: exec_external_pgm", exec_type)

    if exec_type == "hourly_rates" :
        if fi_hr.is_file():    # The file shall be recreated by the program
            print("Deleted existing: "+te["fi_hourly_rate"])
            os.remove(fi_hr)

    if exec_type == "monthly_rates" :
        if fi_mon.is_file():    # The file shall be recreated by the program
            print("Deleted existing: "+te["fi_monthly_rates"])
            os.remove(fi_mon)

    if exec_type == "forecast" :
        if fi_forecast.is_file():    # The file shall be recreated by the program
            print("Deleted existing: "+te["fi_forecast_short"])
            os.remove(fi_forecast)

    if exec_type == "temp_reading" :
        if fi_indoor_temp.is_file():    # The file shall be recreated by the program
            print("Deleted existing: "+te["fi_indoor_temp_reading"])
            os.remove(fi_indoor_temp)

    print(exec_path)
    sys.stdout.flush()
    status = os.system(exec_path)     # The calling program will continue even after a not catched error.

    dt = datetime.strftime(datetime.now(), "%Y-%m-%d_%H:%M:%S")
    print(dt+" End: exec_external_pgm", exec_type, status)

    # If the program succeeded there shall be a new file.
    if exec_type == "hourly_rates" :
        if fi_hr.is_file():
            created = datetime.fromtimestamp(os.path.getctime(fi_hr))
            log_action("exec_external_pgm:\n\tSuccess "+te["fi_hourly_rate"]+" created.", False)
            print(te["fi_hourly_rate"]+" created:"+str(created))
            status, info = is_hourly_rates_proper()
            if not status :
                fi = te["fi_hourly_rate"]
                new_fi = fi + ".bad"
                os_rename(fi, new_fi)
                log_action("exec_external_pgm hourly_rates:\n\t"+fi+" => "+new_fi, False)
                log_action("exec_external_pgm hourly_rates:\n\t"+g_ui_text["t30h"], False)
                return(False)

            return(True)
        else:
            print(te["fi_hourly_rate"]+" not created")
            log_action("exec_external_pgm:\n\tFailed to create:"+te["fi_hourly_rate"], False)
            return(False)

    if exec_type == "monthly_rates" :
        if fi_mon.is_file():
            created = datetime.fromtimestamp(os.path.getctime(fi_mon))
            log_action("exec_external_pgm:\n\tSuccess "+te["fi_monthly_rates"]+" created.", False)
            print(te["fi_monthly_rates"]+" created:"+str(created))
            status, info = is_monthly_rates_proper()
            if not status :
                fi = te["q"]
                new_fi = fi + ".bad"
                os_rename(fi, new_fi)
                log_action("exec_external_pgm monthly_rates:\n\t"+fi+" => "+new_fi, False)
                return(False)

            return(True)
        else:
            print(te["fi_monthly_rates"]+" not created")
            log_action("exec_external_pgm:\n\tFailed to create:"+te["fi_monthly_rates"], False)
            return(False)

    if exec_type == "forecast" :
        if fi_forecast.is_file():
            created = datetime.fromtimestamp(os.path.getctime(fi_forecast))
            log_action("exec_external_pgm:\n\tSuccess "+te["fi_forecast_short"]+" created.", False)
            print(te["fi_forecast_short"]+" created:"+str(created))
            status, info = is_forecast_short_proper()
            if not status :
                fi = te["fi_forecast_short"]
                new_fi = fi + ".bad"
                os_rename(fi, new_fi)
                log_action("exec_external_pgm fi_forecast_short:\n\t"+fi+" => "+new_fi, False)
                return(False)

            return(True)
        else:
            print(te["fi_forecast_short"]+" not created")
            log_action("exec_external_pgm:\n\tFailed to create:"+te["fi_forecast_short"], False)
            return(False)

    if exec_type == "temp_reading" :
        if fi_indoor_temp.is_file():
            created = datetime.fromtimestamp(os.path.getctime(fi_indoor_temp))
            log_action("exec_external_pgm:\n\tSuccess "+te["fi_indoor_temp_reading"]+" created.", False)
            print(te["fi_indoor_temp_reading"]+" created:"+str(created))
            status, info, dt, t = get_ext_temp_reading()
            if not status :
                print(info)
                return(False)

            return(True)
        else:
            print(te["fi_indoor_temp_reading"]+" not created")
            log_action("exec_external_pgm:\n\tFailed to create: "+te["fi_indoor_temp_reading"], False)
            return(False)


def exec_hourly_rate_pgm(pgm, el_area, logreq, max_log_len ) :
    cmd = "/usr/bin/python3 "+ te["g_bin_dir"]+"/"+pgm+" -a "+el_area+" -l "+str(logreq)+" -m "+str(max_log_len)
    if exec_external_pgm("hourly_rates", cmd) :
        return(True)

    return(False)


def is_hourly_rates_proper() :
    fi = Path(te["fi_hourly_rate"])
    if not fi.is_file():
        return(False, te["fi_hourly_rate"]+" missing.")

    f = open(te["fi_hourly_rate"], 'r' , encoding="utf8")
    nr_rec = 0
    for rec in f:
        nr_rec = nr_rec +1
        rec = rec.strip()
        rec = "".join(rec.split())
        if rec.count(":") != 1 :
            info = "is_hourly_rates_proper:\n\t"+te["fi_hourly_rate"]+". "+rec+". "+g_ui_text["tp5d"]
            log_action(info, False)
            return(False, info)

        buf = rec.split(":")     # Must be like 14:38.28
        hr = buf[0]
        if not hr.isnumeric() :
            info = "is_hourly_rates_proper:\n\t"+te["fi_hourly_rate"]+". "+rec+". "+g_ui_text["th2"]
            log_action(info, False)
            return(False, info)

        if not ((int(hr) < 24) and (int(hr) >= 0)) :
            info = "is_hourly_rates_proper:\n\t"+te["fi_hourly_rate"]+". "+rec+". "+g_ui_text["th3"]
            log_action(info, False)
            return(False, info)

        if not is_float(buf[1]) :
            info = "is_hourly_rates_proper:\n\t"+te["fi_hourly_rate"]+". "+rec+". "+g_ui_text["th4"]
            log_action(info, False)
            return(False, info)
    f.close()

    if nr_rec != 24 :
        info = "is_hourly_rates_proper:\n\t"+te["fi_hourly_rate"]+". nr_rec:"+str(nr_rec)+" "+g_ui_text["th5"]
        log_action(info, False)
        return(False, info)

    return(True, "")


def is_monthly_rates_proper() :
    fi = Path(te["fi_monthly_rates"])
    if not fi.is_file():
        return(False, te["fi_monthly_rates"]+" missing.")

    f = open(te["fi_monthly_rates"], 'r' , encoding="utf8")
    nr_rec = 0
    for rec in f:
        nr_rec = nr_rec +1
        rec = rec.strip()
        rec = "".join(rec.split())     # Must be like 2023-02:138.28
        if rec.count(":") != 1 :
            info = "is_monthly_rates_proper:\n\t"+te["fi_monthly_rates"]+". "+rec+". "+g_ui_text["tp5d"]
            log_action(info, False)
            return(False, info)

        if rec.count("-") != 1 :
            info = "is_monthly_rates_proper:\n\t"+te["fi_monthly_rates"]+". "+rec+". "+g_ui_text["tp5d2"]
            log_action(info, False)
            return(False, info)

        buf = rec.split(":")
        year, mon = buf[0].split("-")
        if not (year.isnumeric() and mon.isnumeric()) :
            info = "is_monthly_rates_proper:\n\t"+te["fi_monthly_rates"]+". "+rec+". "+g_ui_text["th2b"]
            log_action(info, False)
            return(False, info)

        if not ((int(mon) < 13) and (int(mon) > 0)) :
            info = "is_monthly_rates_proper:\n\t"+te["fi_monthly_rates"]+". "+rec+". "+g_ui_text["th3b"]
            log_action(info, False)
            return(False, info)

        if not is_float(buf[1]) :
            info = "is_monthly_rates_proper:\n\t"+te["fi_monthly_rates"]+". "+rec+". "+g_ui_text["th4"]
            log_action(info, False)
            return(False, info)
    f.close()

    if nr_rec < 1 :
        info = "is_monthly_rates_proper:\n\t"+te["fi_monthly_rates"]+". "+str(nr_rec)+" "+g_ui_text["th5b"]
        log_action(info, False)
        return(False, info)

    return(True, "")


def get_args_fi_cre_hourly_rates(pgm) :
    argv = sys.argv[1:]     # Bypass my own name
    options = "a:l:m:"
    long_options = ["area=", "logreq=", "maxlog="]

    if len(argv) == 0:
        if pgm == "pgart_get_hourly_rates_herrforsnat_fi.py" :
            return("finland", "0", "1000")   # Something

        if pgm == "pgart_get_hourly_rates_minspotpris_no.py" :
            return("ost", "0", "1000")

        if pgm == "pgart_get_monthly_rates_elbruk_se.py" :
            return("SE1", "0", "1000")

    if len(argv) == 6 :
        try:
            args, values = getopt.getopt(argv, options, long_options)
            for arg, val in args :
                if arg in ("-a", "--area") :
                    el_area = val
                elif arg in ("-l", "--logreq") :
                    logreq = val
                elif arg in ("-m", "--maxlog") :
                    max_log_len = val
        except getopt.error as err :
            print(str(err))
            exit()
    else :
        print("usage: "+pgm+" -a <area_id> -l <0|1>  -m <nr_bytes> or --area <area_id> --logreq <0|1>  --maxlog <nr_bytes>")
        exit()

    logreq = int(logreq)
    if logreq != 1 :
        logreq = 0

    return(el_area, logreq, max_log_len)


def get_args_forecasts_from_smhi() :
    argv = sys.argv[1:]     # Bypass my own name
    options = "lat:lon:wf:a:l:m:"
    long_options = ["lat=", "lon=", "windfact=", "logreq=", "maxlog="]

    if len(argv) == 0:
        return("56.789", "12.34", "1.0", "0", "1000")   # Kattegatt.

    if len(argv) == 10 :
        try:
            args, values = getopt.getopt(argv, options, long_options)
            for arg, val in args :
                if arg in ("-x", "--lat") :
                    my_lat = val
                elif arg in ("-y", "--lon") :
                    my_lon = val
                elif arg in ("-w", "--windfact") :
                    wind_force_factor = val
                elif arg in ("-l", "--logreq") :
                    logreq = val
                elif arg in ("-m", "--maxlog") :
                    max_log_len = val
        except getopt.error as err :
            print(str(err))
            exit()
    else :
        print("usage: pgart_get_smhi_forecasts.py -x <nr> -y <nr> -w <0.5-1.5> -l <0|1>  -m <nr_bytes> or --lat <nr> --lon <nr> --Windfact <0.5-1.5> --logreq <0|1> --maxlog <nr_bytes>")
        exit()

    logreq = int(logreq)
    if logreq != 1 :
        logreq = 0

    return(my_lat, my_lon, wind_force_factor, logreq, max_log_len)


def  get_exec_str(exec_args) :
    # pgm, arg1, arg2, arg3 ...
    exec_args = "".join(exec_args.split())
    buf = exec_args.split(",")
    exec_str = ""
    for b in buf :
        if exec_str == "" :
            exec_str = b
        else :
         exec_str = exec_str+" "+b

    return(exec_str)


def send_mail_via_gmail(mail_from, gmail_app_pwd, mail_to, mail_subject, mail_msg)  :
    # Send to a dedicated (not so serious) user-of-your-own and from there forward to your real user.
    # The "gmail_app_pwd" will be visible.
    # Google "Sign in using app passwords" to get more.
    try:
        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.starttls()
        s.login(mail_from, gmail_app_pwd)

        msg = MIMEText(mail_msg)
        msg['Subject'] = mail_subject

        s.sendmail(mail_from, mail_to, msg.as_string())
        s.quit()
    except :
        return(False)

    return(True)


def log_request(func, req, logreq, max_log_len) :
    if logreq == 0 :
        return()

    dt = datetime.strftime(datetime.now(), "%Y-%m-%d_%H:%M:%S")
    print("\n"+dt+" BEGIN: "+func)
    print("\nreq.request")
    print(req.request)
    print("\nreq.request.url")
    print(req.request.url)
    print("\nreq.request.headers")
    print(req.request.headers)
    if len(req.text) > int(max_log_len) :
        print("\n"+g_ui_text["t31"]+str(len(req.text))+" max:"+str(max_log_len))
    else :
        print("\nreq.request.body")
        print(req.request.body)
        print("\nreq.content")
        print(req.content)

    print("\n"+dt+" END: "+func)
    print("\n")


def print_json_var(verbose_logging, verbose_nr, var, json_var) :
    if verbose_nr in verbose_logging :
        json_formatted_str = json.dumps(json_var, indent=4)
        print(var)
        print(json_formatted_str)


def get_hourly_rates(fi_hourly_rate):
    hr_rates = {}

    fi = Path(fi_hourly_rate)
    if fi.is_file():
        f = open(fi_hourly_rate, 'r' , encoding="utf8")
        for rec in f:
            rec = rec.strip()
            s = rec.split(":")     # 14:38.28
            hr_rates.update({int(s[0]): float(s[1])})

        f.close()
    return(hr_rates)


def print_hourly_rates() :
    hr_rates = get_hourly_rates(te["fi_hourly_rate"])
    print(json.dumps(hr_rates, indent=4))


def get_monthly_rates(fi_monthly_rates):
    hr_rates = {}

    fi = Path(fi_monthly_rates)
    if fi.is_file():
        f = open(fi_monthly_rates, 'r' , encoding="utf8")
        for rec in f:
            rec = rec.strip()
            s = rec.split(":")     # 2023-03:57.22
            hr_rates.update({s[0]: float(s[1])})

        f.close()
    return(hr_rates)


def print_monthly_rates() :
    hr_rates = get_monthly_rates(te["fi_monthly_rates"])
    print(json.dumps(hr_rates, indent=4))


def get_forecast_short() :
    forecast_short = {}

    filepath = Path(te["fi_forecast_short"])
    if filepath.is_file():
        f = open(te["fi_forecast_short"], "r", encoding="utf8")
        for rec in f:
            rec = rec.strip()
            s = rec.split(":", 1)
            forecast_short.update({s[0]: s[1]})

        f.close()
    return(forecast_short)


def is_forecast_short_proper() :
    fi = Path(te["fi_forecast_short"])
    if not fi.is_file():
        return(False, te["fi_forecast_short"]+" missing.")

    f = open(te["fi_forecast_short"], "r", encoding="utf8")
    for rec in f:
        rec = rec.strip()
        rec = "".join(rec.split())
        # Check the format. 2023-01-17_20:0.8,6.8
        if rec.count(":") != 1 :
            info = "is_forecast_short_proper:\n\t"+te["fi_forecast_short"]+". "+rec+". "+g_ui_text["tp5d"]
            log_action(info, False)
            return(False, info)

        if rec.count(",") != 1 :
            info = "is_forecast_short_proper:\n\t"+te["fi_forecast_short"]+". "+rec+". "+g_ui_text["tp5d1"]
            log_action(info, False)
            return(False, info)

        buf = rec.split(":", 1)
        dt_hr = buf[0]
        if len(dt_hr) != 13 :
            info = "is_forecast_short_proper:\n\t"+te["fi_forecast_short"]+". "+rec+". "+g_ui_text["tp5e"]
            log_action(info, False)
            return(False, info)

        if dt_hr[10] != "_" or dt_hr[4] != "-" or dt_hr[7] != "-" :
            info = "is_forecast_short_proper:\n\t"+te["fi_forecast_short"]+". "+rec+". "+g_ui_text["tp5e"]
            log_action(info, False)
            return(False, info)

        # Valid date, hr?
        d = dt_hr.split("_")
        try:
            res = bool(datetime.strptime(d[0], "%Y-%m-%d"))
        except ValueError:
            info = "is_forecast_short_proper:\n\t"+te["fi_forecast_short"]+". "+rec+". "+g_ui_text["tp5f"]
            log_action(info, False)
            return(False, info)

        if not d[1].isnumeric() :
            info = "is_forecast_short_proper:\n\t"+te["fi_forecast_short"]+". "+rec+". "+g_ui_text["th2"]
            log_action(info, False)
            return(False, info)

        if not ((int(d[1]) < 24) and (int(d[1]) >= 0)) :
            info = "is_forecast_short_proper:\n\t"+te["fi_forecast_short"]+". "+rec+". "+g_ui_text["th3"]
            log_action(info, False)
            return(False, info)

        val = buf[1]
        buf = val.split(",")
        if len(buf) != 2 :
            info = "is_forecast_short_proper:\n\t"+te["fi_forecast_short"]+". "+rec+". "+g_ui_text["tp5g"]
            log_action(info, False)
            return(False, info)

        if not (is_float(buf[0]) and is_float(buf[1])) :
            info = "is_forecast_short_proper:\n\t"+te["fi_forecast_short"]+". "+rec+". "+g_ui_text["tp5h"]
            log_action(info, False)
            return(False, info)

    f.close()
    return(True, "")


def print_forecast_short() :
    json_smhi_short = get_forecast_short()
    print(json.dumps(json_smhi_short, indent=4))


def get_ext_temp_reading() :
    filepath = Path(te["fi_indoor_temp_reading"])
    if filepath.is_file():
        f = open(te["fi_indoor_temp_reading"], "r", encoding="utf8")
        for rec in f:
            rec = rec.strip()
            rec = "".join(rec.split())
            # Check the format. 2023-01-17_20:02:01,20.4
            if rec.count(",") != 1 :
                info = "get_ext_temp_reading:\n\t"+te["fi_indoor_temp_reading"]+". "+rec+". "+g_ui_text["tp5d1"]
                log_action(info, False)
                return(False, info, 0, 0)

            buf = rec.split(",", 1)
            # Valid date?
            try:
                res = bool(datetime.strptime(buf[0], "%Y-%m-%d_%H:%M:%S"))
            except ValueError:
                info = "get_ext_temp_reading:\n\t"+te["fi_indoor_temp_reading"]+". "+rec+". "+g_ui_text["tp5f1"]
                log_action(info, False)
                return(False, info, 0, 0)

            if not is_float(buf[1]) :
                info = "get_ext_temp_reading:\n\t"+te["fi_indoor_temp_reading"]+". "+rec+". "+g_ui_text["th4"]
                log_action(info, False)
                return(False, info, 0, 0)
        f.close()
    else :
        return(False, "No file", 0, 0)

    return(True, "ok", buf[0], buf[1])


def get_language() :
    filepath = Path(te["fi_language"])
    if filepath.is_file():
        f = open(te["fi_language"], "r", encoding="utf8")
        for rec in f:
            rec = rec.strip()
            if rec == "":
                continue

            if rec.find("#", 0 , 1) == 0:
                continue

            rec = rec.strip()
            if rec == "se" or rec == "en" :
                return(rec)
            return("se")


def is_mailaddress_valid(address):
    if address == "none" :
        return(True)

    valid_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if re.fullmatch(valid_pattern, address) :
        return(True)

    return(False)


def get_mail_params() :
    # Get the mail parameters from the config file.
    l_general_pars = f1.default_config_parameters()
    valid_par = f1.valid_config_parameters()
    mail_pars = {}
    filepath = Path(te["fi_mail_params"])
    if filepath.is_file():              # Send a mail.
        f = open(te["fi_mail_params"], "r", encoding="utf8")
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
                print(te["fi_mail_params"]+" "+rec+" "+g_ui_text["tp5"])
                exit()

            buf = rec.split("=", 1)
            par = buf[0].replace(' ', '')
            val = buf[1].strip()
            if not (par in l_general_pars) :
                print(te["fi_mail_params"]+" "+par+" "+val+" "+g_ui_text["tp10"])
                exit()

            valid_pars = valid_par[par].split(':')
            if valid_pars[0] == "txt" :
                ir = valid_pars[1].split('-')
                val = val.replace(' ', '')
                if ((len(val) < int(ir[0])) or (len(val) > int(ir[1]))) :
                    print(par+": "+val+" "+g_ui_text["tp14"]+": "+valid_pars[1])
                    exit()

            elif valid_pars[0] == "mailaddress" :
                if val != "none" :
                    valid_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                    if not re.fullmatch(valid_pattern, val) :
                        print(par+": "+val+" "+g_ui_text["tp19"])
                        exit()

            mail_pars.update({par: str(val)})
        f.close()

        if len(mail_pars) == 0 :
            print("get_mail_params:"+te["fi_mail_params"]+" "+g_ui_text["t5a"])

        return(mail_pars)
    else:
        print(te["fi_mail_params"]+" "+g_ui_text["t5"])
        exit()


def send_mail(msg) :
    mail_pars = get_mail_params()
    if len(mail_pars) > 0 :
        if mail_pars["mail_user"] != "none" :
            if not send_mail_via_gmail(
                    mail_pars["mail_user"], mail_pars["gmail_app_pwd"],
                    mail_pars["mail_user"], mail_pars["mail_subject"],
                    msg) :
                log_action_1("send_mail_via_gmail:\n\tfailed. "+mail_pars["mail_user"]+" "+mail_pars["mail_subject"])

            log_action_1("send_mail_via_gmail:\n\tok. "+mail_pars["mail_user"]+" "+mail_pars["mail_subject"])


def log_action_1(txt) :
    dt = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
    f = open(te["fi_action_log"] , "a", encoding="utf8")
    if txt == "" :
        f.write("- - - - - - - - - - - - - - - - - - - - \n")
    else :
        f.write(dt+" "+txt+"\n\n")

    f.close()


def log_action(txt, exit_now) :
    if exit_now :
        txt += " Forced exit."

    log_action_1(txt)

    if exit_now :
        dt = datetime.strftime(datetime.now(), "%Y-%m-%d_%H:%M:%S")
        print(dt+" "+txt)
        send_mail(dt+" "+txt)
        log_action_1("Aborted.")
        exit()


def os_rename(fi, new_fi) :
    fo = Path(fi)
    fn = Path(new_fi)
    os.rename(fo, fn)


def rename_files_to_increased_appendix_nr(fi_current, keep_nr_versions) :
    # Keep some files. fi_current fi_current.1 fi_current.2 ...
    fi_parts = fi_current.split(".")   #Get the last part of the current file.
    fi_current_extension = fi_parts[len(fi_parts) - 1]

    fi_names = []
    for fi in glob.glob(fi_current+'*') :   # get all such files.
        fi_names.append(fi)

    #Rename the files to a higher index
    fi_names.sort(reverse=True)
    for fi in fi_names :
        if fi.endswith('.'+fi_current_extension) :  # The last file now. The one without an index. Rename it to index 1
            new_fi =  fi + ".1"
            os_rename(fi, new_fi)
        else:                                       # Shift up one step or delete.
            fi_parts = fi.split(".")
            ix = fi_parts[len(fi_parts) - 1]
            if not ix.isdigit() :
                continue

            if int(ix) >= keep_nr_versions :        # Just keep keep_nr_versions files.
                fi = Path(fi)
                os.remove(fi)
            else :
                ix_ind = fi.rfind(ix)
                new_fi =  fi[0:ix_ind] + str(int(ix) + 1)   # Increase the index.
                os_rename(fi, new_fi)


def rotate_log_files(keep_nr_rotated_log_files) :
    last_dt = "-"
    dt_now = datetime.strftime(datetime.now(), "%Y-%m-%d")
    fi = Path(te["fi_last_log_rotate"])
    if fi.is_file():
        f = open(te["fi_last_log_rotate"], 'r' , encoding="utf8")
        last_dt = f.readline().strip()
        f.close()

    if last_dt != dt_now :
        rename_files_to_increased_appendix_nr(te["fi_windchill_stats"], keep_nr_rotated_log_files)
        rename_files_to_increased_appendix_nr(te["fi_action_log"], keep_nr_rotated_log_files)
        rename_files_to_increased_appendix_nr(te["fi_hourly_run_log"], keep_nr_rotated_log_files)
        rename_files_to_increased_appendix_nr(te["fi_run_summary_log"], keep_nr_rotated_log_files)

        f = open(te["fi_last_log_rotate"], "w", encoding="utf8")
        f.write(dt_now+"\n")
        f.close()
