import time

import click
import yaml
import os

from gridappsd_field_bus import MessageBusDefinition
from gridappsd_field_bus.field_interface.field_proxy_forwarder import FieldProxyForwarder


@click.command()
@click.option('--username', required=True, help='Username for the connection.')
@click.option('--password', required=True, help='Password for the connection.')
@click.option('--connection_url', required=True, help='Connection URL.')
def start_forwarder(username, password, connection_url):
    """Start the field proxy forwarder with either a YAML configuration or cmd-line arguments."""

    # Use command-line arguments
    click.echo(f"Using command line arguments: {username}, {password}, {connection_url}")

    proxy_forwarder = FieldProxyForwarder(username, password, connection_url)

    time.sleep(0.1)



if __name__ == '__main__':
    start_forwarder()