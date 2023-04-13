#!/usr/bin/python3
# This file is part of PGART_T (Pump Gradual Adjustment Room Temperature for Thermia Atlas).

# Copyright (C) 2023 PG Andersson <pg.andersson@gmail.com>.

# pgart_t is free software: you can redistribute it and/or modify it under the terms of GPL-3.0-or-later

import platform
import os
import glob
from pathlib import Path

import pgart_env_func as f1

te = f1.get_pgart_env()

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
