import os
import sys
import RPi.GPIO as GPIO
import serial
import sqlite3
import atexit
import time
import logging
import pygame
import threading

def dict_factory(cursor, row):
	d = {}
	for idx, col in enumerate(cursor.description):
		d[col[0]] = row[idx]
	return d

class DaemonApp(object):
	def __init__(self):
		self.stdin_path = '/dev/null'
		self.stdout_path = '/dev/null'
		self.stderr_path = '/dev/null'
		self.pidfile_path =  '/var/run/door.pid'
		self.pidfile_timeout = 5

		self.running = True
		self.log = logging.getLogger("daemon")

	def __halt(self):
		self.running = False

	def run(self):
		atexit.register(self.__halt)

		self.setup()
		while self.running:
			try:
				self.loop()
			except KeyboardInterrupt:
				break
			except Exception as ex:
				self.log.exception(ex)
				break

		self.stop()

	def setup(self):
		pass

	def stop(self):
		pass

	def loop(self):
		pass

class App(DaemonApp):
	def __init__(self, serial, db_file):
		super(App, self).__init__();

		self.serial = serial
		self.db_file = db_file
		
		self.last_card = None
		self.last_read = 0.0

	def setup(self):
		self.log.info("starting")

		GPIO.setwarnings(False)
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(17, GPIO.OUT)
		GPIO.output(17, GPIO.LOW)

		

	def loop(self):
		card = self.serial.readline()
		if not card:
			self.last_card = None
			return

		now = time.time()
		if now - self.last_read > 5.0:
			self.last_card = None

		card = card.strip()
		if len(card) != 10:
			return

		self.last_read = now
		if card == self.last_card:
			return
		self.last_card = card
		

		self.handle_card_read(card)

	def stop(self):
		self.log.info("stopping")

	def handle_card_read(self, card):
		self.log.info("Card read: %s" % (card,))

		db = sqlite3.connect(self.db_file)
		db.row_factory = dict_factory

		self.unify_serial_numbers(db, card)

		# TODO flag duplicates
		cards = self.query_cards(db, card)
		if cards:
			card = cards.pop(0)

			# TODO merge duplicate values
			for temp in cards:
				pass

			self.update_timestamp(db, card['serial'])

			self.log.info("%s has entered the space" % (card["owner"],))

			threading.Thread(target=self.play_sound, kwargs={"path": "/home/pi/soundbyte/%s" % (card['soundbyte'],)}).start()
			threading.Thread(target=self.unlock_door, kwargs={"duration": 5.0}).start()
			#self.play_sound("/home/pi/soundbyte/%s" % (card['soundbyte'],))
			#self.unlock_door(5.0)

		db.close()

	def unify_serial_numbers(self, db, card):
		q = "UPDATE cards SET serial = '%s' WHERE serial = '%s'" % (card, card[::-1])
		db.execute(q)

	def update_timestamp(self, db, card):
		q = "UPDATE cards SET first_seen = datetime('now') WHERE serial = '%s' AND first_seen IS NULL" % (card)
		db.execute(q)

		q = "UPDATE cards SET last_seen = datetime('now') WHERE serial = '%s'" % (card)
		db.execute(q)

		db.commit()

	def unlock_door(self, duration):
		GPIO.output(17, GPIO.HIGH)
		time.sleep(duration)
		GPIO.output(17, GPIO.LOW)

	def play_sound(self, path):
		if not (path and os.path.exists(path)):
			return

		if not pygame.mixer.music.get_busy():
			try:
				pygame.mixer.music.load(path)
				pygame.mixer.music.play()
			except:
				self.log.warn("Failed to play sound '%s'" % (path))

	def query_cards(self, db, card):
		cur = db.cursor()
		query = "SELECT * FROM cards WHERE serial = '%s' ORDER BY id ASC" % card
		cur.execute(query)

		cards = []

		row = cur.fetchone()
		while row:
			cards.append(row)
			row = cur.fetchone()

		self.log.debug(cards)

		return cards
