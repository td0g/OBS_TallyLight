#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Written by Tyler Gerritsen
#td0g.ca

#Changelog
#1.0    2020-05-
#   Initial Commit
#1.1    2020-06-27
#   Event logs
#   More preference for last good IP
#   Multi-Ping error catching (would occasionally have an exception)
#1.2	2020-08-14
#	If no communication has occurred in the past 30 seconds, pings to make sure connection still exists
#	If no connection, resets WiFi


#ToDo
#	MultiPing seems to miss some PC's occasionally
#	Fade to black transition will turn on Tally Light if a scene with the trigger char is loaded in preview

import sys
import time
import RPi.GPIO as GPIO
import logging
from pythonping import ping
import itertools
from multiping import MultiPing
import socket
import os

  #Comment out all but one of the following logFileNames.  The first will put all logs into a single file.  The second will create a new logfile for each day.
#logFileName = '/home/pi/tally.log'
logFileName = '/home/pi/tally_'+str(time.strftime("%Y-%m-%d"))+'.log'

  #Set the GPIO Pins
tallyLightGPIO = 13
statusLightGPIO = 16

  #Set the trigger character
triggerChar = '+'

  #Set the number of seconds of no ping response before resetting
resetSeconds = 120 #Minimum 40 seconds

  #Initialize logging
