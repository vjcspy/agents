"""Debate CLI configuration."""

import os

# Server URL
DEBATE_SERVER_URL = os.getenv("DEBATE_SERVER_URL", "http://127.0.0.1:3456")

# Auth token (optional)
DEBATE_AUTH_TOKEN = os.getenv("DEBATE_AUTH_TOKEN")

# Wait deadline for long polling (seconds)
DEBATE_WAIT_DEADLINE = int(os.getenv("DEBATE_WAIT_DEADLINE", "120"))  # 2 minutes

# Poll timeout - must be > server's 60s to avoid premature disconnect
POLL_TIMEOUT = 65
