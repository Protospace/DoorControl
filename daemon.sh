#! /bin/bash
# Author: Kevin Loney
#
# /etc/init.d/door
#
### BEGIN INIT INFO
# Provides: door
# Required-Start: $all
# Should-Start: 
# Required-Stop: 
# Should-Stop:
# Default-Start:  2 3 4 5
# Default-Stop:   0 1 6
# Short-Description: Control the Protospace door
# Description: Control the Protospace door system
### END INIT INFO

# Activate the python virtual environment
#    . /path_to_virtualenv/activate

DAEMON=/home/pi/DoorControl/app.py

case "$1" in
  start)
    echo "Starting server"
    # Start the daemon 
    python $DAEMON start
    ;;
  stop)
    echo "Stopping server"
    # Stop the daemon
    python $DAEMON stop
    ;;
  restart)
    echo "Restarting server"
    python $DAEMON stop
	python $DAEMON start
    ;;
  *)
    # Refuse to do other stuff
    echo "Usage: /etc/init.d/door {start|stop|restart}"
    exit 1
    ;;
esac

exit 0