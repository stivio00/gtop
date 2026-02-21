# Dockerfile for building and running gtop
# This image is intended for use on hosts with NVIDIA GPUs and the
# NVIDIA Container Toolkit (nvidia-docker) enabled. It installs the
# Python package and runs the TUI. Demo mode can be used if no GPU
# is available.

FROM python:3.13-slim

# install necessary system packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        curl \
        ca-certificates \
        psmisc \
        procps \
        && rm -rf /var/lib/apt/lists/*

# set workdir
WORKDIR /app

# copy project
COPY . /app

# install python dependencies using uv
RUN pip install --upgrade pip setuptools uv
RUN uv sync

# default command
ENTRYPOINT ["gtop"]
CMD ["--demo"]
