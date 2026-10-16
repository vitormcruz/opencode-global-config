import subprocess

import pytest

from crwl_diagnostics import CrwlTimeoutError, run_crwl


def _timeout_runner(command, **options):
    raise subprocess.TimeoutExpired(
        command,
        options["timeout"],
        output=b"saida parcial em bytes",
        stderr="erro parcial em texto",
    )


@pytest.mark.unit
def test_timeout_diagnosis_explains_memory_pressure_during_deep_crawl():
    with pytest.raises(CrwlTimeoutError) as failure:
        run_crwl(
            "crwl",
            ["http://127.0.0.1:1234/", "--deep-crawl", "bfs"],
            timeout_seconds=180,
            environment={},
            run_process=_timeout_runner,
            memory_usage_reader=lambda: 96.1,
        )

    message = str(failure.value)

    assert "o Crawl4AI não conseguiu concluir o deep-crawl" in message
    assert "Memória utilizada no momento: 96,10%" in message
    assert "limite de 95% usado pelo Crawl4AI" in message
    assert "saida parcial em bytes" in message
    assert "erro parcial em texto" in message
    assert "AÇÃO PARA O AGENTE: avise o humano" in message


@pytest.mark.unit
def test_timeout_diagnosis_does_not_blame_memory_when_usage_is_normal():
    with pytest.raises(CrwlTimeoutError) as failure:
        run_crwl(
            "crwl",
            ["http://127.0.0.1:1234/", "--deep-crawl", "bfs"],
            timeout_seconds=180,
            environment={},
            run_process=_timeout_runner,
            memory_usage_reader=lambda: 62.4,
        )

    message = str(failure.value)

    assert "não há evidência suficiente para atribuir o problema à memória" in message
    assert "forte pressão de memória" not in message
    assert "Memória utilizada no momento: 62,40%" in message


@pytest.mark.unit
def test_timeout_diagnosis_stays_generic_without_deep_crawl():
    with pytest.raises(CrwlTimeoutError) as failure:
        run_crwl(
            "crwl",
            ["http://127.0.0.1:1234/", "-o", "md-fit"],
            timeout_seconds=180,
            environment={},
            run_process=_timeout_runner,
            memory_usage_reader=lambda: 96.1,
        )

    message = str(failure.value)

    assert "não há evidência suficiente para atribuir o problema à memória" in message
    assert "deep-crawl" not in message
