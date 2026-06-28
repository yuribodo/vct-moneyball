"""``vctm serve`` — run the read-only prediction API via uvicorn."""

from __future__ import annotations

import argparse

from vct_moneyball.common.logging import get_logger


def run_serve(args: argparse.Namespace) -> int:
    import uvicorn

    get_logger().info("serving ENC prediction API on http://%s:%d", args.host, args.port)
    uvicorn.run(
        "vct_moneyball.api.app:app",
        host=args.host,
        port=args.port,
        reload=getattr(args, "reload", False),
    )
    return 0
