#!/usr/bin/env python3
"""Configure and start the OpenCode server inside the test image."""

from __future__ import annotations

import os


OPENCODE_BINARY = "/root/.opencode/bin/opencode"


def main() -> None:
    """Replace this process with OpenCode using the image-baked configuration."""

    os.execv(
        OPENCODE_BINARY,
        [
            OPENCODE_BINARY,
            "--pure",
            "serve",
            "--hostname",
            "0.0.0.0",
            "--port",
            "4096",
        ],
    )


if __name__ == "__main__":
    main()
