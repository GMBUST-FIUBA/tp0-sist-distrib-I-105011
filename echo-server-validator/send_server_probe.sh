#!/bin/sh
SERVER="server"
PORT=12345

# Send probe
echo "PROBE_SERVER" | nc -w 10 $SERVER $PORT