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
import urllib

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
		
		self.recent = {}

	def setup(self):
		self.log.info("starting")

		GPIO.setwarnings(False)
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(17, GPIO.OUT)
		GPIO.output(17, GPIO.LOW)

	def loop(self):
		card = self.serial.readline()
		if not card:
			return

		card = card.strip()
		if len(card) != 10:
			return

		now = time.time()
		if card in self.recent:
			if now - self.recent[card] < 5.0:
				self.recent[card] = now
				return

		self.recent[card] = now

		self.handle_card_read(card)

	def stop(self):
		self.log.info("stopping")

	def handle_card_read(self, card):
		db = sqlite3.connect(self.db_file)
		db.row_factory = dict_factory
                baseurl = "http://my.protospace.ca/locks/door/108A/"

		self.unify_serial_numbers(db, card)

		# TODO flag duplicates
		cards = self.query_cards(db, card)
		if cards:
			card = cards.pop(0)

			# TODO merge duplicate values
			for temp in cards:
				pass

			self.update_timestamp(db, card['serial'])
			if not card['active']:
				self.log.warn("%s[%s] denied access" % (card["owner"], card['serial']))
                                urlaction = "DENIED"
                                rfid = "%s" % card['serial']

			else:
				self.log.info("%s[%s] entered the space" % (card["owner"], card['serial']))
                                urlaction = "ALLOWED"
                                rfid = "%s" % card['serial']

				threading.Thread(target=self.play_sound, kwargs={"path": "/home/pi/soundbyte/%s" % (card['soundbyte'],)}).start()
				threading.Thread(target=self.unlock_door, kwargs={"duration": 5.0}).start()

		else:
			self.log.info("Card read: %s" % (card,))
                        rfid = "%s" % (card,)
                        urlaction = "NOT IN DB"

                url = baseurl + rfid + "/" + urlaction
                response = urllib.urlopen(url).read()
                self.log.info("Web log response was %s" % (response))
		db.close()

	def unify_serial_numbers(self, db, card):
		q = "UPDATE cards SET serial='%s' WHERE serial='%s'" % (card, card[::-1])
		db.execute(q)

	def update_scan_log(self, db, card):
		q = "INSERT INTO scan_logs"

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
		query = "SELECT * FROM cards WHERE serial='%s' ORDER BY id ASC" % card
		cur.execute(query)

		cards = []

		row = cur.fetchone()
		while row:
			cards.append(row)
			row = cur.fetchone()

		self.log.debug(cards)

		return cards
