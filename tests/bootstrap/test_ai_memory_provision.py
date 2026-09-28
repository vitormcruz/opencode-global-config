"""Testes unitários do provisionamento user-space do ai-memory."""

from __future__ import annotations

from hashlib import sha256
from io import StringIO
import json
from pathlib import Path
import stat
from urllib.error import HTTPError

import pytest

from opencode_config.bootstrap import ai_memory
from opencode_config.bootstrap.installers import InstallContext
from opencode_config.harnesses import HarnessDefinition
from opencode_config.lib.environment import EnvironmentKind
from opencode_config.lib.process import CommandResult
from opencode_config.lib.paths import UserSpacePaths


def make_context(home: Path) -> InstallContext:
    return InstallContext(
        environment=EnvironmentKind.LINUX,
        paths=UserSpacePaths(
            home=home,
            config_dir=home / ".config",
            data_dir=home / ".local" / "share",
            bin_dir=home / ".local" / "bin",
            pipx_bin=home / ".local" / "bin",
            npm_bin=home / ".local" / "bin",
        ),
        current_environment={"PATH": "/usr/bin"},
    )


class FakeAiMemoryRunner:
    def __init__(self, home: Path) -> None:
        self.home = home
        self.commands: list[tuple[str, ...]] = []
        self.image_available = False
        self.network_available = False
        self.network_container_names: list[str] = []
        self.container_available = False
        self.container_running = False
        self.container_host_policy = False
        self.health_statuses = ["healthy"]
        self.health_status: str | None = None
        self.container_starts = True
        self.container_image = ai_memory.AI_MEMORY_IMAGE
        self.published_loopback = False
        self.plugin_content = "generated plugin"
        self.pull_count = 0
        self.hook_environments: list[dict[str, str]] = []

    def __call__(
        self,
        command: list[str],
        *,
        env: dict[str, str],
        timeout: float,
    ) -> CommandResult:
        del timeout
        arguments = tuple(command)
        self.commands.append(arguments)
        docker_arguments = arguments[1:]

        if docker_arguments == ("info",):
            return self._result(arguments, 0)
        if docker_arguments[:2] == ("image", "inspect"):
            return self._result(arguments, 0 if self.image_available else 1)
        if docker_arguments[:2] == ("network", "inspect"):
            network_containers = {
                str(index): {"Name": name}
                for index, name in enumerate(self.network_container_names)
            }
            inspect = (
                f"true|{json.dumps(network_containers)}"
                if len(docker_arguments) > 3
                and docker_arguments[3] == "{{.Internal}}|{{json .Containers}}"
                else "true"
            )
            return self._result(
                arguments,
                0 if self.network_available else 1,
                inspect,
            )
        if docker_arguments[:2] == ("network", "create"):
            self.network_available = True
            return self._result(arguments, 0)
        if docker_arguments[:1] == ("pull",):
            self.image_available = True
            self.pull_count += 1
            return self._result(arguments, 0)
        if docker_arguments[:3] == (
            "inspect",
            "--format",
            "{{json .State}}",
        ):
            if self.health_statuses:
                self.health_status = self.health_statuses.pop(0)
            return self._result(
                arguments,
                0,
                json.dumps(
                    {
                        "Running": self.container_running,
                        "Health": {"Status": self.health_status},
                    }
                ),
            )
        if docker_arguments[:1] == ("inspect",):
            return self._inspect_container(arguments)
        if docker_arguments[:1] == ("run",):
            self.container_available = True
            self.container_running = self.container_starts
            self.container_host_policy = True
            if "ai-memory" not in self.network_container_names:
                self.network_container_names.append("ai-memory")
            return self._result(arguments, 0)
        if docker_arguments[:1] == ("start",):
            self.container_running = True
            return self._result(arguments, 0)
        if docker_arguments[:1] == ("stop",):
            self.container_running = False
            return self._result(arguments, 0)
        if docker_arguments[:1] == ("rm",):
            self.container_available = False
            self.network_container_names = [
                name for name in self.network_container_names if name != "ai-memory"
            ]
            return self._result(arguments, 0)
        if "install-hooks" in arguments:
            self.hook_environments.append(env)
            plugin = self.home / ".config" / "opencode" / "plugins" / "ai-memory.ts"
            plugin.parent.mkdir(parents=True, exist_ok=True)
            plugin.write_text(self.plugin_content, encoding="utf-8")
            return self._result(arguments, 0)
        return self._result(arguments, 0)

    @staticmethod
    def _result(
        arguments: tuple[str, ...],
        returncode: int,
        stdout: str = "",
    ) -> CommandResult:
        return CommandResult(
            args=arguments,
            returncode=returncode,
            stdout=stdout,
            stderr="",
        )

    def _inspect_container(self, arguments: tuple[str, ...]) -> CommandResult:
        if not self.container_available:
            return self._result(arguments, 1, "container not found")
        source = self.home / ".local" / "share" / "ai-memory"
        inspected = {
            "Config": {
                "Image": self.container_image,
                "Labels": (
                    {"opencode-config.ai-memory-host-policy": "bridge-ip"}
                    if self.container_host_policy
                    else {}
                ),
                "Healthcheck": {
                    "Interval": 30_000_000_000,
                    "Timeout": 5_000_000_000,
                    "StartPeriod": 5_000_000_000,
                    "Retries": 3,
                },
            },
            "State": {
                "Running": self.container_running,
                "Health": {
                    "Status": self.health_statuses[0]
                    if self.health_statuses
                    else self.health_status or "healthy"
                },
            },
            "HostConfig": {
                "NetworkMode": ai_memory.AI_MEMORY_NETWORK,
                "PortBindings": {
                    "49374/tcp": [
                        {
                            "HostIp": "127.0.0.1",
                            "HostPort": "49374",
                        }
                    ]
                },
            },
            "Mounts": [
                {
                    "Type": "bind",
                    "Source": str(source),
                    "Destination": "/data",
                }
            ],
            "NetworkSettings": {
                "Ports": {
                    "49374/tcp": (
                        [{"HostIp": "127.0.0.1", "HostPort": "49374"}]
                        if self.published_loopback
                        else None
                    )
                },
                "Networks": {ai_memory.AI_MEMORY_NETWORK: {"IPAddress": "172.30.0.2"}},
            },
        }
        return self._result(arguments, 0, json.dumps(inspected))


