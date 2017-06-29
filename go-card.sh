#!/bin/bash

echo "Starting Update"
sqlite3 production.sqlite3 < updatecards.sql
echo "Completed Update"

