FROM docker.io/astral/uv:python3.13-trixie-slim

RUN apt-get update && apt-get install -y \
    vim \
    git \
    sqlite3 \
    curl \

RUN curl -L -o /bin/tailwindcss https://github.com/tailwindlabs/tailwindcss/releases/download/v4.1.17/tailwindcss-linux-x64 && \
    chmod +x /bin/tailwindcss

