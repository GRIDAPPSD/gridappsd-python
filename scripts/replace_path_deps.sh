#!/bin/sh
# This file shows how the sdist & wheel files can be manually modified afterwards
# to replace path dependencies with a version range.
# If the mono repo is at version 1.2.3, it will set the dependencies to (~=1.2,>=1.2.3), effectively equal to ~1.2.3.
set -x
set -u
set -e

VERSION=$(poetry version | awk '{print $2}')
VERSION_MINOR=$(echo $VERSION | sed -E "s/^([0-9]*\.[0-9]*).*/\1/")
curdir=$(pwd)
if [ "$(uname)" = "Darwin" ]; then export SEP=" "; else SEP=""; fi

# ===== Updating the TAR.GZ file =====
cd "$curdir"
TARFILES=$(ls dist/*.tar.gz)
for TARFILE in $TARFILES
do
    rm -rf /tmp/version_update
    mkdir -p /tmp/version_update
    tar -C /tmp/version_update -xf $curdir/$TARFILE
    cd /tmp/version_update
    # Replace the path dependencies (which are prefixed with '@')
    # with compatible version to the current monorepo, but at least at the current one.
    # In semver notation: ~1.2.3, which equals >=1.2.3, <2.0.0
    # Note that allowed matches are defined at:
    # https://peps.python.org/pep-0440/#compatible-release
    # We therefore specify that we require >=1.2.3 AND <2.0
    # Thus at least at the same fix version, but only compatible versions.
    # Therefore we use ~=1.2, which equals >=1.2,<2.0, together with >=1.2.3
    FOLDER=$(ls)
    sed -i$SEP'' "s|^Requires-Dist: \(.*\) @ \.\./.*|Requires-Dist: \1 (~=$VERSION_MINOR,>=$VERSION)|" "$FOLDER/PKG-INFO"
    sed -i$SEP'' "s| @ \.\.[a-zA-Z\-_/]*|~=$VERSION_MINOR,>=$VERSION|" "$FOLDER/setup.py"
    sed -i$SEP'' "s|{.*path.*\.\..*|\"~$VERSION\"|" "$FOLDER/pyproject.toml"
    tar -czvf new.tar.gz "$FOLDER"
    mv new.tar.gz $curdir/$TARFILE
done

# ===== Updating the WHEEL file =====
# Handle the tar.gz
cd "$curdir"
WHEELFILES=$(ls dist/*.whl)
for WHEELFILE in $WHEELFILES
do
    rm -rf /tmp/version_update
    mkdir -p /tmp/version_update
    unzip -d /tmp/version_update $curdir/$WHEELFILE 
    cd /tmp/version_update
    # Replace the path dependencies (which are prefixed with '@')
    # with compatible version to the current monorepo, but at least at the current one.
    # In semver notation: ~1.2.3, which equals >=1.2.3, <2.0.0
    # Note that allowed matches are defined at:
    # https://peps.python.org/pep-0440/#compatible-release
    # We therefore specify that we require >=1.2.3 AND <2.0
    # Thus at least at the same fix version, but only compatible versions.
    # Therefore we use ~=1.2, which equals >=1.2,<2.0, together with >=1.2.3
    FOLDER=$(ls -d *.dist-info)
    sed -i$SEP'' "s|^Requires-Dist: \(.*\) @ \.\./.*|Requires-Dist: \1 (~=$VERSION_MINOR,>=$VERSION)|" "$FOLDER/METADATA"
    zip -r new.whl ./*
    mv new.whl "$curdir/$WHEELFILE"
    cd "$curdir"
    rm -rf /tmp/version_update
done
