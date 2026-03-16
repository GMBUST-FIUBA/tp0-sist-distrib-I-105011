#!/bin/bash
docker build ./echo-server-validator -t echo-server-validator:latest
docker run echo-server-validator:latest
exit 0