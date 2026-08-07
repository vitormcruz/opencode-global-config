"""Escrita idempotente de blocos marcados em arquivos de configuracao."""

from pathlib import Path
import re


def _validate_name(name: str) -> None:
    if not name or "\n" in name or "\r" in name:
        raise ValueError("Nome de bloco invalido")


def _markers(name: str) -> tuple[str, str]:
    _validate_name(name)
    return (
        f"# >>> opencode-config:{name} >>>",
        f"# <<< opencode-config:{name} <<<",
    )


def _block_pattern(name: str) -> re.Pattern[str]:
    start, end = _markers(name)
    return re.compile(
        rf"^{re.escape(start)}\n.*?^{re.escape(end)}(?:\n|$)",
        flags=re.MULTILINE | re.DOTALL,
    )


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def update_marked_block(path: Path, name: str, content: str) -> None:
    """Cria ou substitui um bloco, mantendo uma unica instancia."""

    start, end = _markers(name)
    block = f"{start}\n{content.rstrip(chr(10) + chr(13))}\n{end}\n"
    existing = _read(Path(path))
    pattern = _block_pattern(name)

    if pattern.search(existing):
        updated = pattern.sub(block, existing)
    else:
        separator = "" if not existing else ("" if existing.endswith("\n\n") else "\n")
        updated = f"{existing}{separator}{block}"

    if updated != existing:
        _write(Path(path), updated)


def remove_marked_block(path: Path, name: str) -> bool:
    """Remove bloco marcado e informa se havia uma instancia para remover."""

    config_path = Path(path)
    existing = _read(config_path)
    pattern = _block_pattern(name)
    updated, count = pattern.subn("", existing)
    if count and updated != existing:
        _write(config_path, updated)
    return count > 0
