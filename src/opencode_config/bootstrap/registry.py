"""Registro declarativo das dependencias gerenciadas pelo bootstrap."""

from dataclasses import dataclass, field
from collections.abc import Mapping

from opencode_config.lib.environment import EnvironmentKind


@dataclass(frozen=True)
class DependencySpec:
    """Contrato de deteccao e instalacao de uma dependencia."""

    name: str
    commands: tuple[str, ...]
    install_methods: Mapping[EnvironmentKind, str]
    manual_commands: Mapping[EnvironmentKind, str] = field(default_factory=dict)
    commands_by_environment: Mapping[
        EnvironmentKind,
        tuple[str, ...],
    ] = field(default_factory=dict)
    supported_environments: frozenset[EnvironmentKind] | None = None
    required: bool = True
    version_args: tuple[str, ...] = ("--version",)
    version_pattern: str = (
        r"(?P<version>\d+(?:\.\d+)+(?:[-+][0-9A-Za-z.-]+)?)"
    )
    minimum_version: tuple[int, ...] | None = None

    @property
    def command(self) -> str:
        """Retorna o primeiro comando candidato da dependencia."""

        return self.commands[0]

    def commands_for(self, environment: EnvironmentKind) -> tuple[str, ...]:
        """Retorna os comandos candidatos para um ambiente."""

        return self.commands_by_environment.get(environment, self.commands)

    def install_method_for(self, environment: EnvironmentKind) -> str:
        """Retorna o metodo previsto para um ambiente."""

        return self.install_methods[environment]

    def manual_command_for(self, environment: EnvironmentKind) -> str:
        """Retorna o comando copiavel previsto para um ambiente."""

        return self.manual_commands.get(
            environment,
            self.install_method_for(environment),
        )


_ALL_ENVIRONMENTS = {
    EnvironmentKind.LINUX,
    EnvironmentKind.WSL,
    EnvironmentKind.WINDOWS,
}


def _methods(linux: str, wsl: str | None = None, windows: str = ""):
    """Cria o mapa de metodos mantendo a declaracao da tabela compacta."""

    wsl_method = linux if wsl is None else wsl
    return {
        EnvironmentKind.LINUX: linux,
        EnvironmentKind.WSL: wsl_method,
        EnvironmentKind.WINDOWS: windows,
    }


def _commands(linux: str, wsl: str | None = None, windows: str = ""):
    """Cria o mapa de comandos copiaveis por ambiente."""

    wsl_command = linux if wsl is None else wsl
    return {
        EnvironmentKind.LINUX: linux,
        EnvironmentKind.WSL: wsl_command,
        EnvironmentKind.WINDOWS: windows,
    }


