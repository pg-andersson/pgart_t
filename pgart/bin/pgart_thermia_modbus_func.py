#!/usr/bin/python3
# This file is part of PGART_T (Pump Gradual Adjustment Room Temperature for Thermia Atlas).

# Copyright (C) 2023 PG Andersson <pg.andersson@gmail.com>.

# pgart_t is free software: you can redistribute it and/or modify it under the terms of GPL-3.0-or-later
#
# Functions to get the room-, indoor- and outdoor temperatures and to set the indoor temperature via TCP-Modbus.
#

from datetime import date,datetime,timedelta
import time
import socket
import struct

import pgart_misc_func as f0
import pgart_env_func as f1

# From Thermias' Modbus protocol for "Comfort wheel setting"
# Function 3, 6 (6=write)
# address 5 de facto address 40006 scale 100 Comfort wheel setting
# 40006  4: Read/Write Output or Holding Registers. 16-bits  (function, read: 0x03, write: 0x06)
# 0006 = represents a four digit address location in user data memory.Means address 5.
#
# Modbus tcp data packet layout.
# trans-id proto-id len  unit-id function address total_number_of_registers
# 0001     0000     0006  05      03       0005    0001


# From Thermias' Modbus protocol for "Outdoor temperature"
# Function 4
# address 13 de facto address 30014 scale 100
# 30014  4: Read or Holding Registers. 16-bits  (function, read: 0x03, write: 0x06)
# 0001     0000     0006  05      04       0013    0001

# 121 30122 10 Room temperature sensor


def exit_if_resp_invalid(bytes_rcvd) :
    """ From Acromag Technical Reference – Modbus
    In a normal response, the slave simply echoes the function code of the
    original query in the function field of the response. All function codes have
    their most-significant bit (msb) set to 0 (their values are below 80H). In an
    exception response, the slave sets the msb of the function code to 1 in the
    returned response (i.e. exactly 80H higher than normal) and returns the
    exception code in the data field.
    """
    ret_func = int.from_bytes(bytes_rcvd[7:8], "big")  # Function code is at byte pos 8
    if ret_func > 127 :
        info = "exit_if_resp_invalid:\n\texception response:"+str(ret_func)+" "+str(bytes_rcvd)
        f0.log_action(info, True)

    return(True)


def create_mbap_hdr() :
    h_trans_id =1
    h_proto_id = 0
    h_msg_len = 6
    b_device_address = 5
    mbap_hdr = struct.pack(">HHHB", h_trans_id, h_proto_id, h_msg_len, b_device_address)
    return(mbap_hdr)


def tcp_read_modbus_reg_temp(ip, logreq, b_func_code, h_reg_address, scale) :
    #Protocol Data Unit (PDU)
    h_number_of_regs = 1

    modbus_apu = create_mbap_hdr() + struct.pack(">BHH", b_func_code, h_reg_address, h_number_of_regs)
    rcv_len = 11
    bytes_rcvd = tcp_modbus_transaction(ip, modbus_apu, rcv_len, logreq, "Read")
    exit_if_resp_invalid(bytes_rcvd)

    t = int.from_bytes(bytes_rcvd[9:11], "big")     # The temp is in the last 2 bytes. As hundredths of degrees.
    if (t & 0x8000) == 0x8000 :
        t = -(65536 - t)
    t = round(t/scale)
    return(t)


def tcp_get_indoor_temperature(ip, logreq) :
    #Protocol Data Unit (PDU)
    b_func_code = 3
    h_reg_address = 5
    temp = tcp_read_modbus_reg_temp(ip, logreq, b_func_code, h_reg_address, 100)
    f0.log_action("tcp_get_indoor_temperature:\n\tstatus:ok. heating_effect:"+str(temp), False)
    return(temp)


def tcp_get_outdoor_temperature(ip, logreq) :
    #Protocol Data Unit (PDU)
    b_func_code = 4
    h_reg_address = 13
    temp = tcp_read_modbus_reg_temp(ip, logreq, b_func_code, h_reg_address, 100 )
    f0.log_action("tcp_get_outdoor_temperature:\n\tstatus:ok. outdoor_temp:"+str(temp), False)
    return(temp)


def tcp_get_room_sensor_temperature(ip, logreq) :
    #Protocol Data Unit (PDU)
    b_func_code = 4
    h_reg_address = 121
    temp = tcp_read_modbus_reg_temp(ip, logreq, b_func_code, h_reg_address, 10 )
    f0.log_action("tcp_get_room_sensor_temperature:\n\tstatus:ok. room_sensor_temp:"+str(temp), False)
    return(temp)


def tcp_set_indoor_temperature(ip, new_indoor_temp, logreq) :
    #Protocol Data Unit (PDU)
    b_func_code = 6
    h_reg_address = 5
    h_preset_data = new_indoor_temp * 100
    modbus_apu = create_mbap_hdr() + struct.pack(">BHH", b_func_code, h_reg_address, h_preset_data)
    rcv_len = 11
    bytes_rcvd = tcp_modbus_transaction(ip, modbus_apu, rcv_len, logreq, "Update")
    exit_if_resp_invalid(bytes_rcvd)

    f0.log_action("tcp_set_indoor_temperature:\n\tstatus:ok", False)
    return(new_indoor_temp)


def tcp_modbus_transaction(ip, modbus_apu, rcv_len, logreq, run_type) :
    if logreq == 1 :
        dt = datetime.strftime(datetime.now(), "%Y-%m-%d_%H:%M:%S")
        print("\n"+dt+" BEGIN: send "+run_type)
        print(ip)
        print(modbus_apu.hex())

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error as err:
        info = "tcp_modbus_transaction:\n\tsocket creation failed: "+ip+" %s" %(err)
        f0.log_action(info, True)

    try:
        s.connect((ip, 502))
    except socket.error as err:
        info = "tcp_modbus_transaction:\n\tConnect failed: "+ip+" %s" %(err)
        f0.log_action(info, True)

    nr_sent = 0
    nr_to_send = len(modbus_apu)
    while nr_sent < nr_to_send:
        sent = s.send(modbus_apu[nr_sent:])
        if sent == 0:
            info = "tcp_modbus_transaction:\n\tsocket connection broken: "+ip
            f0.log_action(info, True)

        nr_sent = nr_sent + sent

    if logreq == 1 :
        dt = datetime.strftime(datetime.now(), "%Y-%m-%d_%H:%M:%S")
        print("\n"+dt+" BEGIN: receive")

    msg_rcvd = []
    nr_rcvd = 0
    while nr_rcvd < rcv_len:
        rcvd = s.recv(min(rcv_len - nr_rcvd, 1024))
        if rcvd == b'':
            info = "tcp_modbus_transaction:\n\tsocket connection broken: "+ip
            f0.log_action(info, True)

        msg_rcvd.append(rcvd)
        nr_rcvd = nr_rcvd + len(rcvd)

    s.close()
    bytes_rcvd = b''.join(msg_rcvd)
    if logreq == 1:
        dt = datetime.strftime(datetime.now(), "%Y-%m-%d_%H:%M:%S")
        print(bytes_rcvd.hex())
        print(dt+" END: receive")

    return(bytes_rcvd)