@pytest.fixture(autouse=True)
def prevent_real_docker_processes(monkeypatch: pytest.MonkeyPatch) -> None:
    def reject_process(*_args: object, **_kwargs: object) -> None:
        pytest.fail(
            "Teste unitário não pode executar Docker real; injete um runner fake."
        )

    def reject_mcp_get(request, *, timeout: float):
        del timeout
        if request.full_url.endswith("/mcp"):
            raise HTTPError(
                request.full_url,
                405,
                "Method Not Allowed",
                None,
                None,
            )
        pytest.fail("Teste unitário não pode executar requisições HTTP reais.")

    monkeypatch.setattr(ai_memory.subprocess, "Popen", reject_process)
    monkeypatch.setattr(
        ai_memory.urllib.request,
        "urlopen",
        reject_mcp_get,
    )


@pytest.mark.unit
def test_ai_memory_upstream_release_pins_match_reviewed_artifacts() -> None:
    assert ai_memory.AI_MEMORY_WRAPPER_VERSION == "v2.4.1"
    assert ai_memory.AI_MEMORY_WRAPPER_URL == (
        "https://github.com/akitaonrails/ai-memory/releases/download/"
        "v2.4.1/ai-memory-wrapper"
    )
    assert ai_memory.AI_MEMORY_WRAPPER_SHA256 == (
        "49c965a0319dbe9c525d552a9a4c8b3464e5dd278e36d5dc7a03edee8b5502e6"
    )
    assert ai_memory.AI_MEMORY_IMAGE_TAG == "akitaonrails/ai-memory:latest"
    assert ai_memory.AI_MEMORY_IMAGE_MANIFEST_SHA256 == (
        "a626d115e0350afe934954c02c9064d30b708c58316763a9c6674ef5d0c8e3d9"
    )
    assert ai_memory.AI_MEMORY_IMAGE_LINUX_AMD64_SHA256 == (
        "5ce8700b2d0a5243370a544c805f86c32d19aaca2251ecae32d66c09d221ef6e"
    )
    assert ai_memory.AI_MEMORY_IMAGE == (
        "akitaonrails/ai-memory:latest@sha256:"
        "5ce8700b2d0a5243370a544c805f86c32d19aaca2251ecae32d66c09d221ef6e"
    )


