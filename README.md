# GridAPPS-D Sample Application

## Purpose

The purpose of this repository is to document the chosen way of installing and/or debugging applications into the GridAPPS-D docker container.

## Requirements

1. Docker ce version 17.12 or better.  You can install this via the docker_install_ubuntu.sh script.  (note for mint you will need to modify the file to work with xenial rather than ubuntu generically)

1. Please clone the repository <https://github.com/GRIDAPPSD/gridappsd-docker> next to this repository (they should both have the same parent folder)

```` bash
.
├── gridappsd-docker
└── gridappsd-sample-app
````

## Adding your application

In order to add your application to the you will need to modify the docker-compose.yml file in the gridappsd-docker repository.  Under the gridappsd service there is a volumes leaf where you will add the path to your application and mount it on the container's filesystem.

## Debugging your python applications

### Command line

In gridappsd we include a python package called remote_pdb.  This is the only BSD licensed product that we have found to be able to allow us to remotely debug our python based applicatoins.  To use it we need a telnet client and we need to modify the sample-applicatoin to break at a trace_point.

```` python

# The container allows ports between 8001-9000 to be used as anything
# you like.
from remote_pdb import RemotePdb

# Add the following where you would like to break within the python app.
RemotePdb('127.0.0.1', 8888).set_trace()

````

Connect to the remote debugging session via telnet 

```` bash

telnet '127.0.0.1' 8888
````

Once connected you can use any of the pdb commands to move to the next line set other breakpoints etc.  Documentation of those commands can be found at <https://docs.python.org/2/library/pdb.html#debugger-commands>.

To exit the telnet shell type 'quit' and press enter.

