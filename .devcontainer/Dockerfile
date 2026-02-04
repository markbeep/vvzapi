FROM docker.io/astral/uv:python3.14-trixie-slim

# dev tools
RUN apt-get update && apt-get install -y \
    vim \
    git \
    sqlite3 \
    curl

ENV EDITOR=vim

# install jj and tailwindcss for the host's architecture
RUN set -eux; \
    ARCH="$(uname -m)"; \
    case "${ARCH}" in \
          amd64|x86_64) JJ_ARCH="x86_64-unknown-linux-musl"; TAILWIND_ARCH="tailwindcss-linux-x64";; \
      arm64|aarch64) JJ_ARCH="aarch64-unknown-linux-musl"; TAILWIND_ARCH="tailwindcss-linux-arm64";; \
      *) echo "Unsupported ARCH=${ARCH}"; exit 1;; \
    esac; \
    curl -fL -o /tmp/jj.tar.gz "https://github.com/jj-vcs/jj/releases/download/v0.37.0/jj-v0.37.0-${JJ_ARCH}.tar.gz"; \
    tar -xzf /tmp/jj.tar.gz -C /tmp; mv /tmp/jj /usr/local/bin/jj; rm -f /tmp/jj.tar.gz; chmod +x /usr/local/bin/jj; \
    curl -fL -o /usr/local/bin/tailwindcss "https://github.com/tailwindlabs/tailwindcss/releases/download/v4.1.17/${TAILWIND_ARCH}"; \
    chmod +x /usr/local/bin/tailwindcss


CMD ["/bin/bash"]
