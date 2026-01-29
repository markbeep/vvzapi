FROM docker.io/astral/uv:python3.13-trixie-slim

# dev tools
RUN apt-get update && apt-get install -y \
    vim \
    git \
    sqlite3 \
    curl

ENV EDITOR=vim

RUN curl -Lo jj.tar.gz https://github.com/jj-vcs/jj/releases/download/v0.37.0/jj-v0.37.0-x86_64-unknown-linux-musl.tar.gz && \
    tar -xzf jj.tar.gz -C /bin ./jj && \
    rm jj.tar.gz && \
    chmod +x /bin/jj


# project tools
RUN curl -Lo /bin/tailwindcss https://github.com/tailwindlabs/tailwindcss/releases/download/v4.1.17/tailwindcss-linux-x64 && \
    chmod +x /bin/tailwindcss


CMD ["/bin/bash"]
