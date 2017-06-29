import csv
import sqlite3
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('database')
parser.add_argument('diff')

args = parser.parse_args()

insert = []
update = []

with open(args.diff, 'r') as f:
	reader = csv.DictReader(f)
	for row in reader:
		key = row['FobId']
		active = int(row['Active'])
		if not key:
			continue

		if active:
			if row['Name']:
				insert.append((active, key, row['Name']))
			else:
				update.append((active, key))
		else:
			update.append((active, key))

with sqlite3.connect(args.database) as db:
	cursor = db.cursor()
	cursor.executemany('UPDATE cards SET active=? WHERE serial=?', update)
	cursor.executemany('INSERT INTO cards(active,serial,owner) VALUES (?,?,?)', insert)
