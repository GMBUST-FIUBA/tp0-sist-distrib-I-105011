#!/bin/bash
docker build ./echo-server-validator -t echo-server-validator:latest
docker run --network tp0_testing_net echo-server-validator:latest
exit 0