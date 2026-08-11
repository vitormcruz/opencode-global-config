from io import StringIO
from pathlib import Path

import pytest

from opencode_config.bootstrap.detect import (
    DependencyDetection,
    DependencySpec,
    DependencyStatus,
)
from opencode_config.bootstrap.interactive import (
    InteractiveError,
    run_bootstrap,
)
from opencode_config.bootstrap.installers import InstallContext, InstallResult
from opencode_config.lib.environment import EnvironmentKind
from opencode_config.lib.paths import resolve_user_space_paths


class TTYStream(StringIO):
    def isatty(self) -> bool:
        return True


def make_detection(
    name: str,
    *,
    required: bool,
    status: DependencyStatus = DependencyStatus.MISSING,
) -> DependencyDetection:
    spec = DependencySpec(
        name=name,
        commands=(name,),
        install_methods={
            EnvironmentKind.LINUX: f"instalar {name}",
            EnvironmentKind.WSL: f"instalar {name}",
            EnvironmentKind.WINDOWS: f"instalar {name} no Windows",
        },
        required=required,
    )
    return DependencyDetection(
        spec=spec,
        status=status,
        version=None,
        path=None,
        install_method=f"instalar {name}",
    )


def make_context(tmp_path: Path) -> InstallContext:
    return InstallContext(
        environment=EnvironmentKind.LINUX,
        paths=resolve_user_space_paths(
            EnvironmentKind.LINUX,
            home=tmp_path,
        ),
        repo_root=tmp_path,
        profile_path=tmp_path / ".profile",
    )


@pytest.mark.unit
def test_bootstrap_renders_table_and_selects_each_missing_dependency(
    tmp_path: Path,
) -> None:
    detections = (
        make_detection("required-tool", required=True),
        make_detection("optional-tool", required=False),
    )
    input_stream = TTYStream("\nn\n")
    output = TTYStream()
    selected: list[str] = []

    def fake_installer(
        names,
        _context: InstallContext,
    ) -> tuple[InstallResult, ...]:
        selected.extend(names)
        return tuple(
            InstallResult(name=name, success=True, changed=True)
            for name in names
        )

    result = run_bootstrap(
        context=make_context(tmp_path),
        detections=detections,
        input_stream=input_stream,
        output=output,
        installer=fake_installer,
    )

    rendered = output.getvalue()
    assert "nome" in rendered
    assert "required-tool" in rendered
    assert "missing" in rendered
    assert "instalar optional-tool" in rendered
    assert selected == ["required-tool"]
    assert result.selected == ("required-tool",)
    assert rendered.count("```") == 2


@pytest.mark.unit
def test_bootstrap_requires_yes_without_tty() -> None:
    detections = (make_detection("required-tool", required=True),)

    with pytest.raises(InteractiveError, match="--yes"):
        run_bootstrap(
            context=make_context(Path("/tmp")),
            detections=detections,
            input_stream=StringIO(),
            output=StringIO(),
        )


@pytest.mark.unit
def test_bootstrap_with_everything_present_does_not_require_tty(
    tmp_path: Path,
) -> None:
    detections = (
        make_detection(
            "present-tool",
            required=True,
            status=DependencyStatus.PRESENT,
        ),
    )

    result = run_bootstrap(
        context=make_context(tmp_path),
        detections=detections,
        input_stream=StringIO(),
        output=StringIO(),
    )

    assert result.selected == ()
    assert result.install_results == ()


@pytest.mark.unit
def test_bootstrap_detects_using_the_context_environment(
    tmp_path: Path,
) -> None:
    context = make_context(tmp_path)
    observed: dict[str, object] = {}

    def detector(environment, *, env):
        observed["environment"] = environment
        observed["env"] = env
        return ()

    run_bootstrap(
        context=context,
        environment=EnvironmentKind.LINUX,
        detector=detector,
        input_stream=StringIO(),
        output=StringIO(),
    )

    assert observed["environment"] is EnvironmentKind.LINUX
    assert observed["env"] is context.current_environment


@pytest.mark.unit
def test_bootstrap_reinstalls_repo_in_venv_when_global_pytest_is_present(
    tmp_path: Path,
) -> None:
    detections = (
        make_detection(
            "pytest",
            required=False,
            status=DependencyStatus.PRESENT,
        ),
    )
    selected: list[str] = []

    def fake_installer(
        names,
        _context: InstallContext,
    ) -> tuple[InstallResult, ...]:
        selected.extend(names)
        return tuple(
            InstallResult(name=name, success=True, changed=True)
            for name in names
        )

    result = run_bootstrap(
        context=make_context(tmp_path),
        detections=detections,
        assume_yes=True,
        input_stream=StringIO(),
        output=StringIO(),
        installer=fake_installer,
    )

    assert result.selected == ("pytest",)
    assert selected == ["pytest"]


@pytest.mark.unit
def test_bootstrap_yes_selects_all_missing_without_prompt(
    tmp_path: Path,
) -> None:
    detections = (
        make_detection("required-tool", required=True),
        make_detection("optional-tool", required=False),
        make_detection(
            "present-tool",
            required=True,
            status=DependencyStatus.PRESENT,
        ),
    )
    selected: list[str] = []

    def fake_installer(
        names,
        _context: InstallContext,
    ) -> tuple[InstallResult, ...]:
        selected.extend(names)
        return tuple(
            InstallResult(name=name, success=True, changed=True)
            for name in names
        )

    result = run_bootstrap(
        context=make_context(tmp_path),
        detections=detections,
        assume_yes=True,
        input_stream=StringIO(),
        output=StringIO(),
        installer=fake_installer,
    )

    assert selected == ["required-tool", "optional-tool"]
    assert result.selected == ("required-tool", "optional-tool")


@pytest.mark.unit
def test_check_only_does_not_install_and_emits_one_manual_block(
    tmp_path: Path,
) -> None:
    detections = (
        make_detection("required-tool", required=True),
        make_detection("optional-tool", required=False),
    )
    output = StringIO()
    installer_called = False

    def fail_if_called(
        _names,
        _context: InstallContext,
    ) -> tuple[InstallResult, ...]:
        nonlocal installer_called
        installer_called = True
        raise AssertionError("check-only nao pode instalar")

    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    result = run_bootstrap(
        context=make_context(tmp_path),
        detections=detections,
        check_only=True,
        input_stream=StringIO(),
        output=output,
        installer=fail_if_called,
    )
    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    assert result.selected == ()
    assert result.install_results == ()
    assert not installer_called
    assert before == after
    assert output.getvalue().count("```") == 2


@pytest.mark.unit
def test_failed_installation_is_included_in_single_manual_block(
    tmp_path: Path,
) -> None:
    detections = (make_detection("required-tool", required=True),)

    def failing_installer(
        names,
        _context: InstallContext,
    ) -> tuple[InstallResult, ...]:
        return tuple(
            InstallResult(
                name=name,
                success=False,
                changed=False,
                error="falha simulada",
            )
            for name in names
        )

    output = StringIO()
    result = run_bootstrap(
        context=make_context(tmp_path),
        detections=detections,
        assume_yes=True,
        input_stream=StringIO(),
        output=output,
        installer=failing_installer,
    )

    assert not result.install_results[0].success
    assert "instalar required-tool" in output.getvalue()
    assert "falha simulada" in output.getvalue()
    assert output.getvalue().count("```") == 2
