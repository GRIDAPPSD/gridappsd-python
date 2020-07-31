#!/bin/bash

echo " "
if [ "$1" = "version" -o "$1" = "-v" -o "$1" = "--version" ]; then
  if [ -f /gridappsd/dockerbuildversion.txt ]; then
    echo -n "version: "
    cat /gridappsd/dockerbuildversion.txt
  else
    echo "Error: can't find version"
  fi
  echo " "
  exit 0
fi

# Setup the path for running the gridappsd framework
export PATH=/gridappsd/services/fncsgossbridge/service:$PATH

cd /gridappsd

# clean up log files
if [ -d /gridappsd/log ]; then
  /bin/rm -rf /gridappsd/log/* 2 > /dev/null
fi

# If the DEBUG environmental variable is set and is not 0
# then expose the port for remote debugging.
if [ "${DEBUG:-0}" != "0" ]; then
    if tty -s ; then
        #Interactive terminal
	    # java -agentlib:jdwp=transport=dt_socket,server=y,address=8000,suspend=n -jar lib/run.bnd.jar
        java -agentlib:jdwp=transport=dt_socket,server=y,address=8000,suspend=n \
                      -Dcom.sun.management.jmxremote.port=2000 \
                      -Dcom.sun.management.jmxremote.authenticate=false \
                      -Dcom.sun.management.jmxremote.ssl=false \
                      -jar lib/run.bnd.jar

    else
	    java -Dgosh.args=--nointeractive -agentlib:jdwp=transport=dt_socket,server=y,address=8000,suspend=n -jar lib/run.bnd.jar
    fi
else
	java -jar lib/run.bnd.jar
fi