@pytest.mark.unit
def test_ai_memory_without_docker_warns_and_cleans_active_hooks(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    context = make_context(tmp_path / "home")
    data_directory = context.paths.data_dir / "ai-memory"
    marker = data_directory / ai_memory.AI_MEMORY_READY_MARKER
    marker.parent.mkdir(parents=True)
    marker.write_text("ready", encoding="utf-8")
    plugin = tmp_path / "home" / ".config" / "opencode" / "plugins" / "ai-memory.ts"
    plugin.parent.mkdir(parents=True)
    plugin.write_text("generated hook", encoding="utf-8")
    legacy_jsonc = context.paths.home / ".config" / "opencode" / "opencode.jsonc"
    legacy_jsonc.parent.mkdir(parents=True, exist_ok=True)
    legacy_jsonc.write_text('{"mcp":{"ai-memory":{}}}', encoding="utf-8")
    active_config = context.paths.home / ".config" / "opencode" / "opencode.json"
    active_config.write_text(
        json.dumps(
            {
                "mcp": {
                    "ai-memory": {"type": "remote", "url": ai_memory.AI_MEMORY_MCP_URL},
                    "user-server": {"type": "remote", "url": "http://localhost"},
                }
            }
        ),
        encoding="utf-8",
    )
    copilot_config = context.paths.home / ".copilot" / "mcp-config.json"
    copilot_config.parent.mkdir(parents=True)
    copilot_config.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "ai-memory": {
                        "type": "http",
                        "url": ai_memory.AI_MEMORY_MCP_URL,
                    },
                    "user-server": {"type": "http", "url": "http://localhost"},
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(ai_memory.shutil, "which", lambda *_args, **_kwargs: None)
    output = StringIO()
    downloads: list[str] = []

    result = ai_memory.provision_ai_memory(
        context,
        fetcher=lambda url, _destination: downloads.append(url),
        output=output,
    )

    assert not result.provisioned
    assert not marker.exists()
    assert not plugin.exists()
    assert not legacy_jsonc.exists()
    disabled_config = json.loads(active_config.read_text(encoding="utf-8"))
    assert "ai-memory" not in disabled_config["mcp"]
    assert "user-server" in disabled_config["mcp"]
    backups = list(
        (context.paths.home / ".config" / "opencode-backup").rglob("opencode.jsonc")
    )
    assert backups
    assert json.loads(copilot_config.read_text(encoding="utf-8"))["mcpServers"] == {
        "user-server": {"type": "http", "url": "http://localhost"}
    }
    assert downloads == []
    assert "Docker" in output.getvalue()
    assert "rootless" in output.getvalue()
    assert "não use sudo" in output.getvalue()
    assert "ai-memory" in output.getvalue()


@pytest.mark.unit
def test_ai_memory_provision_downloads_verified_wrapper_and_restricts_container(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    context = make_context(tmp_path / "home")
    runner = FakeAiMemoryRunner(context.paths.home)
    wrapper_bytes = b"verified wrapper bytes"
    monkeypatch.setattr(
        ai_memory.shutil,
        "which",
        lambda *_args, **_kwargs: "/usr/bin/docker",
    )
    monkeypatch.setattr(
        ai_memory,
        "AI_MEMORY_WRAPPER_SHA256",
        sha256(wrapper_bytes).hexdigest(),
    )
    downloaded: list[str] = []

    def fetcher(url: str, destination: Path) -> None:
        downloaded.append(url)
        destination.write_bytes(wrapper_bytes)

    result = ai_memory.provision_ai_memory(
        context,
        runner=runner,
        fetcher=fetcher,
        port_is_in_use=lambda _host, _port: False,
        output=StringIO(),
    )

    assert result.provisioned
    assert downloaded == [ai_memory.AI_MEMORY_WRAPPER_URL]
    assert downloaded[0].startswith("https://github.com/akitaonrails/")
    assert (context.paths.bin_dir / "ai-memory").read_bytes() == wrapper_bytes
    assert (context.paths.data_dir / "ai-memory").is_dir()
    assert stat.S_IMODE((context.paths.data_dir / "ai-memory").stat().st_mode) == 0o700
    assert (
        context.paths.data_dir / "ai-memory" / ai_memory.AI_MEMORY_READY_MARKER
    ).is_file()
    docker_run = next(command for command in runner.commands if command[1] == "run")
    assert "127.0.0.1:49374:49374" in docker_run
    assert ai_memory.AI_MEMORY_NETWORK in docker_run
    assert "--entrypoint" in docker_run
    assert "/bin/sh" in docker_run
    assert any("AI_MEMORY_ALLOWED_HOSTS" in argument for argument in docker_run)
    assert any("hostname -i" in argument for argument in docker_run)
    assert "opencode-config.ai-memory-host-policy=bridge-ip" in docker_run
    assert "--privileged" not in docker_run
    assert not any("insecure" in argument.lower() for argument in docker_run)
    assert any(
        command[1:3] == ("network", "create") and "--internal" in command
        for command in runner.commands
    )


@pytest.mark.unit
def test_ai_memory_waits_for_container_health_before_endpoint_probe(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    context = make_context(tmp_path / "home")
    runner = FakeAiMemoryRunner(context.paths.home)
    runner.health_statuses = ["starting", "healthy"]
    wrapper_bytes = b"verified wrapper bytes"
    observed_health_statuses: list[str | None] = []
    monkeypatch.setattr(
        ai_memory.shutil,
        "which",
        lambda *_args, **_kwargs: "/usr/bin/docker",
    )
    monkeypatch.setattr(
        ai_memory,
        "AI_MEMORY_WRAPPER_SHA256",
        sha256(wrapper_bytes).hexdigest(),
    )
    monkeypatch.setattr(ai_memory.time, "sleep", lambda _seconds: None)

    def endpoint_is_reachable(_url: str) -> bool:
        observed_health_statuses.append(runner.health_status)
        return runner.health_status == "healthy"

    result = ai_memory.provision_ai_memory(
        context,
        runner=runner,
        fetcher=lambda _url, destination: destination.write_bytes(wrapper_bytes),
        port_is_in_use=lambda _host, _port: False,
        endpoint_is_reachable=endpoint_is_reachable,
        output=StringIO(),
    )

    assert result.provisioned
    assert observed_health_statuses == ["healthy"]


@pytest.mark.unit
def test_ai_memory_uses_internal_bridge_url_when_docker_does_not_publish_loopback(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    context = make_context(tmp_path / "home")
    runner = FakeAiMemoryRunner(context.paths.home)
    expected_url = "http://172.30.0.2:49374/mcp"
    observed_urls: list[str] = []
    wrapper_bytes = b"verified wrapper"
    monkeypatch.setattr(
        ai_memory.shutil,
        "which",
        lambda *_args, **_kwargs: "/usr/bin/docker",
    )
    monkeypatch.setattr(
        ai_memory,
        "AI_MEMORY_WRAPPER_SHA256",
        sha256(wrapper_bytes).hexdigest(),
    )

    result = ai_memory.provision_ai_memory(
        context,
        runner=runner,
        fetcher=lambda _url, destination: destination.write_bytes(wrapper_bytes),
        port_is_in_use=lambda _host, _port: False,
        endpoint_is_reachable=lambda url: observed_urls.append(url) or True,
        output=StringIO(),
    )

    assert result.provisioned
    assert result.mcp_url == expected_url
    assert observed_urls == [expected_url]
    assert runner.hook_environments[0]["AI_MEMORY_SERVER_URL"] == (
        "http://172.30.0.2:49374"
    )
    marker = ai_memory.ai_memory_ready_marker(context.paths)
    assert json.loads(marker.read_text(encoding="utf-8"))["complete"] is True
    url_marker = ai_memory._mcp_url_marker(context.paths)
    assert url_marker.read_text(encoding="utf-8").strip() == expected_url
    assert stat.S_IMODE(url_marker.parent.stat().st_mode) == 0o700
    assert not (
        context.paths.data_dir / "ai-memory" / ai_memory.AI_MEMORY_URL_MARKER
    ).exists()
    assert ai_memory.ai_memory_mcp_url(context.paths.home) == expected_url


@pytest.mark.unit
def test_ai_memory_endpoint_probe_rejects_disallowed_host_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def reject_host(request, *, timeout: float):
        assert request.method == "GET"
        assert request.full_url == "http://172.30.0.2:49374/mcp"
        assert timeout > 0
        raise HTTPError(
            "http://172.30.0.2:49374/mcp",
            403,
            "forbidden host",
            None,
            None,
        )

    monkeypatch.setattr(ai_memory.urllib.request, "urlopen", reject_host)

    assert not ai_memory._endpoint_is_reachable("http://172.30.0.2:49374/mcp")


@pytest.mark.unit
def test_ai_memory_endpoint_probe_accepts_method_not_allowed_from_mcp_get(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def reject_method(_request, *, timeout: float):
        assert timeout > 0
        raise HTTPError(
            "http://172.30.0.2:49374/mcp",
            405,
            "Method Not Allowed",
            None,
            None,
        )

    monkeypatch.setattr(ai_memory.urllib.request, "urlopen", reject_method)

    assert ai_memory._endpoint_is_reachable("http://172.30.0.2:49374/mcp")


@pytest.mark.unit
def test_ai_memory_does_not_adopt_existing_container_without_bridge_host_policy(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    context = make_context(tmp_path / "home")
    runner = FakeAiMemoryRunner(context.paths.home)
    runner.network_available = True
    runner.container_available = True
    runner.container_running = True
    data_directory = context.paths.data_dir / "ai-memory"
    data_directory.mkdir(parents=True)
    user_data = data_directory / "memory.sqlite"
    user_data.write_bytes(b"pilot data")
    monkeypatch.setattr(
        ai_memory.shutil,
        "which",
        lambda *_args, **_kwargs: "/usr/bin/docker",
    )

    result = ai_memory.provision_ai_memory(
        context,
        runner=runner,
        output=StringIO(),
    )

    assert not result.provisioned
    assert runner.container_running
    assert user_data.read_bytes() == b"pilot data"
    assert not any("install-hooks" in command for command in runner.commands)
    assert "preserve o volume" in result.message.lower()


@pytest.mark.unit
def test_ai_memory_does_not_enable_mcp_when_internal_endpoint_is_unreachable(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    context = make_context(tmp_path / "home")
    runner = FakeAiMemoryRunner(context.paths.home)
    wrapper_bytes = b"verified wrapper"
    monkeypatch.setattr(
        ai_memory.shutil,
        "which",
        lambda *_args, **_kwargs: "/usr/bin/docker",
    )
    monkeypatch.setattr(
        ai_memory,
        "AI_MEMORY_WRAPPER_SHA256",
        sha256(wrapper_bytes).hexdigest(),
    )

    result = ai_memory.provision_ai_memory(
        context,
        runner=runner,
        fetcher=lambda _url, destination: destination.write_bytes(wrapper_bytes),
        port_is_in_use=lambda _host, _port: False,
        endpoint_is_reachable=lambda _url: False,
        output=StringIO(),
    )

    assert not result.provisioned
    assert not ai_memory.ai_memory_ready_marker(context.paths).exists()
    assert "não está acessível pelo host" in result.message


@pytest.mark.unit
def test_ai_memory_falls_back_to_bridge_when_reported_loopback_is_unreachable(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    context = make_context(tmp_path / "home")
    runner = FakeAiMemoryRunner(context.paths.home)
    runner.published_loopback = True
    bridge_url = "http://172.30.0.2:49374/mcp"
    probed_urls: list[str] = []
    wrapper_bytes = b"verified wrapper"
    monkeypatch.setattr(
        ai_memory.shutil,
        "which",
        lambda *_args, **_kwargs: "/usr/bin/docker",
    )
    monkeypatch.setattr(
        ai_memory,
        "AI_MEMORY_WRAPPER_SHA256",
        sha256(wrapper_bytes).hexdigest(),
    )

    result = ai_memory.provision_ai_memory(
        context,
        runner=runner,
        fetcher=lambda _url, destination: destination.write_bytes(wrapper_bytes),
        port_is_in_use=lambda _host, _port: False,
        endpoint_is_reachable=lambda url: probed_urls.append(url) or url == bridge_url,
        output=StringIO(),
    )

    assert result.provisioned
    assert result.mcp_url == bridge_url
    assert probed_urls == [ai_memory.AI_MEMORY_MCP_URL, bridge_url]


@pytest.mark.unit
def test_ai_memory_windows_verifies_both_user_space_wrapper_assets(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    bin_directory = home / "AppData" / "Local" / "opencode-config" / "bin"
    context = InstallContext(
        environment=EnvironmentKind.WINDOWS,
        paths=UserSpacePaths(
            home=home,
            config_dir=home / "AppData" / "Roaming",
            data_dir=home / "AppData" / "Local",
            bin_dir=bin_directory,
            pipx_bin=home / ".local" / "bin",
            npm_bin=home / "AppData" / "Roaming" / "npm",
        ),
        current_environment={"PATH": "C:/Windows/System32"},
    )
    runner = FakeAiMemoryRunner(home)
    asset_contents = {
        "ai-memory-wrapper.cmd": b"verified command wrapper",
        "ai-memory-wrapper.ps1": b"verified PowerShell wrapper",
    }
    expected_assets = tuple(
        (name, sha256(asset_contents[name]).hexdigest())
        for name, _expected in ai_memory.AI_MEMORY_WINDOWS_WRAPPERS
    )
    monkeypatch.setattr(ai_memory, "AI_MEMORY_WINDOWS_WRAPPERS", expected_assets)
    monkeypatch.setattr(
        ai_memory.shutil,
        "which",
        lambda name, **_kwargs: (
            "C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"
            if name == "powershell.exe"
            else "C:/Program Files/Docker/docker.exe"
        ),
    )
    downloads: list[str] = []

    def fetcher(url: str, destination: Path) -> None:
        asset_name = url.rsplit("/", maxsplit=1)[-1]
        downloads.append(url)
        destination.write_bytes(asset_contents[asset_name])

    result = ai_memory.provision_ai_memory(
        context,
        runner=runner,
        fetcher=fetcher,
        port_is_in_use=lambda _host, _port: False,
        output=StringIO(),
    )

    assert result.provisioned
    assert len(downloads) == 2
    assert all(url.startswith("https://github.com/akitaonrails/") for url in downloads)
    for asset_name, contents in asset_contents.items():
        assert (bin_directory / asset_name).read_bytes() == contents
    expected_state_marker = (
        home / ".local" / "state" / "ai-memory" / ai_memory.AI_MEMORY_URL_MARKER
    )
    assert ai_memory._mcp_url_marker(context.paths) == expected_state_marker
    assert ai_memory.ai_memory_mcp_url(home) == result.mcp_url
    assert any(
        "powershell.exe" in argument
        for command in runner.commands
        for argument in command
    )


@pytest.mark.unit
def test_ai_memory_second_run_does_not_download_or_pull_again(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    context = make_context(tmp_path / "home")
    runner = FakeAiMemoryRunner(context.paths.home)
    wrapper_bytes = b"verified wrapper bytes"
    monkeypatch.setattr(
        ai_memory.shutil,
        "which",
        lambda *_args, **_kwargs: "/usr/bin/docker",
    )
    monkeypatch.setattr(
        ai_memory,
        "AI_MEMORY_WRAPPER_SHA256",
        sha256(wrapper_bytes).hexdigest(),
    )
    downloads: list[str] = []

    def fetcher(url: str, destination: Path) -> None:
        downloads.append(url)
        destination.write_bytes(wrapper_bytes)

    first = ai_memory.provision_ai_memory(
        context,
        runner=runner,
        fetcher=fetcher,
        port_is_in_use=lambda _host, _port: False,
        output=StringIO(),
    )
    command_count = len(runner.commands)
    second = ai_memory.provision_ai_memory(
        context,
        runner=runner,
        fetcher=fetcher,
        port_is_in_use=lambda _host, _port: False,
        output=StringIO(),
    )

    assert first.provisioned and second.provisioned
    assert downloads == [ai_memory.AI_MEMORY_WRAPPER_URL]
    assert runner.pull_count == 1
    assert len(runner.commands) == command_count + 6
    assert sum("install-hooks" in command for command in runner.commands) == 2


@pytest.mark.unit
def test_ai_memory_download_hash_mismatch_blocks_installation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    context = make_context(tmp_path / "home")
    runner = FakeAiMemoryRunner(context.paths.home)
    monkeypatch.setattr(
        ai_memory.shutil, "which", lambda *_args, **_kwargs: "/usr/bin/docker"
    )
    monkeypatch.setattr(ai_memory, "AI_MEMORY_WRAPPER_SHA256", "0" * 64)

    result = ai_memory.provision_ai_memory(
        context,
        runner=runner,
        fetcher=lambda _url, destination: destination.write_bytes(b"untrusted"),
        port_is_in_use=lambda _host, _port: False,
        output=StringIO(),
    )

    assert not result.provisioned
    assert not (context.paths.bin_dir / "ai-memory").exists()
    assert not (
        context.paths.data_dir / "ai-memory" / ai_memory.AI_MEMORY_READY_MARKER
    ).exists()
    assert "SHA256" in result.message


@pytest.mark.unit
def test_ai_memory_existing_wrapper_drift_requires_explicit_upgrade(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    context = make_context(tmp_path / "home")
    runner = FakeAiMemoryRunner(context.paths.home)
    existing_wrapper = context.paths.bin_dir / "ai-memory"
    existing_wrapper.parent.mkdir(parents=True)
    existing_wrapper.write_bytes(b"previous wrapper")
    monkeypatch.setattr(
        ai_memory.shutil,
        "which",
        lambda *_args, **_kwargs: "/usr/bin/docker",
    )
    monkeypatch.setattr(ai_memory, "AI_MEMORY_WRAPPER_SHA256", "0" * 64)
    downloads: list[str] = []

    result = ai_memory.provision_ai_memory(
        context,
        runner=runner,
        fetcher=lambda url, _destination: downloads.append(url),
        port_is_in_use=lambda _host, _port: False,
        output=StringIO(),
    )

    assert not result.provisioned
    assert existing_wrapper.read_bytes() == b"previous wrapper"
    assert downloads == []
    assert "backup" in result.message.lower()
    assert "reexecute" in result.message.lower()


@pytest.mark.unit
def test_ai_memory_occupied_loopback_port_aborts_before_container_creation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    context = make_context(tmp_path / "home")
    runner = FakeAiMemoryRunner(context.paths.home)
    monkeypatch.setattr(
        ai_memory.shutil,
        "which",
        lambda *_args, **_kwargs: "/usr/bin/docker",
    )

    result = ai_memory.provision_ai_memory(
        context,
        runner=runner,
        fetcher=lambda _url, destination: destination.write_bytes(b"wrapper"),
        port_is_in_use=lambda _host, _port: True,
        output=StringIO(),
    )

    assert not result.provisioned
    assert not runner.container_available
    assert "49374" in result.message
    assert "ai-memory" in result.message


@pytest.mark.unit
def test_ai_memory_refuses_internal_network_shared_with_another_container(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    context = make_context(tmp_path / "home")
    runner = FakeAiMemoryRunner(context.paths.home)
    runner.network_available = True
    runner.network_container_names = ["other-service"]
    monkeypatch.setattr(
        ai_memory.shutil,
        "which",
        lambda *_args, **_kwargs: "/usr/bin/docker",
    )
    downloads: list[str] = []

    result = ai_memory.provision_ai_memory(
        context,
        runner=runner,
        fetcher=lambda url, _destination: downloads.append(url),
        port_is_in_use=lambda _host, _port: False,
        output=StringIO(),
    )

    assert not result.provisioned
    assert not runner.container_available
    assert downloads == []
    assert "outro container" in result.message


@pytest.mark.unit
def test_ai_memory_plugin_hash_drift_is_reported(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    context = make_context(tmp_path / "home")
    plugin = context.paths.home / ".config" / "opencode" / "plugins" / "ai-memory.ts"
    plugin.parent.mkdir(parents=True)
    plugin.write_text("plugin before regeneration", encoding="utf-8")
    runner = FakeAiMemoryRunner(context.paths.home)
    runner.plugin_content = "plugin after regeneration"
    wrapper_bytes = b"verified wrapper bytes"
    monkeypatch.setattr(
        ai_memory.shutil,
        "which",
        lambda *_args, **_kwargs: "/usr/bin/docker",
    )
    monkeypatch.setattr(
        ai_memory,
        "AI_MEMORY_WRAPPER_SHA256",
        sha256(wrapper_bytes).hexdigest(),
    )
    output = StringIO()

    result = ai_memory.provision_ai_memory(
        context,
        runner=runner,
        fetcher=lambda _url, destination: destination.write_bytes(wrapper_bytes),
        port_is_in_use=lambda _host, _port: False,
        output=output,
    )

    assert result.provisioned
    assert "AVISO" in output.getvalue()
    assert "ai-memory.ts" in output.getvalue()


@pytest.mark.unit
def test_ai_memory_does_not_enable_mcp_when_container_exits_on_start(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    context = make_context(tmp_path / "home")
    runner = FakeAiMemoryRunner(context.paths.home)
    runner.container_starts = False
    wrapper_bytes = b"verified wrapper bytes"
    monkeypatch.setattr(
        ai_memory.shutil,
        "which",
        lambda *_args, **_kwargs: "/usr/bin/docker",
    )
    monkeypatch.setattr(
        ai_memory,
        "AI_MEMORY_WRAPPER_SHA256",
        sha256(wrapper_bytes).hexdigest(),
    )

    result = ai_memory.provision_ai_memory(
        context,
        runner=runner,
        fetcher=lambda _url, destination: destination.write_bytes(wrapper_bytes),
        port_is_in_use=lambda _host, _port: False,
        output=StringIO(),
    )

    assert not result.provisioned
    assert not ai_memory.ai_memory_ready_marker(context.paths).exists()
    assert not any("install-hooks" in command for command in runner.commands)


@pytest.mark.unit
def test_ai_memory_rejects_container_with_an_untrusted_image(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    context = make_context(tmp_path / "home")
    runner = FakeAiMemoryRunner(context.paths.home)
    runner.network_available = True
    runner.container_available = True
    runner.container_running = True
    runner.container_image = "example/other:latest"
    wrapper_bytes = b"verified wrapper bytes"
    monkeypatch.setattr(
        ai_memory.shutil,
        "which",
        lambda *_args, **_kwargs: "/usr/bin/docker",
    )
    monkeypatch.setattr(
        ai_memory,
        "AI_MEMORY_WRAPPER_SHA256",
        sha256(wrapper_bytes).hexdigest(),
    )

    result = ai_memory.provision_ai_memory(
        context,
        runner=runner,
        fetcher=lambda _url, destination: destination.write_bytes(wrapper_bytes),
        output=StringIO(),
    )

    assert not result.provisioned
    assert "image" in result.message.lower()
    assert not ai_memory.ai_memory_ready_marker(context.paths).exists()
    assert not any("install-hooks" in command for command in runner.commands)


@pytest.mark.unit
def test_streaming_command_forwards_incremental_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakePipe:
        def __init__(self) -> None:
            self.characters = iter("pulling layer\n")
            self.closed = False

        def read(self, _size: int) -> str:
            return next(self.characters, "")

        def close(self) -> None:
            self.closed = True

    class FakeProcess:
        def __init__(self) -> None:
            self.stdout = FakePipe()

        def poll(self) -> int:
            return 0

        def wait(self) -> int:
            return 0

    process = FakeProcess()
    monkeypatch.setattr(
        ai_memory.subprocess,
        "Popen",
        lambda *_args, **_kwargs: process,
    )
    output = StringIO()

    result = ai_memory.run_streaming_command(
        ["docker", "pull", ai_memory.AI_MEMORY_IMAGE],
        env={},
        timeout=10,
        output=output,
    )

    assert result.succeeded
    assert result.stdout == "pulling layer\n"
    assert output.getvalue() == "pulling layer\n"
    assert process.stdout.closed


@pytest.mark.unit
def test_ai_memory_security_spec_and_adr_declare_executable_assertions(
    repo_root: Path,
) -> None:
    security_spec = (repo_root / "docs" / "specs" / "Seguranca.md").read_text(
        encoding="utf-8"
    )
    adr_paths = list((repo_root / "docs" / "adr").glob("0008-*.md"))

    assert len(adr_paths) == 1
    adr = adr_paths[0].read_text(encoding="utf-8")
    fixture = repo_root / "src" / "test" / "groovy" / "Adr0008Fixture.groovy"
    build = (repo_root / "build.gradle").read_text(encoding="utf-8")
    for requirement in [*(f"SEC-{number:02d}" for number in range(1, 12)), "SEC-21"]:
        assert requirement in security_spec
    assert "#execute=verificarSec01()" in security_spec
    assert "Asserções executáveis" in adr
    assert "executarVerificacoes()" in adr
    assert fixture.is_file()
    assert "Adr0008Fixture" in build


@pytest.mark.unit
def test_ai_memory_rollback_removes_runtime_but_preserves_data(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    context = make_context(tmp_path / "home")
    runner = FakeAiMemoryRunner(context.paths.home)
    runner.image_available = True
    runner.network_available = True
    runner.container_available = True
    runner.container_running = True
    data_directory = context.paths.data_dir / "ai-memory"
    data_directory.mkdir(parents=True)
    (data_directory / "memory.sqlite").write_text("preserved", encoding="utf-8")
    marker = data_directory / ai_memory.AI_MEMORY_READY_MARKER
    marker.write_text(
        json.dumps({"complete": True, "network_created": True}),
        encoding="utf-8",
    )
    wrapper = context.paths.bin_dir / "ai-memory"
    wrapper.parent.mkdir(parents=True)
    wrapper.write_text("wrapper", encoding="utf-8")
    plugin = context.paths.home / ".config" / "opencode" / "plugins" / "ai-memory.ts"
    plugin.parent.mkdir(parents=True)
    plugin.write_text("generated hook", encoding="utf-8")
    open_code_config = context.paths.home / ".config" / "opencode" / "opencode.json"
    open_code_config.write_text(
        json.dumps(
            {
                "mcp": {
                    "ai-memory": {"type": "remote", "url": ai_memory.AI_MEMORY_MCP_URL},
                    "user-server": {"type": "remote", "url": "http://localhost"},
                }
            }
        ),
        encoding="utf-8",
    )
    copilot_config = context.paths.home / ".copilot" / "mcp-config.json"
    copilot_config.parent.mkdir(parents=True)
    copilot_config.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "ai-memory": {"type": "http", "url": ai_memory.AI_MEMORY_MCP_URL},
                    "user-server": {"type": "http", "url": "http://localhost"},
                }
            }
        ),
        encoding="utf-8",
    )
    legacy_backup = (
        context.paths.home
        / ".config"
        / "opencode-backup"
        / "20260927-000000"
        / "opencode.jsonc"
    )
    legacy_backup.parent.mkdir(parents=True)
    legacy_backup.write_text('{"user":true}', encoding="utf-8")
    monkeypatch.setattr(
        ai_memory.shutil, "which", lambda *_args, **_kwargs: "/usr/bin/docker"
    )

    result = ai_memory.rollback_ai_memory(
        context,
        runner=runner,
        output=StringIO(),
    )

    assert not result.provisioned
    assert not result.failed
    assert not marker.exists()
    assert not runner.container_available
    assert not wrapper.exists()
    assert not plugin.exists()
    assert json.loads(open_code_config.read_text(encoding="utf-8"))["mcp"] == {
        "user-server": {"type": "remote", "url": "http://localhost"}
    }
    assert json.loads(copilot_config.read_text(encoding="utf-8"))["mcpServers"] == {
        "user-server": {"type": "http", "url": "http://localhost"}
    }
    restored_jsonc = context.paths.home / ".config" / "opencode" / "opencode.jsonc"
    assert restored_jsonc.read_text(encoding="utf-8") == '{"user":true}'
    assert (data_directory / "memory.sqlite").read_text(encoding="utf-8") == "preserved"
    assert sum(command[1:2] == ("stop",) for command in runner.commands) == 1
    assert sum(command[1:2] == ("rm",) for command in runner.commands) == 1
    assert sum(command[1:3] == ("network", "rm") for command in runner.commands) == 1


@pytest.mark.unit
def test_ai_memory_rollback_removes_the_recorded_internal_bridge_endpoint(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    context = make_context(tmp_path / "home")
    runner = FakeAiMemoryRunner(context.paths.home)
    runner.network_available = True
    runner.container_available = True
    runner.container_running = True
    bridge_url = "http://172.30.0.2:49374/mcp"
    data_directory = context.paths.data_dir / "ai-memory"
    data_directory.mkdir(parents=True)
    marker = data_directory / ai_memory.AI_MEMORY_READY_MARKER
    marker.write_text(
        json.dumps(
            {
                "complete": True,
                "network_created": True,
            }
        ),
        encoding="utf-8",
    )
    url_marker = data_directory / ai_memory.AI_MEMORY_URL_MARKER
    url_marker.write_text(f"{bridge_url}\n", encoding="utf-8")
    copilot_config = context.paths.home / ".copilot" / "mcp-config.json"
    copilot_config.parent.mkdir(parents=True)
    copilot_config.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "ai-memory": {"type": "http", "url": bridge_url},
                    "user-server": {"type": "http", "url": "http://localhost"},
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        ai_memory.shutil,
        "which",
        lambda *_args, **_kwargs: "/usr/bin/docker",
    )

    result = ai_memory.rollback_ai_memory(
        context,
        runner=runner,
        output=StringIO(),
    )

    assert result.previous_mcp_url == bridge_url
    assert not url_marker.exists()
    assert json.loads(copilot_config.read_text(encoding="utf-8"))["mcpServers"] == {
        "user-server": {"type": "http", "url": "http://localhost"}
    }
    assert data_directory.is_dir()


@pytest.mark.parametrize("provisioned", [False, True])
@pytest.mark.unit
def test_bootstrap_passes_one_ai_memory_state_to_both_harnesses(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    provisioned: bool,
) -> None:
    from types import SimpleNamespace

    from opencode_config.bootstrap import main as bootstrap_main

    home = tmp_path / "home"
    context = make_context(home)
    repository = tmp_path / "repository"
    canonical_config = repository / "harness-conf" / "opencode.json"
    canonical_config.parent.mkdir(parents=True)
    canonical_config.write_text(
        json.dumps(
            {
                "mcp": {
                    "ai-memory": {
                        "type": "remote",
                        "url": ai_memory.AI_MEMORY_MCP_URL,
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    applied: dict[str, bool | None] = {}

    class RecordingHarness:
        def __init__(self, name: str) -> None:
            self.name = name

        def installed(self, _environment: EnvironmentKind) -> bool:
            return True

        def apply(self, _repository: Path, options) -> None:
            applied[self.name] = options.ai_memory_enabled

    adapters = [RecordingHarness("opencode"), RecordingHarness("copilot")]
    definitions = [
        HarnessDefinition(
            name=adapter.name,
            create=lambda _environment, selected=adapter: selected,
            skip_variable=f"OPENCODE_SKIP_{adapter.name.upper()}_ADAPTER",
        )
        for adapter in adapters
    ]
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.delenv("OPENCODE_SKIP_DEPS", raising=False)
    monkeypatch.setattr(
        bootstrap_main,
        "detect_environment",
        lambda: EnvironmentKind.LINUX,
    )
    monkeypatch.setattr(
        bootstrap_main,
        "_context_for",
        lambda *_args, **_kwargs: context,
    )
    monkeypatch.setattr(bootstrap_main, "_default_repo_root", lambda: repository)
    monkeypatch.setattr(
        bootstrap_main,
        "selecionar_harnesses",
        lambda _selection: definitions,
    )
    monkeypatch.setattr(
        bootstrap_main,
        "run_bootstrap",
        lambda **_kwargs: SimpleNamespace(install_results=()),
    )
    monkeypatch.setattr(
        ai_memory.shutil,
        "which",
        lambda *_args, **_kwargs: "/usr/bin/docker" if provisioned else None,
    )
    if provisioned:
        monkeypatch.setattr(
            bootstrap_main,
            "provision_ai_memory",
            lambda *_args, **_kwargs: ai_memory.AiMemoryProvisionResult(
                True,
                True,
                "ready",
            ),
        )

    status = bootstrap_main.run(
        ["--yes", "--repo-root", str(repository)],
        output=StringIO(),
        error=StringIO(),
    )

    assert status == 0
    assert applied == {"opencode": provisioned, "copilot": provisioned}


@pytest.mark.unit
def test_bootstrap_passes_current_and_previous_mcp_urls_to_harnesses(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from opencode_config.bootstrap import main as bootstrap_main

    current_url = "http://172.30.0.3:49374/mcp"
    previous_url = "http://172.30.0.2:49374/mcp"
    received: list[tuple[str | None, str | None]] = []

    class RecordingHarness:
        name = "opencode"

        def installed(self, _environment: EnvironmentKind) -> bool:
            return True

        def apply(self, _repository: Path, options) -> None:
            received.append((options.ai_memory_url, options.previous_ai_memory_url))

    adapter = RecordingHarness()
    definition = HarnessDefinition(
        name=adapter.name,
        create=lambda _environment: adapter,
        skip_variable="OPENCODE_SKIP_OPENCODE_ADAPTER",
    )
    monkeypatch.setattr(
        bootstrap_main,
        "selecionar_harnesses",
        lambda _selection: [definition],
    )

    result = bootstrap_main._apply_harnesses(
        EnvironmentKind.LINUX,
        tmp_path / "repo",
        None,
        assume_yes=True,
        quiet=True,
        output=StringIO(),
        error=StringIO(),
        ai_memory_enabled=True,
        ai_memory_url=current_url,
        previous_ai_memory_url=previous_url,
    )

    assert result == 0
    assert received == [(current_url, previous_url)]


@pytest.mark.unit
def test_bootstrap_rollback_flag_skips_dependency_install_and_updates_both_harnesses(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from opencode_config.bootstrap import main as bootstrap_main

    home = tmp_path / "home"
    context = make_context(home)
    repository = tmp_path / "repository"
    applied: dict[str, bool | None] = {}
    rollback_contexts: list[InstallContext] = []

    class RecordingHarness:
        def __init__(self, name: str) -> None:
            self.name = name

        def installed(self, _environment: EnvironmentKind) -> bool:
            return True

        def apply(self, _repository: Path, options) -> None:
            applied[self.name] = options.ai_memory_enabled

    adapters = [RecordingHarness("opencode"), RecordingHarness("copilot")]
    definitions = [
        HarnessDefinition(
            name=adapter.name,
            create=lambda _environment, selected=adapter: selected,
            skip_variable=f"OPENCODE_SKIP_{adapter.name.upper()}_ADAPTER",
        )
        for adapter in adapters
    ]
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setattr(
        bootstrap_main,
        "detect_environment",
        lambda: EnvironmentKind.LINUX,
    )
    monkeypatch.setattr(
        bootstrap_main,
        "_context_for",
        lambda *_args, **_kwargs: context,
    )
    monkeypatch.setattr(bootstrap_main, "_default_repo_root", lambda: repository)
    monkeypatch.setattr(
        bootstrap_main,
        "selecionar_harnesses",
        lambda _selection: definitions,
    )
    monkeypatch.setattr(
        bootstrap_main,
        "run_bootstrap",
        lambda **_kwargs: pytest.fail("rollback não deve instalar dependências"),
    )
    monkeypatch.setattr(
        bootstrap_main,
        "rollback_ai_memory",
        lambda selected, **_kwargs: (
            rollback_contexts.append(selected)
            or ai_memory.AiMemoryProvisionResult(False, True, "rollback concluído")
        ),
    )

    status = bootstrap_main.run(
        ["--rollback-ai-memory"],
        output=StringIO(),
        error=StringIO(),
    )

    assert status == 0
    assert rollback_contexts == [context]
    assert applied == {"opencode": False, "copilot": False}
