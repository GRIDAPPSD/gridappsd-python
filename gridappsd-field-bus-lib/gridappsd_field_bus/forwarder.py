import time

from dotenv import load_dotenv
import click
import yaml
import os
import urllib

from gridappsd_field_bus import MessageBusDefinition
from gridappsd_field_bus.field_interface.field_proxy_forwarder import FieldProxyForwarder


@click.command()
@click.option('--username',
              default=lambda: os.getenv("GRIDAPPSD_USER"),
              metavar='USERNAME',
              type=str,
              help='Username for the connection.',
              show_default="from environment variable GRIDAPPSD_USER")
@click.option('--password',
              metavar='PASSWORD',
              type=str,
              default=lambda: os.getenv("GRIDAPPSD_PASSWORD"), 
              help='Password for the connection.',
              show_default="from environment variable GRIDAPPSD_PASSWORD")
@click.option('--connection_url', 
              default=lambda: os.getenv("GRIDAPPSD_ADDRESS"),
              type=str,
              metavar='URL',
              show_default="from environment variable GRIDAPPSD_ADDRESS",
              help='Connection URL.')
def start_forwarder(username, password, connection_url):
    """Start the field proxy forwarder with either a YAML configuration or cmd-line arguments."""

    required = [username, password, connection_url]
    if not all(required):
        click.echo("Username, password, and connection URL must be provided either through environment variables or command-line arguments.")
        click.Abort()

    parsed = urllib.parse.urlparse(connection_url)
    if not (parsed.hostname and parsed.port):
        click.echo("Invalid connection URL. It must include both hostname and port.")
        click.Abort()

    # Use command-line arguments
    click.echo(f"Using command line arguments: {username}, {password}, {connection_url}")

    proxy_forwarder = FieldProxyForwarder(username, password, connection_url)

    time.sleep(0.1)



if __name__ == '__main__':
    load_dotenv()
    start_forwarder()