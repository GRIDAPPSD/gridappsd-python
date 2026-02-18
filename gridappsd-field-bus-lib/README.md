# gridappsd-field-bus

A distributed field bus communication framework for the [GridAPPS-D](https://gridappsd.readthedocs.io) platform. Provides hierarchical agent-based communication across power grid field devices, enabling decentralized control and context management at the substation, feeder, switch area, and secondary area levels.

## Features

- **Message Bus Abstraction** - Pluggable message bus architecture with support for STOMP, GridAPPS-D, and VOLTTRON connection types
- **Distributed Agents** - Hierarchical agent framework (`SubstationAgent`, `FeederAgent`, `SwitchAreaAgent`, `SecondaryAreaAgent`) for multi-level grid communication
- **Context Management** - Topology-aware context managers that provide neighborhood information to distributed agents via CIM-Graph
- **Field Proxy Forwarding** - Bridges field device buses to the operational technology (OT) bus when direct connections are unavailable
- **Protocol Support** - Extensible protocol transformers for IEEE 2030.5 and DNP3 field protocols

## Installation

```bash
pip install gridappsd-field-bus
```

## Requirements

- Python >= 3.10
- [gridappsd-python](https://pypi.org/project/gridappsd-python/)
- [cim-graph](https://pypi.org/project/cim-graph/)

## CLI Commands

**Start the field proxy forwarder:**

```bash
start-field-bus-forwarder --username app_user --password 1234App
```

**Start centralized context managers:**

```bash
context_manager --feeder_id <feeder_mrid> --simulation_id <sim_id>
```

## Documentation

See the main [GridAPPS-D Python repository](https://github.com/GRIDAPPSD/gridappsd-python) for full documentation.
