#!/usr/bin/env python
# This file is part of PGART_T (Pump Gradual Adjustment Room Temperature for Thermia Atlas).

# Copyright (C) 2023 PG Andersson <pg.andersson@gmail.com>.

# pgart_t is free software: you can redistribute it and/or modify it under the terms of GPL-3.0-or-later

# Raspberry Pi and DS18B20 Temperature Sensor.
# https://www.circuitbasics.com/raspberry-pi-ds18b20-temperature-sensor-tutorial/
# The program reads the temperature and save it in a file.

import os
import glob
import time
from datetime import date,datetime,timedelta

import pgart_misc_func as f0
import pgart_env_func as f1
import pgart_lang_func as f8


base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

log = 1  #0=zero, 1=all

te = f1.get_pgart_env()

def list_env() :
    print(base_dir)
    print(device_folder)
    print(device_file)


def log_temp_reading(txt) :
    f = open(te["fi_indoor_temp_reading"], "w", encoding="utf8")
    f.write(txt+"\n")
    f.close()


def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines


def read_temp(log):
    i = 1
    sum_sec = 0
    device_file_not_two_lines = True
    while device_file_not_two_lines :
        lines = read_temp_raw()
        if len(lines) != 2 :
            if log > 0 :
                print("Device line 2 missing.")
        else :
            if lines[0].strip()[-3:] == 'YES' :
                # rad 0: 32 01 7f 80 7f ff 0e 10 91 : crc=91 YES

                if lines[1].find('t=') != -1 :
                    # rad 1: 32 01 7f 80 7f ff 0e 10 91 t=19125
                    t_s = lines[1].split("=")[1]        # Temp in 1/1000.
                    t = round(float(t_s)/1000.0, 1)
                    dt = datetime.strftime(datetime.now(), "%Y-%m-%d_%H:%M:%S")
                    if log > 0 :
                        print("read nr: "+str(i)+" nr_sec:"+str(sum_sec))
                        print(str(dt)+" ok "+str(t))

                    return(True, "ok", dt, t)

                else :
                    if log > 0 :
                        print("Device line 2 misses t= even after "+str(i)+" readings.")

            else :
                if log > 0  :
                    print("Device line missing YES even after "+str(i)+" readings")

        if i == 10 :
            msg = "Device lines not complete even after "+str(i)+" readings. Aborts now."
            if log > 0 :
                print(msg)
            return(False, msg, "", 0)

        time.sleep(0.5)  # Try again later.
        sum_sec += 0.5


list_env()
stat, msg, dt, t = read_temp(log)
if stat :
    log_temp_reading(dt+","+str(t))
else :
    log_temp_reading("Error: "+msg)

exit()
