#!/bin/bash

trap "exit" INT TERM ERR
trap "kill 0" EXIT

./run_api.sh &
./run_system.sh &
celery -A scheduler.tasks worker -l INFO -E

wait