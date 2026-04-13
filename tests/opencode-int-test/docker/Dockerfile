FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/root/.opencode/bin:${PATH}"

RUN apt-get update && apt-get install -y \
    curl \
    git \
    jq \
    bash \
    nodejs \
    && rm -rf /var/lib/apt/lists/*

# Instala OpenCode via script oficial
RUN curl -fsSL https://opencode.ai/install | bash

# Copia o repositório
COPY . /opt/opencode-config
WORKDIR /opt/opencode-config

# Config de teste dedicada para o ambiente de integração do OpenCode
RUN cp tests/opencode-int-test/config/opencode.test.json opencode.json

# Executa bootstrap (cria symlinks em /root/.config/opencode)
RUN bash ./scripts/bootstrap_repo/opencode-link --yes

RUN chmod +x tests/opencode-int-test/docker/entrypoint.sh

EXPOSE 4096

# Sobe o mock MCP local e depois o opencode serve
CMD ["/opt/opencode-config/tests/opencode-int-test/docker/entrypoint.sh"]
