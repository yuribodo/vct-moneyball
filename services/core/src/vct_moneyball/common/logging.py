"""Logging and CLI error/exit helpers.

Convention (CLI contract): human-readable progress + errors go to stderr; the
machine-readable result (``--json``) goes to stdout. A validation failure raises
``CliError`` which the CLI entry point turns into a stderr message + non-zero exit.
"""

from __future__ import annotations

import logging
import sys

_LOGGER_NAME = "vctm"


class CliError(Exception):
    """A validation/usage failure that should exit non-zero with a clean message.

    ``exit_code`` defaults to 1; the CLI prints ``str(self)`` to stderr.
    """

    def __init__(self, message: str, *, exit_code: int = 1) -> None:
        super().__init__(message)
        self.exit_code = exit_code


def get_logger() -> logging.Logger:
    """Return the shared ``vctm`` logger, configured to write to stderr once."""
    logger = logging.getLogger(_LOGGER_NAME)
    if not logger.handlers:
        handler = logging.StreamHandler(stream=sys.stderr)
        handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


def set_verbose(verbose: bool) -> None:
    """Toggle DEBUG-level logging."""
    get_logger().setLevel(logging.DEBUG if verbose else logging.INFO)
