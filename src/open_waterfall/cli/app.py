from __future__ import annotations

import click

from open_waterfall.cli.commands.demo import demo_command
from open_waterfall.cli.commands.enrich import enrich_command
from open_waterfall.cli.commands.message import message_command
from open_waterfall.cli.commands.search import search_command
from open_waterfall.cli.commands.score import score_command
from open_waterfall.cli.commands.sync import sync_command


@click.group()
def main() -> None:
    """Open Waterfall CLI."""


main.add_command(enrich_command)
main.add_command(score_command)
main.add_command(message_command)
main.add_command(search_command)
main.add_command(sync_command)
main.add_command(demo_command)


if __name__ == "__main__":
    main()
