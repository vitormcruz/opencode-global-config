"""Registro declarativo das dependencias gerenciadas pelo bootstrap."""

from dataclasses import dataclass
from collections.abc import Mapping

from opencode_config.lib.environment import EnvironmentKind


@dataclass(frozen=True)
class DependencySpec:
    """Contrato de deteccao e instalacao de uma dependencia."""

    name: str
    commands: tuple[str, ...]
    install_methods: Mapping[EnvironmentKind, str]
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

    def install_method_for(self, environment: EnvironmentKind) -> str:
        """Retorna o metodo previsto para um ambiente."""

        return self.install_methods[environment]


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


DEPENDENCY_REGISTRY: tuple[DependencySpec, ...] = (
    DependencySpec(
        name="python",
        commands=("python3", "python"),
        install_methods=_methods(
            "pre-requisito: Python >= 3.10",
            windows="pre-requisito: Python >= 3.10 (instalacao por usuario)",
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
    ),
    DependencySpec(
        name="pipx",
        commands=("pipx",),
        install_methods=_methods(
            "pip install --user pipx",
            windows="python -m pip install --user pipx",
        ),
    ),
    DependencySpec(
        name="crwl",
        commands=("crwl",),
        install_methods=_methods(
            "pipx install crawl4ai + crawl4ai-setup",
        ),
        version_args=("--help",),
    ),
    DependencySpec(
        name="docling",
        commands=("docling",),
        install_methods=_methods("pipx install docling"),
    ),
    DependencySpec(
        name="codebase-memory-mcp",
        commands=("codebase-memory-mcp",),
        install_methods=_methods(
            "npm install -g codebase-memory-mcp com prefix user-space",
            windows="npm install -g codebase-memory-mcp com prefix user-space",
        ),
    ),
    DependencySpec(
        name="pandoc",
        commands=("pandoc",),
        install_methods=_methods(
            "download do arquivo portatil oficial",
            windows="download do zip portatil oficial",
        ),
    ),
    DependencySpec(
        name="git",
        commands=("git",),
        install_methods=_methods(
            "git pre-instalado ou pacote do sistema",
            windows="PortableGit em user-space",
        ),
    ),
    DependencySpec(
        name="playwright",
        commands=("playwright",),
        install_methods=_methods(
            "npx playwright install",
            windows="npx playwright install",
        ),
    ),
    DependencySpec(
        name="pytest",
        commands=("pytest",),
        install_methods=_methods(
            "criar .venv e instalar requirements-dev.txt",
            windows="criar .venv e instalar requirements-dev.txt",
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
    ),
)

if {
    environment
    for spec in DEPENDENCY_REGISTRY
    for environment in spec.install_methods
} != _ALL_ENVIRONMENTS:
    raise RuntimeError("Registro de dependencias sem metodo para algum ambiente")
