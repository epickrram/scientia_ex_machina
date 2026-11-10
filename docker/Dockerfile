# Image for bin/scientia --sandbox docker. Built on first use, tagged by this file's checksum.
# The container runs as the invoking user (any uid), so HOME is world-writeable.
FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash ca-certificates curl git python3 ripgrep tree procps less \
    && rm -rf /var/lib/apt/lists/*

# Claude Code's native installer targets $HOME; install under /opt and expose on PATH.
ARG CLAUDE_VERSION=stable
RUN HOME=/opt/claude bash -c 'curl -fsSL https://claude.ai/install.sh | bash -s "$0"' "$CLAUDE_VERSION" \
    && ln -s "$(readlink -f /opt/claude/.local/bin/claude)" /usr/local/bin/claude \
    && chmod -R a+rX /opt/claude \
    && mkdir -m 1777 /home/scientia /src /vault /notes /opt/scientia

ENV HOME=/home/scientia
WORKDIR /vault
