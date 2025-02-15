#!/bin/bash
flask db upgrade head
flask run --host 0.0.0.0 --port 8008 --with-threads #python -m server.main
exit

# Variables
PROGRAM_NAME="python -m server.main" # Full path to the program
RESTART_INTERVAL=600 # Time in seconds (e.g., 600 seconds = 10 mins)

# Function to start the program
start_program() {
  echo "Starting $PROGRAM_NAME..."
  $PROGRAM_NAME &
  PROGRAM_PID=$!
  echo "Program started with PID: $PROGRAM_PID"
}

# Function to stop the program
stop_program() {
  if [ -n "$PROGRAM_PID" ]; then
    echo "Stopping program with PID: $PROGRAM_PID..."
    kill $PROGRAM_PID
    wait $PROGRAM_PID 2>/dev/null
    echo "Program stopped."
  else
    echo "No program is currently running."
  fi
}

trap stop_program EXIT

# Main loop
while true; do
  start_program
  echo "Waiting for $RESTART_INTERVAL seconds before restarting..."
  sleep $RESTART_INTERVAL
  stop_program
done	
