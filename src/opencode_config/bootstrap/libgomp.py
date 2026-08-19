"""Metadata and validation for the user-space libgomp runtime."""

from __future__ import annotations

import ctypes
import hashlib
import json
import platform
from pathlib import Path


LIBGOMP_VERSION = "12.2.0-14+deb12u1"
LIBGOMP_ARCHITECTURE = "amd64"
LIBGOMP_PACKAGE_NAME = f"libgomp1_{LIBGOMP_VERSION}_{LIBGOMP_ARCHITECTURE}.deb"
LIBGOMP_PACKAGE_URL = (
    "https://snapshot.debian.org/archive/debian/20250415T084322Z/pool/main/"
    "g/gcc-12/libgomp1_12.2.0-14%2Bdeb12u1_amd64.deb"
)
LIBGOMP_PACKAGE_SHA256 = (
    "48fec46bda7f5b1638b9e959889bfbc20491247d402d120bb152687eb48143d7"
)
LIBGOMP_LIBRARY_NAME = "libgomp.so.1.0.0"
LIBGOMP_LIBRARY_SHA256 = (
    "f9a9ad78a8dc39c0e90a265ffa551fae6c92a40f360889b44a7e141f9a2adfb1"
)
LIBGOMP_LICENSE = "GPLv3-or-later WITH GCC-exception-3.1"
LIBGOMP_RUNTIME_SUBDIRECTORY = "opencode-config/runtime/libgomp"


def runtime_directory(home: Path | None = None) -> Path:
    """Return the immutable-versioned user cache directory."""

    resolved_home = Path.home() if home is None else Path(home)
    return (
        resolved_home
        / ".cache"
        / LIBGOMP_RUNTIME_SUBDIRECTORY
        / f"{LIBGOMP_VERSION}-{LIBGOMP_ARCHITECTURE}"
    )


def runtime_library_path(home: Path | None = None) -> Path:
    """Return the canonical libgomp path in the user cache."""

    return runtime_directory(home) / LIBGOMP_LIBRARY_NAME


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def runtime_validation_error(
    home: Path | None = None,
    *,
    load_library: bool = True,
) -> str | None:
    """Return a human-readable error, or ``None`` for a valid runtime."""

    if platform.machine().lower() not in {"x86_64", "amd64"}:
        return (
            "a runtime libgomp fixada suporta somente Linux x86_64/amd64; "
            f"arquitetura detectada: {platform.machine()}"
        )
    library = runtime_library_path(home)
    if not library.is_file():
        return f"arquivo ausente: {library}"
    try:
        actual = _sha256(library)
    except OSError as error:
        return f"nao foi possivel ler {library}: {error}"
    if actual.casefold() != LIBGOMP_LIBRARY_SHA256:
        return (
            f"SHA-256 invalido para {library}: esperado "
            f"{LIBGOMP_LIBRARY_SHA256}, encontrado {actual}"
        )
    metadata_path = library.parent / "runtime.json"
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return f"metadados ausentes ou invalidos em {metadata_path}: {error}"
    if metadata != runtime_metadata():
        return f"metadados inesperados em {metadata_path}"
    link = library.parent / "libgomp.so.1"
    if not link.is_symlink() or link.resolve() != library.resolve():
        return f"link libgomp.so.1 ausente ou incorreto em {library.parent}"
    if load_library:
        try:
            ctypes.CDLL(str(link))
        except OSError as error:
            return f"carregamento ELF incompatível de {link}: {error}"
    return None


def runtime_is_valid(home: Path | None = None) -> bool:
    """Return whether the cached library is present, intact and loadable."""

    return runtime_validation_error(home) is None


def runtime_metadata() -> dict[str, str]:
    """Return the fixed provenance and licensing metadata."""

    return {
        "source": LIBGOMP_PACKAGE_URL,
        "package": LIBGOMP_PACKAGE_NAME,
        "version": LIBGOMP_VERSION,
        "architecture": LIBGOMP_ARCHITECTURE,
        "package_sha256": LIBGOMP_PACKAGE_SHA256,
        "library": LIBGOMP_LIBRARY_NAME,
        "library_sha256": LIBGOMP_LIBRARY_SHA256,
        "license": LIBGOMP_LICENSE,
    }


def write_runtime_metadata(directory: Path) -> None:
    """Persist provenance next to the extracted library."""

    (directory / "runtime.json").write_text(
        json.dumps(runtime_metadata(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
