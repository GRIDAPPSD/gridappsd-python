![Build Status](https://github.com/craig8/gridappsd-python/workflows/run-pytest/badge.svg)
    
# gridappsd-python
Python library for developing applications and services against the gridappsd api

## Installation

The `gridappsd-python` library requires python 3.6+ in order to work.
- Clone repository
- Install into your python environment `pip install . `

## Creating a connection to GridAPPS-D

```` python

from gridappsd import GridAPPSD

def on_message_callback(header, message):
    print(f"header: {header} message: {message}")

# Note: there are other parameters for connecting to other
# systems thatn localhost
gapps = GridAPPSD(username="user", password="pass")

assert gapps.connected

gapps.send('send.topic', {"foo": "bar"})

# Note we are sending the function not executing the function in the second parameter
gapps.subscribe('subscrbe.topic', on_message_callback)

gapps.send('subcribe.topic', 'A message about subscription')

time.sleep(5)

gapps.close()

````


## Testing

The testing requires gridappsd to be running in the docker container.  First install
the pytest environment `pip install pytest`.  Then run pytest from the root
of the gridappsd-python environment. 
