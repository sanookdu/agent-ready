"""Thin, capability-constrained subprocess adapters; no provider-specific rubric."""

import json
import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory


class ProviderError(RuntimeError):
    """Provider invocation failed; never substitute an assessment."""


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def _invalid_constant(value):
    raise ValueError("Non-JSON constant")


class _Adapter:
    executable: str
    version: str

    def __init__(self, runner=None):
        self.runner = runner or subprocess.run

    def command(self, runtime: Path) -> list[str]:
        raise NotImplementedError

    def assess(self, prompt: str) -> object:
        # Preserve only explicit runtime/authentication inputs. Never expose them
        # to the model or copy arbitrary tool/config/telemetry environment knobs.
        names = (
            "PATH",
            "HOME",
            "USERPROFILE",
            "SYSTEMROOT",
            "WINDIR",
            "APPDATA",
            "LOCALAPPDATA",
            "TEMP",
            "TMP",
        )
        names += (
            ("CODEX_HOME", "OPENAI_API_KEY", "CODEX_API_KEY")
            if self.executable == "codex"
            else ("ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN")
        )
        env = {name: os.environ[name] for name in names if name in os.environ}
        env.update(
            {
                "DISABLE_TELEMETRY": "1",
                "DISABLE_ERROR_REPORTING": "1",
                "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
            }
        )
        try:
            with TemporaryDirectory(prefix="agent-ready-") as runtime:
                cwd = Path(runtime) / "work"
                cwd.mkdir()
                if self.executable == "codex":
                    # Codex loads global instructions even with ignore-user-config.
                    # Isolate its state; copy only the fixed authentication artifact.
                    original = Path(env.get("CODEX_HOME", str(Path.home() / ".codex")))
                    isolated = Path(runtime) / "codex"
                    isolated.mkdir(mode=0o700)
                    credential = original / "auth.json"
                    if credential.is_file():
                        with credential.open("rb") as stream:
                            auth = stream.read(131073)
                        if len(auth) > 131072:
                            raise ProviderError(
                                "Provider authentication artifact exceeds the size limit."
                            )
                        target = isolated / "auth.json"
                        target.touch(mode=0o600)
                        target.write_bytes(auth)
                    env["CODEX_HOME"] = str(isolated)
                    isolated_home = Path(runtime) / "home"
                    isolated_home.mkdir(mode=0o700)
                    env["HOME"] = str(isolated_home)
                    env["USERPROFILE"] = str(isolated_home)
                options = dict(
                    text=True, encoding="utf-8", capture_output=True, shell=False, cwd=cwd, env=env
                )
                version = self.runner([self.executable, "--version"], timeout=10, **options)
                if version.returncode or version.stdout.strip() != self.version:
                    raise ProviderError(
                        f"Unsupported {self.executable} version; requires {self.version}."
                    )
                result = self.runner(
                    self.command(Path(runtime)), input=prompt, timeout=180, **options
                )
        except FileNotFoundError:
            raise ProviderError(f"{self.executable} is not installed or not on PATH.") from None
        except subprocess.TimeoutExpired:
            raise ProviderError("Analysis provider timed out; no assessment produced.") from None
        except (OSError, UnicodeError):
            raise ProviderError(
                "Analysis provider could not run; no assessment produced."
            ) from None
        if result.returncode:
            raise ProviderError(
                "Analysis provider failed; check local authentication and availability."
            )
        if len(result.stdout) > 1_000_000:
            raise ProviderError("Analysis provider output exceeds the response limit.")
        try:
            return json.loads(
                result.stdout, object_pairs_hook=_unique_object, parse_constant=_invalid_constant
            )
        except (ValueError, RecursionError):
            raise ProviderError("Analysis provider did not return valid JSON.") from None


class CodexAdapter(_Adapter):
    executable = "codex"
    version = "codex-cli 0.153.4"

    def command(self, runtime: Path) -> list[str]:
        args = [
            "codex",
            "exec",
            "--sandbox",
            "read-only",
            "--ignore-user-config",
            "--ignore-rules",
            "--ephemeral",
            "--skip-git-repo-check",
            "--color",
            "never",
        ]
        # A fixed minimal model catalog removes model-dependent patch tools.
        # Tool feature flags alone do not remove apply_patch in this CLI version.
        catalog = Path(runtime) / "model.json"
        catalog.write_text(
            json.dumps(
                {
                    "models": [
                        {
                            "slug": "gpt-5.5",
                            "display_name": "gpt-5.5",
                            "description": "Text-only analysis",
                            "supported_reasoning_levels": [],
                            "shell_type": "disabled",
                            "visibility": "list",
                            "supported_in_api": True,
                            "priority": 0,
                            "base_instructions": "Assess software work using the supplied rubric. No tools are available.",
                            "supports_reasoning_summaries": False,
                            "support_verbosity": False,
                            "truncation_policy": {"mode": "bytes", "limit": 10000},
                            "supports_parallel_tool_calls": False,
                            "experimental_supported_tools": [],
                            "input_modalities": ["text"],
                            "apply_patch_tool_type": None,
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        config = {
            "model": '"gpt-5.5"',
            "model_catalog_json": json.dumps(str(catalog)),
            "approval_policy": '"never"',
            "web_search": '"disabled"',
            "project_doc_max_bytes": "0",
            "analytics.enabled": "false",
            "feedback.enabled": "false",
            "tools.experimental_request_user_input.enabled": "false",
            "features.skip_host_skill_discovery": "true",
        }
        for feature in (
            "shell_tool",
            "unified_exec",
            "view_image",
            "apps",
            "plugins",
            "hooks",
            "memories",
            "multi_agent",
            "multi_agent_v2",
            "image_generation",
            "browser_use",
            "browser_use_external",
            "computer_use",
            "code_mode",
            "code_mode_host",
            "skill_search",
            "skill_mcp_dependency_install",
            "shell_snapshot",
            "workspace_dependencies",
            "tool_suggest",
            "remote_plugin",
        ):
            config["features." + feature] = "false"
        for key, value in config.items():
            args.extend(["-c", key + "=" + value])
        return args + ["-"]


class ClaudeAdapter(_Adapter):
    executable = "claude"
    version = "2.1.258 (Claude Code)"

    def command(self, runtime: Path) -> list[str]:
        return [
            "claude",
            "--print",
            "--output-format",
            "text",
            "--tools",
            "",
            "--safe-mode",
            "--strict-mcp-config",
            "--mcp-config",
            '{"mcpServers":{}}',
            "--setting-sources",
            "",
            "--disable-slash-commands",
            "--no-chrome",
            "--no-session-persistence",
            "--permission-mode",
            "dontAsk",
            "--system-prompt",
            "You assess software work. Follow the Agent Ready rubric supplied in stdin.",
        ]
