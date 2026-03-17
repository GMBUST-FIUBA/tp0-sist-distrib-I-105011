#!/bin/sh
SERVER="server"
PORT=12345
PROBE_MESSAGE="PROBE_SERVER"

# Send probe
response=$(echo $PROBE_MESSAGE | nc -w 10 $SERVER $PORT)
if [ "$response" = "$PROBE_MESSAGE" ] ; then
    exit 0
else
    exit 1
fi