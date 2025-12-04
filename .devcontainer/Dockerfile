FROM astral/uv:python3.13-trixie-slim

# gcc required for pyright
RUN apt-get update && apt-get install -y \
    vim \
    git \
    sqlite3 \
    curl \
    gcc

RUN curl -L -o /bin/tailwindcss https://github.com/tailwindlabs/tailwindcss/releases/download/v4.1.17/tailwindcss-linux-x64 && \
    chmod +x /bin/tailwindcss