DEPENDENCY_REGISTRY: tuple[DependencySpec, ...] = (
    DependencySpec(
        name="python",
        commands=("python3", "python"),
        commands_by_environment={
            EnvironmentKind.WINDOWS: ("python", "python3"),
        },
        install_methods=_methods(
            "pre-requisito: Python >= 3.10",
            windows="pre-requisito: Python >= 3.10 (instalacao por usuario)",
        ),
        manual_commands=_commands(
            "python3 --version",
            windows=(
                "winget install --scope user --id Python.Python.3.12"
            ),
        ),
        minimum_version=(3, 10),
    ),
    DependencySpec(
        name="node",
        commands=("node",),
        install_methods=_methods(
            "fnm em user-space",
            windows="fnm-windows.zip em user-space",
        ),
        manual_commands=_commands(
            "fnm install 22 && fnm use 22",
            windows="fnm install 22; fnm use 22",
        ),
        minimum_version=(22,),
    ),
    DependencySpec(
        name="npm",
        commands=("npm",),
        install_methods=_methods(
            "fnm em user-space",
            windows="fnm-windows.zip em user-space",
        ),
        manual_commands=_commands(
            "fnm install 22 && fnm use 22",
            windows="fnm install 22; fnm use 22",
        ),
        version_args=("--version",),
    ),
    DependencySpec(
        name="npx",
        commands=("npx",),
        install_methods=_methods(
            "fnm em user-space",
            windows="fnm-windows.zip em user-space",
        ),
        manual_commands=_commands(
            "fnm install 22 && fnm use 22",
            windows="fnm install 22; fnm use 22",
        ),
        version_args=("--version",),
    ),
    DependencySpec(
        name="pipx",
        commands=("pipx",),
        install_methods=_methods(
            "pip install --user pipx",
            windows="python -m pip install --user pipx",
        ),
        manual_commands=_commands(
            "python3 -m pip install --user pipx",
            windows="python -m pip install --user pipx",
        ),
    ),
    DependencySpec(
        name="crwl",
        commands=("crwl",),
        install_methods=_methods(
            "pipx install crawl4ai + crawl4ai-setup",
        ),
        manual_commands=_commands(
            "pipx install crawl4ai && crawl4ai-setup",
            windows="pipx install crawl4ai; crawl4ai-setup",
        ),
        version_args=("--help",),
    ),
    DependencySpec(
        name="docling",
        commands=("docling",),
        install_methods=_methods("pipx install docling"),
        manual_commands=_commands(
            "pipx install docling",
            windows="pipx install docling",
        ),
    ),
    DependencySpec(
        name="codebase-memory-mcp",
        commands=("codebase-memory-mcp",),
        install_methods=_methods(
            "npm install -g codebase-memory-mcp com prefix user-space",
            windows="npm install -g codebase-memory-mcp com prefix user-space",
        ),
        manual_commands=_commands(
            "npm install --global --prefix \"$HOME/.local\" "
            "codebase-memory-mcp@0.9.0",
            windows=(
                'npm install --global --prefix "$env:APPDATA\\npm" '
                "codebase-memory-mcp@0.9.0"
            ),
        ),
        minimum_version=(0, 9, 0),
    ),
    DependencySpec(
        name="pandoc",
        commands=("pandoc",),
        install_methods=_methods(
            "download do arquivo portatil oficial",
            windows="download do zip portatil oficial",
        ),
        manual_commands=_commands(
            "\n".join(
                (
                    'mkdir -p "$HOME/.local"',
                    (
                        'curl -fL "https://github.com/jgm/pandoc/releases/'
                        'download/3.7.0.2/'
                        'pandoc-3.7.0.2-linux-amd64.tar.gz" '
                        '-o "/tmp/pandoc.tar.gz"'
                    ),
                    (
                        'tar -xzf "/tmp/pandoc.tar.gz" '
                        '--strip-components=1 -C "$HOME/.local"'
                    ),
                    'rm -f "/tmp/pandoc.tar.gz"',
                )
            ),
            windows="\n".join(
                (
                    '$archive = Join-Path $env:TEMP "pandoc.zip"',
                    (
                        '$destination = Join-Path $env:LOCALAPPDATA '
                        '"opencode-config\\bin"'
                    ),
                    (
                        'New-Item -ItemType Directory -Force '
                        '$destination | Out-Null'
                    ),
                    (
                        'Invoke-WebRequest -Uri '
                        '"https://github.com/jgm/pandoc/releases/download/'
                        '3.7.0.2/pandoc-3.7.0.2-windows-x86_64.zip" '
                        '-OutFile $archive'
                    ),
                    (
                        '$extract = Join-Path $env:TEMP '
                        '"pandoc-extract"'
                    ),
                    'Expand-Archive -Force $archive $extract',
                    (
                        'Copy-Item (Join-Path $extract '
                        '"pandoc-3.7.0.2\\pandoc.exe") $destination'
                    ),
                    'Remove-Item -Recurse -Force $extract, $archive',
                )
            ),
        ),
    ),
    DependencySpec(
        name="git",
        commands=("git",),
        install_methods=_methods(
            "git pre-instalado ou pacote do sistema",
            windows="PortableGit em user-space",
        ),
        manual_commands=_commands(
            "git --version",
            windows="\n".join(
                (
                    (
                        '$archive = Join-Path $env:TEMP '
                        '"PortableGit-2.53.0-64-bit.7z.exe"'
                    ),
                    (
                        'Invoke-WebRequest -Uri '
                        '"https://github.com/git-for-windows/git/releases/'
                        'download/v2.53.0.windows.1/'
                        'PortableGit-2.53.0-64-bit.7z.exe" '
                        '-OutFile $archive'
                    ),
                    (
                        '$destination = Join-Path $env:LOCALAPPDATA '
                        '"opencode-config\\PortableGit"'
                    ),
                    (
                        'Start-Process -Wait -FilePath $archive '
                        '-ArgumentList "-y", "-o$destination"'
                    ),
                    'Remove-Item $archive',
                )
            ),
        ),
    ),
    DependencySpec(
        name="playwright",
        commands=("playwright",),
        install_methods=_methods(
            "npx playwright install",
            windows="npx playwright install",
        ),
        manual_commands=_commands(
            "npx --yes playwright install chromium",
            windows="npx --yes playwright install chromium",
        ),
    ),
    DependencySpec(
        name="pytest",
        commands=("pytest",),
        install_methods=_methods(
            "criar .venv e instalar requirements-dev.txt",
            windows="criar .venv e instalar requirements-dev.txt",
        ),
        manual_commands=_commands(
            "python3 -m venv .venv && "
            ".venv/bin/python -m pip install -r requirements-dev.txt",
            windows=(
                "python -m venv .venv; "
                ".venv\\Scripts\\python.exe -m pip install "
                "-r requirements-dev.txt"
            ),
        ),
        required=False,
    ),
    DependencySpec(
        name="aws-cli",
        commands=("aws",),
        install_methods=_methods(
            "script oficial AWS em modo user-local",
            windows="script oficial AWS em modo user-local",
        ),
        manual_commands=_commands(
            'curl -fsSL "https://awscli.amazonaws.com/v2/install.sh" | bash',
            windows='irm "https://awscli.amazonaws.com/v2/install.ps1" | iex',
        ),
        minimum_version=(2,),
    ),
    DependencySpec(
        name="libgomp-runtime",
        commands=("libgomp-runtime",),
        supported_environments=frozenset(
            {EnvironmentKind.LINUX, EnvironmentKind.WSL}
        ),
        install_methods=_methods(
            "pacote Debian oficial extraido no cache user-space",
            windows="nao aplicavel",
        ),
        manual_commands=_commands(
            "opencode-bootstrap --yes",
            windows="opencode-bootstrap --yes",
        ),
        version_args=(),
        minimum_version=None,
    ),
    DependencySpec(
        name="opencode-config",
        commands=("opencode-config-check",),
        install_methods=_methods(
            "pipx install --editable .",
            windows="pipx install --editable .",
        ),
        manual_commands=_commands(
            "pipx install --editable .",
            windows="pipx install --editable .",
        ),
    ),
    DependencySpec(
        name="copilot",
        commands=("copilot",),
        supported_environments=frozenset({EnvironmentKind.WINDOWS}),
        install_methods=_methods(
            "cliente Copilot externo",
            windows="npm install --global --prefix user-space @github/copilot",
        ),
        manual_commands=_commands(
            "npm install --global --prefix \"$HOME/.local\" @github/copilot",
            windows=(
                'npm install --global --prefix "$env:APPDATA\\npm" '
                "@github/copilot"
            ),
        ),
    ),
)

if {
    environment
    for spec in DEPENDENCY_REGISTRY
    for environment in spec.install_methods
} != _ALL_ENVIRONMENTS:
    raise RuntimeError("Registro de dependencias sem metodo para algum ambiente")
