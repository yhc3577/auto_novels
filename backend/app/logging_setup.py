"""Logging setup."""

from __future__ import annotations

import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)-5s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )
    # 屏蔽掉 sql alchemy 过于啰嗦的 echo
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)