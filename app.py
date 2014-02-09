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

db_file = '/home/pi/production.sqlite3'

handler = logging.handlers.TimedRotatingFileHandler('/home/pi/log/door.log', when='W0') 
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

log = logging.getLogger()
log.addHandler(handler)
log.setLevel(logging.DEBUG)

ser = serial.Serial(port='/dev/ttyAMA0', baudrate=2400, timeout=.5)

# The database connection is opened and closed on every card read so we can modify it externally
db = None

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)
GPIO.output(17, GPIO.LOW)

pygame.mixer.init()
pygame.mixer.music.set_volume(1.0)

def datetime_converter(s):
	return datetime.strptime(s, '%Y-%d-%d %H:%M:%S')
#sqlite3.register_converter("datetime", datetime_converter)

def dict_factory(cursor, row):
	d = {}
	for idx, col in enumerate(cursor.description):
		d[col[0]] = row[idx]
	return d

def query_cards(card):
	cur = db.cursor()
	query = "SELECT * FROM cards WHERE serial = '%s' ORDER BY id ASC" % card
	cur.execute(query)

	log.debug(query)

	cards = []

	row = cur.fetchone()
	while row:
		cards.append(row)
		row = cur.fetchone()

	log.debug(cards)

	return cards

def update_timestamp(card):
	q = "UPDATE cards SET first_seen = datetime('now') WHERE serial = '%s' AND first_seen IS NULL" % (card)
	db.execute(q)

	q = "UPDATE cards SET last_seen = datetime('now') WHERE serial = '%s'" % (card)
	db.execute(q)

	db.commit()

def play_sound(path):
	if not (path and os.path.exists(path)):
		return

	if not pygame.mixer.music.get_busy():
		try:
			pygame.mixer.music.load(path)
			pygame.mixer.music.play()
		except:
			log.warn("Failed to sound '%s'" % (path))

last_card = None
while True:
	# Read from the serial port and skip duplicates
	card = ser.readline()
	if not card:
		last_card = None
		continue
	if card == last_card:
		continue
	last_card = card

	# Card numbers are 10, pull the \r\n off the end
	card = card[:10]
	log.info("Card read: %s" % (card))

	db = sqlite3.connect(db_file)
	db.row_factory = dict_factory

	# Remove all reversed card serial numbers
	q = "UPDATE cards SET serial = '%s' WHERE serial = '%s'" % (card, card[::-1])
	db.execute(q)

	# TODO flag duplicates
	cards = query_cards(card)
	if cards:
		card = cards.pop(0)
		log.debug("Card id %s" % card['id'])

		for temp in cards:
			pass

		update_timestamp(card['serial'])

		log.info("Unlocking")
		GPIO.output(17, GPIO.HIGH)		

		time.sleep(5)
		play_sound("/home/pi/soundbyte/%s" % (card['soundbyte']))

		log.debug("Locking")
		GPIO.output(17, GPIO.LOW)

	db.close()
