#!/usr/bin/python3
# This file is part of PGART_T (Pump Gradual Adjustment Room Temperature for Thermia Atlas).

# Copyright (C) 2023 PG Andersson <pg.andersson@gmail.com>.

# pgart_t is free software: you can redistribute it and/or modify it under the terms of GPL-3.0-or-later

# Functions to get and set indoor temperature via thermia-online-genesis.

# Many thanks to Krisjanis Lejejs for the API klejejs/python-thermia-online-api.
# The procedures for accessing Thermia-online are largely based on his work.


import sys
import platform
import os
import requests
import json
from pathlib import Path
from datetime import date,datetime,timedelta
import hashlib
import random
import base64

import pgart_misc_func as f0
import pgart_env_func as f1
import pgart_lang_func as f8

g_lang = f8.get_language()
g_ui_text = f1.ui_texts(g_lang)

thermia_api_config_url, thermia_b2clogin_url, thermia_login_redirect_uri, thermia_client_id, thermia_scope = f1.get_url_thermia_api_azure_login()

def parse_state_and_csrf(text):
    for line in text.splitlines():
        if line.startswith("var SETTINGS ="):
            settings = json.loads(line[15:-1])
            state_code = settings["transId"].split("=")[1]
            csrf_token = settings["csrf"]
            return state_code, csrf_token

    info = "parse_state_and_csrf:\n\t"+g_ui_text["t8d"]
    f0.log_action(info, True)


def auth_via_azure(login_id, password, logreq, max_log_len):
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    code_challenge = "".join(random.choice(chars) for _ in range(43))
    code_challenge_hash = str( base64.urlsafe_b64encode( hashlib.sha256( code_challenge.encode("utf-8") ).digest() ).rstrip(b"="), "utf-8" )

    try:
        request_auth = requests.get(
            thermia_b2clogin_url + "/oauth2/v2.0/authorize",
            params = {
                "client_id": thermia_client_id,
                "scope": thermia_scope,
                "redirect_uri": thermia_login_redirect_uri,
                "response_type": "code",
                "code_challenge": code_challenge_hash,
                "code_challenge_method": "S256",
            }
        )
    except requests.exceptions.ConnectionError:
        info = "request_auth:\n\t"+g_ui_text["t8"]
        f0.log_action(info, True)

    f0.log_request("request_auth", request_auth, logreq, max_log_len)

    if request_auth.status_code != 200:
        info = "request_auth:\n\t"+g_ui_text["t8a"]+", response:"+str(request_auth.status_code)+" "+str(request_auth.reason)
        f0.log_action(info, True)

    info = "request_auth:\n\tresponse:"+str(request_auth.status_code)+" size:"+str(len(request_auth.text))
    f0.log_action(info, False)

    state_code, csrf_token = parse_state_and_csrf(request_auth.text)
    info = "state_code:"+str(state_code)+" csrf_token:"+csrf_token
    #f0.log_action(info, False)

    try:
        request_self_asserted = requests.post(
            thermia_b2clogin_url + "/SelfAsserted",
            headers = {
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-Csrf-Token": csrf_token,
            },
            cookies = request_auth.cookies,
            data = {
                "request_type": "RESPONSE",
                "signInName": login_id,
                "password": password,
            },
            params = {
                "tx": "StateProperties=" + state_code,
                "p": "B2C_1A_SignUpOrSigninOnline",
            },
        )
    except requests.exceptions.ConnectionError:
        info = "request_self_asserted:\n\t"+g_ui_text["t8b"]
        f0.log_action(info, True)

    f0.log_request("request_self_asserted", request_self_asserted, logreq, max_log_len)

    if request_self_asserted.status_code != 200 or '{"status":"400"' in request_self_asserted.text:
        info = "request_self_asserted:\n\t"+g_ui_text["t8c"]+" Response:"+str(request_self_asserted.status_code)+" "+request_self_asserted.text
        f0.log_action(info, True)

    info = "request_self_asserted:\n\tresponse:"+str(request_self_asserted.status_code)+" size:"+str(len(request_self_asserted.text))
    f0.log_action(info, False)

    request_confirmed_cookies = request_self_asserted.cookies
    request_confirmed_cookies.set_cookie(
        requests.cookies.create_cookie( name="x-ms-cpim-csrf", value=request_auth.cookies.get("x-ms-cpim-csrf") )
    )
    info = "set_cookie request_confirmed_cookies:\n\tsize:"+str(len(request_auth.cookies.get("x-ms-cpim-csrf")))
    #q+" "+request_auth.cookies.get("x-ms-cpim-csrf")
    f0.log_action(info, False)

    try:
        request_confirmed = requests.get(
            thermia_b2clogin_url + "/api/CombinedSigninAndSignup/confirmed",
            cookies = request_confirmed_cookies,
            params = {
                "csrf_token": csrf_token,
                "tx": "StateProperties=" + state_code,
                "p": "B2C_1A_SignUpOrSigninOnline",
            },
        )
    except requests.exceptions.ConnectionError:
        info = "request_confirmed: "+g_ui_text["t8"]
        f0.log_action(info, True)

    f0.log_request("request_confirmed", request_confirmed, logreq, max_log_len)
    if request_confirmed.status_code != 200:
        info = "request_confirmed:\n\t"+g_ui_text["t8e"]+" Response:"+str(request_confirmed.status_code)+" "+request_confirmed.text
        f0.log_action(info, True)

    info = "request_confirmed:\n\tresponse:"+str(request_confirmed.status_code)+" size:"+str(len(request_confirmed.text))
    f0.log_action(info, False)

    try:
        request_token = requests.post(
            thermia_b2clogin_url + "/oauth2/v2.0/token",
            headers = {
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            },
            data = {
                "client_id": thermia_client_id,
                "redirect_uri": thermia_login_redirect_uri,
                "scope": thermia_scope,
                "code": request_confirmed.url.split("code=")[1],
                "code_verifier": code_challenge,
                "grant_type": "authorization_code",
            }
        )
    except requests.exceptions.ConnectionError:
        info = "request_token:\n\t"+g_ui_text["t8"]
        f0.log_action(info, True)

    f0.log_request("request_token", request_token, logreq, max_log_len)
    if request_token.status_code != 200:
        info = "request_token:\n\t"+g_ui_text["t8f"]+" Response:"+str(request_token.status_code)
        f0.log_action(info, True)

    info = "request_token:\n\tresponse:"+str(request_token.status_code)+" size:"+str(len(request_token.text))
    f0.log_action(info, False)

    authentication = json.loads(request_token.text)
    request_headers = {
        "Authorization": "Bearer " + authentication["access_token"],
        "Content-Type": "application/json",
    }

    return(request_headers)


