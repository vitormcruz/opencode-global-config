"""Persistencia de variaveis de usuario no Windows via HKCU\\Environment."""

from __future__ import annotations


def broadcast_environment_change() -> None:
    """Notifica o Explorer (WM_SETTINGCHANGE) sem exigir logoff."""

    import ctypes

    if not hasattr(ctypes, "windll"):
        raise RuntimeError(
            "broadcast de WM_SETTINGCHANGE exige o Windows (user32)"
        )

    result = ctypes.c_ulong()
    ctypes.windll.user32.SendMessageTimeoutW(
        0xFFFF,  # HWND_BROADCAST
        0x001A,  # WM_SETTINGCHANGE
        0,
        ctypes.c_wchar_p("Environment"),
        0x0002,  # SMTO_ABORTIFHUNG
        5000,
        ctypes.byref(result),
    )


def get_user_env(name: str) -> str | None:
    """Retorna o valor persistido em HKCU\\Environment; None se ausente."""

    import winreg

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            "Environment",
        ) as key:
            value, _ = winreg.QueryValueEx(key, name)
    except FileNotFoundError:
        return None
    return str(value)


def set_user_env(name: str, value: str) -> None:
    """Grava a variavel em HKCU\\Environment e broadcasta a mudanca."""

    import winreg

    access = winreg.KEY_QUERY_VALUE | winreg.KEY_SET_VALUE
    with winreg.CreateKeyEx(
        winreg.HKEY_CURRENT_USER,
        "Environment",
        0,
        access,
    ) as key:
        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)
    broadcast_environment_change()
