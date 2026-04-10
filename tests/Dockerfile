FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    curl \
    git \
    jq \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Instala OpenCode via script oficial
RUN curl -fsSL https://opencode.ai/install | bash

# Copia o repositório
COPY . /opt/opencode-config
WORKDIR /opt/opencode-config

# Executa bootstrap (cria symlinks em /root/.config/opencode)
RUN bash ./scripts/opencode-link --yes

EXPOSE 4096

# Sobe opencode serve como processo principal
CMD ["opencode", "serve", "--port", "4096"]