def thermia_api_login(login_id, password, logreq, max_log_len):
    try:
        request_config = requests.get(thermia_api_config_url)
    except requests.exceptions.ConnectionError:
        info = "login_get_config:\n\t"+g_ui_text["t6"]
        f0.log_action(info, True)

    if request_config.status_code != 200:
        info = "login_get_config:\n\t"+g_ui_text["t7"]+" Response:"+str(request_config.status_code)
        f0.log_action(info, True)

    f0.log_request("request_config", request_config, logreq, max_log_len)
    info = "BEGIN login:\n\trequest_config. Response:"+str(request_config.status_code)+" json_len="+str(len(request_config.json()))
    f0.log_action(info, False)

    configuration = []
    configuration = request_config.json()
    request_headers = auth_via_azure(login_id, password, logreq, max_log_len)

    info = "END login:\n\tauth_via_azure"
    f0.log_action(info, False)
    info = "login-status:"+g_ui_text["t10"]
    return(info, configuration, request_headers)


def thermia_api_get_devices(configuration, request_headers, logreq, max_log_len):
    url = (configuration["apiBaseUrl"]+"/api/v1/InstallationsInfo/own")
    try:
        request = requests.get(url, headers=request_headers)
    except requests.exceptions.ConnectionError:
        info = "thermia_api_get_devices:\n\t"+g_ui_text["t11"]
        f0.log_action(info, True)

    if request.status_code != 200 :
        f0.log_action("thermia_api_get_devices:\n\t"+g_ui_text["t12"]+" Response:"+str(request.status_code), True)

    f0.log_request("thermia_api_get_devices", request, logreq, max_log_len)
    return request.json()


def thermia_api_get_device_info(configuration, request_headers, id, logreq, max_log_len):
    url = (configuration["apiBaseUrl"]+"/api/v1/installationstatus/"+str(id)+"/status")
    try:
        request = requests.get(url, headers=request_headers)
    except requests.exceptions.ConnectionError:
        info = "thermia_api_get_device_info: "+g_ui_text["t13"]
        f0.log_action(info, True)

    if request.status_code != 200:
        f0.log_action("thermia_api_get_device_info:\n\t"+g_ui_text["t14"]+" Response:"+str(request.status_code), True)

    f0.log_request("thermia_api_get_device_info", request, logreq, max_log_len)
    return request.json()


def thermia_api_set_indoor_temperature(request_headers, configuration, id, heatingEffectRegisters_index, temperature, logreq, max_log_len):
    url = (configuration["apiBaseUrl"]+"/api/v1/Registers/Installations/"+str(id)+"/Registers")
    new_temp = {
        "registerSpecificationId": heatingEffectRegisters_index,
        "registerValue": temperature,
        "clientUuid": "api-client-uuid",
    }
    try:
        request = requests.post(url, headers=request_headers, json=new_temp)
    except requests.exceptions.ConnectionError:
        info = "thermia_api_set_indoor_temperature:\n\t"+g_ui_text["t15"]
        f0.log_action(info, True)

    if request.status_code != 200:
        f0.log_action("thermia_api_set_indoor_temperature:\n\t"+g_ui_text["t16"]+":"+str(heatingEffectRegisters_index)+
                      ". Response:"+str(request.status_code), True)
    else :
        f0.log_action("thermia_api_set_indoor_temperature:\n\theatingEffectRegisters_index:"+str(heatingEffectRegisters_index)+
                      ". Response:"+str(request.status_code), False)

    f0.log_request("thermia_api_set_indoor_temperature:\n\t", request, logreq, max_log_len)
    return request.status_code
