#!/bin/bash

set -eux

# Setup the path for running the gridappsd framework
export PATH=/gridappsd/services/fncsgossbridge/service:$PATH

cd /gridappsd

# clean up log files
if [ -d /gridappsd/log ]; then
  /bin/rm -rf /gridappsd/log/* 2 > /dev/null
fi
cd /gridappsd
java -Dgosh.args=--nointeractive -agentlib:jdwp=transport=dt_socket,server=y,suspend=n -jar lib/run.bnd.jar
