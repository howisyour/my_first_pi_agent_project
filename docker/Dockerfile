# Day 28: run the whole `pi` process inside a container instead of on the host.
#
# The image has to carry everything the *task* needs as well as the agent: the fixture's
# quality gate runs ruff and pytest, so if they are missing the agent cannot finish.
# Versions are pinned to the host's so the two arms differ in isolation, not in toolchain.

FROM python:3.13-slim-bookworm

ARG NODE_VERSION=24.18.0
ARG PI_VERSION=0.84.3

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl git xz-utils ripgrep fd-find \
    && rm -rf /var/lib/apt/lists/*

# Node from the official tarball, pinned to the host's version.
RUN curl -fsSLO "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.xz" \
    && tar -xJf "node-v${NODE_VERSION}-linux-x64.tar.xz" -C /usr/local --strip-components=1 \
    && rm "node-v${NODE_VERSION}-linux-x64.tar.xz" \
    && node --version

RUN npm install -g "@earendil-works/pi-coding-agent@${PI_VERSION}" \
    && npm cache clean --force

# Same versions as the host bench venv, so `python scripts/check.py` behaves identically.
RUN pip install --no-cache-dir ruff==0.15.5 pytest==8.3.4

# Pi looks for ripgrep/fd on PATH before downloading its own copies.
RUN ln -s "$(command -v fdfind)" /usr/local/bin/fd

ENV PYTHONUTF8=1 \
    PI_CODING_AGENT_DIR=/pi-agent \
    PI_CLI_JS=/usr/local/lib/node_modules/@earendil-works/pi-coding-agent/dist/bundle/cli.js

WORKDIR /work
