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
RUN cp tests/integration/config/opencode.test.json opencode.json

# Executa bootstrap (cria symlinks em /root/.config/opencode)
RUN bash ./adapters/opencode/opencode-adapter.sh --yes

RUN chmod +x tests/integration/docker/entrypoint.sh

EXPOSE 4096

# Sobe o OpenCode para os testes comportamentais
CMD ["/opt/opencode-config/tests/integration/docker/entrypoint.sh"]
