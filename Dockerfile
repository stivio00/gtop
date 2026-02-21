FROM python:3.13-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        curl \
        ca-certificates \
        psmisc \
        procps \
        && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . /app

RUN pip install --upgrade pip
RUN pip install .

ENTRYPOINT ["gtop"]
CMD ["--demo"]