logging.basicConfig(filename=logFileName,level=logging.DEBUG, format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',  datefmt='%y-%m-%d %H:%M:%S %Z')
logging.debug('Tally Light BOOTED')
print("Logging to: " + logFileName)

  #Not sure what this does...
sys.path.append('../')
from obswebsocket import obsws, events, requests  # noqa: E402

  #Set the websocket port (Should be 4444) and password (set in OBS Studio)
port = 4444
password = "123456"

  #Try load last good IP address
lastKnownOBSStudioIP = ""
try:
    logging.debug('Opening obsAddr.log')
    ipAddressHistory = open("obsAddr.log","r")
    logging.debug('Reading last known OBS Studio IP Address')
    lastKnownOBSStudioIP = ipAddressHistory.readline()
    logging.debug('Last known OBS Studio IP: ' + lastKnownOBSStudioIP)
    ipAddressHistory.close()
except:
	logging.debug('Could not load last good IP')

#Keep track of last communication time
lastCommunicationTime = time.time()

#Shutdown and restart WiFi
def resetWiFi():
    logging.debug("Shutting down WiFi")
    print("Shutting down WiFi")
    cmd = 'ifconfig wlan0 down'
    os.system(cmd)
    print("Bringing up WiFi in 5")
    time.sleep(1)
    print("4")
    time.sleep(1)
    print("3")
    time.sleep(1)
    print("2")
    time.sleep(1)
    print("1")
    time.sleep(1)
    print("Now!")
    logging.debug("Bringing up WiFi")
    cmd = 'ifconfig wlan0 up'
    os.system(cmd)
    time.sleep(5)

#Returns tuple of available IP addresses
def scan_all_ip():
  ipRange = []
  logging.debug("Pinging all IP addresses")
  for i in range(1,253):
    ipRange.append("192.168.2."+str(i))
    ipRange.append("192.168.1."+str(i))
  mp = MultiPing(ipRange)
  try:
    mp.send()
    responses, no_responses = mp.receive(2)
  except:
    logging.debug("Failure to ping addresses")
    print("Failure to ping addresses")
    return ""
  for addr, rtt in responses.items():
  	logging.debug ("%s responded in %f seconds" % (addr, rtt))
  return responses
  
def pingHost(ipToPing):
  p = []
  p.append(ipToPing)
  mp = MultiPing(p)
  try:
    mp.send()
    responses, no_responses = mp.receive(2)
  except:
    logging.debug("Ping " + ipToPing + " Failure - Unable To Ping")
    print("Ping " + ipToPing + " Failure - Unable To Ping")
    return False
  if ipToPing in responses:
    logging.debug("Ping " + ipToPing + " Successful")
    print("Ping " + ipToPing + " Successful")
    return True
    logging.debug("Ping " + ipToPing + ": No Response")
    print("Ping " + ipToPing + ": No Response")
  return False
	
#Returns IP of OBS Studio (or "" if OBS Studio not found
def find_open_socket():
  global lastCommunicationTime
  prefferedIP = ""
  responses = scan_all_ip()	  
  if responses != "":
    for addr, rtt in responses.items():
      if str(addr) == lastKnownOBSStudioIP:
        prefferedIP = addr
        print("Preffered IP loaded: " + lastKnownOBSStudioIP + " " + str(addr))
    for addr, rtt in responses.items():
      if connected == False:
        if prefferedIP != "":
          print("Attempting to connect to " + prefferedIP + "(last known IP of OBS Studio)")
          logging.debug ("Attempting to connect " + prefferedIP + "(last known IP of OBS Studio)")
          sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
          result = sock.connect_ex((prefferedIP,port))
          sock.close
          if result == 0:
            logging.debug("OBS Studio Websocket Found!")
            print("OBS Studio Websocket Found!")
            return prefferedIP
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("Attempting to connect to " + addr)
        logging.debug ("Attempting to connect to " + addr)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((addr,port))
        sock.close
        if result == 0:
          logging.debug("OBS Studio Websocket Found!")
          print("OBS Studio Websocket Found!")
          lastCommunicationTime = time.time()
          return addr
  return ""

#Function called if any Websocket Message rec'd
def on_event(message):
  global connected, lastCommunicationTime
  logging.debug(u"Got message: {}".format(message))
  print(u"Got message: {}".format(message))
  if format(message).find("SourceDestroyed event") > -1:
    connected = False
  else:
    lastCommunicationTime = time.time()

#Function called if scene changed
def on_switch(message):
  global LEDstate, lastCommunicationTime
  logging.debug(u"Scene Changed To {}".format(message.getSceneName()))
  lastCommunicationTime = time.time()
  if format(message.getSceneName()).find(triggerChar) > -1:
    GPIO.output(tallyLightGPIO, 1)
    logging.debug("LED ON")
    print("LED ON")
    LEDstate = 1
  else:
    GPIO.output(tallyLightGPIO, 0)
    logging.debug("LED OFF")
    print("LED OFF")
    LEDstate = 0

#Parses scene name from websocket message
def getSceneName(message):
    sn = str(message)[str(message).find("name"):]
    sn = sn[:sn.find(",")]
    return sn

#Saves IP address to file for next time
def saveGoodIP(addr):
  logging.debug("Saved new OBS Studio IP: " + str(addr))
  ipAddressHistory = open("obsAddr.log","w+")
  ipAddressHistory.write(addr)
  ipAddressHistory.close()


#Setup GPIO pins
GPIO.setmode(GPIO.BCM)
GPIO.setup(statusLightGPIO, GPIO.OUT)
GPIO.output(statusLightGPIO, GPIO.HIGH)

#Begin attempting to find and connect to OBS Studio
connected = False
try:
    LEDstate = 0
    GPIO.setup(tallyLightGPIO, GPIO.OUT)
    while 1:
            addr = find_open_socket()	#Get the address of OBS Studio
            if addr != "":	#If OBS Studio found
                    ws = obsws(addr, port, password)
                    ws.register(on_event)
                    ws.register(on_switch, events.SwitchScenes)
                    try:
                      ws.connect()
                      message = ws.call(requests.GetCurrentScene())
                      lastCommunicationTime = time.time()
                      currentSceneName = getSceneName(message)
                      logging.debug("Current Scene Name: " + currentSceneName)
                      print("Current Scene Name: " + currentSceneName)
                      connected = True
                      saveGoodIP(addr)
                      if currentSceneName.find(triggerChar) > -1:
                        GPIO.output(tallyLightGPIO, 1)
                        logging.debug("LED ON")
                        print("LED ON")
                        LEDstate = 1
                    except:
                      logging.debug("Connection Refused")
                      print("Connection Refused")

            while connected:	#blink status LED once for connected, twice for connected and Tally Light ON
                if lastCommunicationTime + 30 < time.time():
                  logging.debug("Haven't heard from OBS in a while... Pinging!")
                  print("Haven't heard from OBS in a while... Pinging!")
                  if pingHost(addr):
                    lastCommunicationTime = time.time()
                  else:
                    time.sleep(2)
                    if lastCommunicationTime + resetSeconds < time.time():
					
                      logging.debug("TIMEOUT!!!")
                      print("TIMEOUT!!!")
                      resetWiFi()
                      connected = False
                GPIO.output(statusLightGPIO, GPIO.LOW)
                time.sleep(0.98)
                GPIO.output(statusLightGPIO, GPIO.HIGH)
                time.sleep(0.02)
                if lastCommunicationTime + 60 < time.time():
                    GPIO.output(statusLightGPIO, GPIO.LOW)
                    time.sleep(0.2)
                    GPIO.output(statusLightGPIO, GPIO.HIGH)
                    time.sleep(0.02)
                    GPIO.output(statusLightGPIO, GPIO.LOW)
                    time.sleep(0.2)
                    GPIO.output(statusLightGPIO, GPIO.HIGH)
                    time.sleep(0.02)
                    GPIO.output(statusLightGPIO, GPIO.LOW)
                    time.sleep(0.2)
                    GPIO.output(statusLightGPIO, GPIO.HIGH)
                    time.sleep(0.02)
                elif LEDstate == 1:
                    GPIO.output(statusLightGPIO, GPIO.LOW)
                    time.sleep(0.2)
                    GPIO.output(statusLightGPIO, GPIO.HIGH)
                    time.sleep(0.02)
            try:
                GPIO.output(tallyLightGPIO, 0)
                ws.disconnect()
            except:
                pass
            logging.debug("Could not find OBS Studio - Waiting 2 seconds and re-attempting")
            print("Could not find OBS Studio - Waiting 2 seconds and re-attempting")

            print(lastCommunicationTime)
            time.sleep(2)

except KeyboardInterrupt: #End loop
    GPIO.output(tallyLightGPIO, 0)
    try:
      ws.disconnect()
    except:
      pass

logging.debug("Shutting Down")
print("Shutting Down")
GPIO.output(tallyLightGPIO, 0)
GPIO.cleanup()
