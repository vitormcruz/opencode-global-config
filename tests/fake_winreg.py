"""winreg falso com armazenamento em memoria e registro de chamadas."""

from __future__ import annotations

import types


class FakeWinreg(types.ModuleType):
    """Substitui o modulo winreg em testes; nao toca no registro real."""

    HKEY_CURRENT_USER = "HKEY_CURRENT_USER"
    KEY_QUERY_VALUE = 1
    KEY_SET_VALUE = 2
    REG_SZ = 1
    REG_EXPAND_SZ = 2

    def __init__(self) -> None:
        super().__init__("winreg")
        self.values: dict[str, object] = {}
        self.set_calls: list[tuple[str, object]] = []

    class _Key:
        def __enter__(self) -> "FakeWinreg._Key":
            return self

        def __exit__(self, *_exc: object) -> None:
            return None

    def CreateKeyEx(
        self,
        _root: object,
        _subkey: str,
        _reserved: int,
        _access: int,
    ) -> "FakeWinreg._Key":
        return self._Key()

    def OpenKey(self, _root: object, _subkey: str) -> "FakeWinreg._Key":
        return self._Key()

    def QueryValueEx(self, _key: "FakeWinreg._Key", name: str) -> tuple[object, int]:
        if name not in self.values:
            raise FileNotFoundError(name)
        return self.values[name], FakeWinreg.REG_SZ

    def SetValueEx(
        self,
        _key: "FakeWinreg._Key",
        name: str,
        _reserved: int,
        value_type: int,
        value: object,
    ) -> None:
        assert value_type in (
            FakeWinreg.REG_SZ,
            FakeWinreg.REG_EXPAND_SZ,
        )
        self.values[name] = value
        self.set_calls.append((name, value))
