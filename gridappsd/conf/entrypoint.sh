#!/bin/bash

set -eux

# Install application python requirements
for reqfile in `ls /gridappsd/services/*/requirements.txt 2>/dev/null`; do
  echo "[Entrypoint] Installing requirements $reqfile"
  sudo pip install -q --disable-pip-version-check -r $reqfile
done
for reqfile in `ls /gridappsd/applications/*/requirements.txt 2>/dev/null`; do
  echo "[Entrypoint] Installing requirements $reqfile"
  sudo pip install -q --disable-pip-version-check -r $reqfile
done

echo "[Entrypoint] Starting the platform"
/startup/conf/run-gridappsd.sh

tail -f /dev/null