import os
import click

from .reddit import reddit


@click.group()
def cli():
    pass

cli.add_command(reddit)
