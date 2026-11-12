"""Repository rules that are cheaper to enforce than to remember."""

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
NODE_LOCKS = ("package-lock.json", "bun.lock", "pnpm-lock.yaml", "yarn.lock")


def tracked(pattern: str) -> list[Path]:
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", pattern],
                         cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [ROOT / p for p in out.splitlines() if "node_modules" not in p]


def ignored(path: Path) -> bool:
    return subprocess.run(["git", "check-ignore", "-q", str(path)], cwd=ROOT).returncode == 0


@pytest.mark.parametrize("manifest", tracked("*package.json"), ids=lambda p: str(p.parent.relative_to(ROOT)))
def test_every_node_project_has_a_lockfile(manifest):
    locks = [manifest.parent / lock for lock in NODE_LOCKS if (manifest.parent / lock).is_file()]
    assert locks, "run `npm install --package-lock-only` (or `bun install`) and commit the lockfile"
    assert not any(ignored(lock) for lock in locks), f"{locks[0].name} is gitignored, so it can never be committed"


@pytest.mark.parametrize("manifest", tracked("*pyproject.toml"), ids=lambda p: str(p.parent.relative_to(ROOT)))
def test_every_python_project_has_a_uv_lock(manifest):
    lock = manifest.parent / "uv.lock"
    assert lock.is_file(), "run `uv lock` and commit uv.lock"
    assert not ignored(lock), "uv.lock is gitignored, so it can never be committed"


def test_no_old_claude_code_sdk_imports():
    hits = [p for p in tracked("*.ts") if '"@anthropic-ai/claude-code"' in p.read_text(errors="replace")]
    assert hits == [], "import from @anthropic-ai/claude-agent-sdk instead"


def test_no_versioned_model_ids_outside_transcripts_and_locks():
    pattern = r"claude-[0-9a-z-]*(sonnet|opus|haiku)-?[0-9]|\b(sonnet|opus|haiku)[-._][0-9]"
    proc = subprocess.run(
        ["git", "grep", "-nIE", pattern, "--", ".", ":!*.txt", ":!*.lock", ":!*package-lock.json"],
        cwd=ROOT, capture_output=True, text=True)
    assert proc.stdout == "", "use model aliases (see cheat_sheets/model_aliases.md):\n" + proc.stdout
