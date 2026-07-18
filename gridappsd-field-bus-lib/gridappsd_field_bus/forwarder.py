import time

from dotenv import load_dotenv
import click
import os
import urllib

from gridappsd_field_bus.field_interface.field_proxy_forwarder import FieldProxyForwarder


@click.command()
@click.option(
    "--username",
    default=lambda: os.getenv("GRIDAPPSD_USER"),
    metavar="USERNAME",
    type=str,
    help="Username for the connection.",
    show_default="from environment variable GRIDAPPSD_USER",
)
@click.option(
    "--password",
    metavar="PASSWORD",
    type=str,
    default=lambda: os.getenv("GRIDAPPSD_PASSWORD"),
    help="Password for the connection.",
    show_default="from environment variable GRIDAPPSD_PASSWORD",
)
@click.option(
    "--connection_url",
    default=lambda: os.getenv("GRIDAPPSD_ADDRESS"),
    type=str,
    metavar="URL",
    show_default="from environment variable GRIDAPPSD_ADDRESS",
    help="Connection URL.",
)
@click.option(
    "--mrid",
    default=lambda: os.getenv("GRIDAPPSD_FIELD_BUS_MRID"),
    type=str,
    metavar="MRID",
    show_default="from environment variable GRIDAPPSD_FIELD_BUS_MRID",
    help="mRID of the distribution area/substation to bridge for field bus forwarding.",
)
def start_forwarder(username, password, connection_url, mrid):
    """Start the field proxy forwarder with either a YAML configuration or cmd-line arguments."""

    required = [username, password, connection_url, mrid]
    if not all(required):
        click.echo(
            "Username, password, connection URL, and mrid must be provided either through environment variables or command-line arguments."
        )
        click.Abort()

    parsed = urllib.parse.urlparse(connection_url)
    if not (parsed.hostname and parsed.port):
        click.echo("Invalid connection URL. It must include both hostname and port.")
        click.Abort()

    # Use command-line arguments
    click.echo(f"Using command line arguments: {username}, {password}, {connection_url}, {mrid}")

    FieldProxyForwarder(
        connection_url=connection_url,
        username=username,
        password=password,
        mrid=mrid,
    )

    time.sleep(0.1)


if __name__ == "__main__":
    load_dotenv()
    start_forwarder()
