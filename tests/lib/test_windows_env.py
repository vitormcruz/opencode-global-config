"""Testes da persistencia de env vars de usuario no Windows (HKCU)."""

import sys
import types

import pytest

from fake_winreg import FakeWinreg
from opencode_config.lib import windows_env


@pytest.mark.unit
def test_set_user_env_writes_value_and_broadcasts(
    monkeypatch: pytest.MonkeyPatch,
    fake_winreg: FakeWinreg,
) -> None:
    broadcasts: list[str] = []
    monkeypatch.setattr(
        windows_env,
        "broadcast_environment_change",
        lambda: broadcasts.append("env"),
    )

    windows_env.set_user_env("OPENCODE_ENABLE_EXA", "1")

    assert fake_winreg.values["OPENCODE_ENABLE_EXA"] == "1"
    assert fake_winreg.set_calls == [("OPENCODE_ENABLE_EXA", "1")]
    assert broadcasts == ["env"]


@pytest.mark.unit
def test_get_user_env_reads_persisted_value(
    fake_winreg: FakeWinreg,
) -> None:
    fake_winreg.values["OPENCODE_ENABLE_EXA"] = "1"

    assert windows_env.get_user_env("OPENCODE_ENABLE_EXA") == "1"


@pytest.mark.unit
def test_get_user_env_returns_none_for_missing_value(
    fake_winreg: FakeWinreg,
) -> None:
    assert windows_env.get_user_env("INEXISTENTE") is None


@pytest.mark.unit
def test_broadcast_environment_change_requires_windows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ctypes falso sem windll: recusa o broadcast em qualquer SO."""

    monkeypatch.setitem(sys.modules, "ctypes", types.ModuleType("ctypes"))

    with pytest.raises(RuntimeError, match="Windows"):
        windows_env.broadcast_environment_change()


@pytest.mark.unit
def test_module_imports_without_winreg_available() -> None:
    assert "winreg" not in sys.modules or isinstance(
        sys.modules["winreg"],
        (types.ModuleType,),
    )
    assert callable(windows_env.set_user_env)
    assert callable(windows_env.get_user_env)
