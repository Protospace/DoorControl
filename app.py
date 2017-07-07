#!/usr/bin/python

import RPi.GPIO as GPIO
import serial
import sqlite3
import os
import sys
from datetime import datetime
import time
import logging
import logging.handlers
import pygame

try:
	from daemon import runner
except ImportError:
	runner = None

import server

db_file = '/home/pi/production.sqlite3'

handler = logging.handlers.TimedRotatingFileHandler('/home/pi/log/door.log', when='W0') 
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

log = logging.getLogger()
log.addHandler(handler)
log.setLevel(logging.INFO)

#ser = serial.Serial(port='/dev/ttyAMA0', baudrate=2400, timeout=.5)
ser = serial.Serial(port='/dev/ttyAMA0', baudrate=2400, timeout=.1)

try:
	app = server.App(ser, db_file)
	if runner:
		app_runner = runner.DaemonRunner(app)
		app_runner.daemon_context.files_preserve=[handler.stream, ser]
		app_runner.do_action()
	else:
		app.run()
except KeyboardInterrupt:
	pass
except Exception as ex:
	log.exception(ex)