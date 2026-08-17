FROM python:3.12-bookworm

ENV PATH="/root/.opencode/bin:${PATH}"

# Instala OpenCode via script oficial
RUN curl -fsSL https://opencode.ai/install | bash

# Copia o repositório
COPY . /opt/opencode-config
WORKDIR /opt/opencode-config

# Config de teste dedicada para o ambiente de integração do OpenCode
RUN cp tests/integration/config/opencode.test.json opencode.json

# Executa bootstrap (cria symlinks em /root/.config/opencode)
RUN PYTHONPATH=/opt/opencode-config/src \
    python3 -m opencode_config.adapters.opencode --yes

RUN chmod +x tests/integration/docker/entrypoint.py

EXPOSE 4096

# Sobe o OpenCode para os testes comportamentais
CMD ["python3", "/opt/opencode-config/tests/integration/docker/entrypoint.py"]
