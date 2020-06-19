#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time
import RPi.GPIO as GPIO
import logging
from pythonping import ping
import itertools
from multiping import MultiPing
import socket
logging.basicConfig(level=logging.INFO)
sys.path.append('../')
from obswebsocket import obsws, events, requests  # noqa: E402

############## User Configuration ###############
port = 4444 #Should be 4444
password = "123456" #Change to a unique password.  Use the same password in OBS -> Tools -> Websockets Server Settings -> Password
trigger_char = "+" #If this character is found in the scene name then tally light will illuminate


############## Script ###############
ipAddressHistory = open("obsAddr.log","r")
host = ipAddressHistory.readline()
ipAddressHistory.close()

def scan_all_ip():
	ipRange = []
	for i in range(1,253):
	  ipRange.append("192.168.2."+str(i))
	  ipRange.append("192.168.1."+str(i))
	mp = MultiPing(ipRange)
	mp.send()
	responses, no_responses = mp.receive(1)
	for addr, rtt in responses.items():
		print ("%s responded in %f seconds" % (addr, rtt))
	return responses
	
	
def find_open_socket():
        responses = scan_all_ip()
        for addr, rtt in responses.items():
                if addr == host:
                    print ("Attempting to connect " + host)
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    result = sock.connect_ex((host,port))
                    sock.close
                    if result == 0:
                        return host
        for addr, rtt in responses.items():
            if connected == False:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                print ("Attempting to connect " + addr)
                result = sock.connect_ex((addr,port))
                sock.close
                if result == 0:
                    return addr
        return ""

def on_event(message):
    global connected
    print(u"Got message: {}".format(message))
    if format(message).find("SourceDestroyed event") > -1:
        connected = False


def on_switch(message):
    global LEDstate
    print(u"You changed the scene to {}".format(message.getSceneName()))
    if format(message.getSceneName()).find(trigger_char) > -1:
            GPIO.output(26, 1) #https://raspberrypi.stackexchange.com/questions/12966/what-is-the-difference-between-board-and-bcm-for-gpio-pin-numbering
            print("   LED ON")
            LEDstate = 1
    else:
            GPIO.output(26, 0)
            print("   LED OFF")
            LEDstate = 0

GPIO.setmode(GPIO.BCM)
GPIO.setup(16, GPIO.OUT)
GPIO.output(16, GPIO.HIGH)
connected = False
try:
    LEDstate = 0
    GPIO.setup(26, GPIO.OUT)
    while 1:
            addr = find_open_socket()
            if addr != "":
                    ws = obsws(addr, port, password)
                    ws.register(on_event)
                    ws.register(on_switch, events.SwitchScenes)
                    ws.connect()
                    message = ws.call(requests.GetCurrentScene())
                    sn = str(message)[str(message).find("name"):]
                    sn = sn[:sn.find(",")]
                    connected = True
                    ipAddressHistory = open("obsAddr.log","w")
                    ipAddressHistory.write(addr)
                    ipAddressHistory.close()
                    if sn.find(trigger_char) > -1:
                      GPIO.output(26, 1)
                      print("   LED ON")
                      LEDstate = 1
            while connected:
                GPIO.output(16, GPIO.LOW)
                time.sleep(0.98)
                GPIO.output(16, GPIO.HIGH)
                time.sleep(0.02)
                if LEDstate == 1:
                    GPIO.output(16, GPIO.LOW)
                    time.sleep(0.2)
                    GPIO.output(16, GPIO.HIGH)
                    time.sleep(0.02)
            try:
                GPIO.output(26, 0)
                ws.disconnect()
            except:
                pass
            time.sleep(2)

except KeyboardInterrupt:
    GPIO.output(26, 0)
    try:
      ws.disconnect()
    except:
      pass

GPIO.output(26, 0)
GPIO.cleanup()
