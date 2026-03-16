#!/bin/bash
docker build ./echo-server-validator -t echo-server-validator:latest
docker run --network tp0_testing_net echo-server-validator:latest
if [[ $? -eq 0 ]] ; then
    echo "action: test_echo_server | result: success"
else
    echo "action: test_echo_server | result: fail"
fi
exit 0