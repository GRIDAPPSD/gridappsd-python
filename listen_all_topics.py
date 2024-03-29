from time import sleep
from gridappsd import GridAPPSD

g = GridAPPSD()


def cb(header, msg):
    print(f"header: {header} message: {msg}")


g.subscribe("/topic/data", cb)

houses = g.get_houses()
hs = houses.get_houses_for_feeder('_503D6E20-F499-4CC7-8051-971E23D0BF79')
print(hs)

while True:
    sleep(0.1)
