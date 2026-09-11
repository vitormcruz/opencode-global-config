"""Requisitos de capacidade do SO declarados nos proprios testes.

O `skipif` e mecanismo da suite: o teste declara a capacidade de que
precisa e a suite nao o executa onde a capacidade nao se aplica. Nao e
licenca para o agente deixar de rodar a suite completa.
"""

import os

import pytest

requires_symlink = pytest.mark.skipif(
    os.name != "posix",
    reason="exige symlink (POSIX)",
)
