"""Traducao do atalho de selecao `all` para a taxonomia de markers."""

from __future__ import annotations

import re

_ALIAS = "all"
_EXPANSION = "(unit or integration)"


def translate_all_alias(expression: str | None) -> str | None:
    """Expande o token `all` para `(unit or integration)`.

    Traducao literal de atalho: apenas o token `all` e substituido e a
    expressao volta intacta quando nao contem o atalho. Nenhuma selecao
    alem do que foi pedido e acrescentada ou removida.
    """

    if not expression:
        return expression
    return re.sub(rf"\b{_ALIAS}\b", _EXPANSION, expression)
