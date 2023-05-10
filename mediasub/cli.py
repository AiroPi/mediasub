from __future__ import annotations

import logging
import os
import sys
import time
import tomllib
from typing import TYPE_CHECKING, Any

import click

from .builtins.posters import ForumWebhook, MultipleWebhooks
from .builtins.sources import ScanVFDotNet
from .main import ScanDownloader

if TYPE_CHECKING:
    from .poster import Poster

logger = logging.getLogger(__name__)

config: dict[str, Any] = {}
if os.path.exists("config.toml"):
    with open("config.toml", "rb") as f:
        config = tomllib.load(f)
else:
    logger.error("No config.toml file found")
    sys.exit(1)

if config.get("forum_webhook") and config.get("webhooks"):
    logger.error("You can't use both forum_webhook and webhooks in the config")
    sys.exit(1)

# This method will be used to post the chapter (anywhere). Can create an own method.
post_service: list[Poster] | Poster | None
if config.get("webhooks"):
    if not config["webhooks"].get("global"):
        logger.error('A "global" webhook must be defined in the "webhooks" section')
        sys.exit(1)
    post_service = MultipleWebhooks(config["webhooks"])
elif config.get("forum_webhook"):
    post_service = ForumWebhook(config["forum_webhook"])
else:
    post_service = None

active_mangas: list[str] | None = config.get("active_mangas", None)

scan_dl = ScanDownloader(ScanVFDotNet(), active_mangas, post_service)


@click.group()
def cli():
    """Scan VF Downloader"""
    pass


@cli.command()
@click.option("--every", default=60, help="Interval between each sync in minutes")
def cron(every: int):
    while True:
        try:
            scan_dl.sync()
        except Exception as e:
            print(e)
        time.sleep(every * 60)


@cli.command()
def make_history():
    scan_dl.sync(without_posting=True)


@cli.command()
def sync():
    scan_dl.sync()


if __name__ == "__main__":
    cli()
