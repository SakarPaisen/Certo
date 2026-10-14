"""Certo — a coding-agent harness built on the OpenHands SDK.

Implementation is built out per docs/SPEC.md. Modules to add:
config, llm, tools, agent, runner, cli, and custom_tools/.
"""

import os

# The SDK prints a startup banner when `openhands.sdk` is first imported.
# Every entry point (certo, certo-server, certo-admin, python -m certo)
# imports this package first, so set it here, before any SDK import.
# setdefault: an explicit OPENHANDS_SUPPRESS_BANNER=0 still shows it.
os.environ.setdefault("OPENHANDS_SUPPRESS_BANNER", "1")

__version__ = "0.1.2"
