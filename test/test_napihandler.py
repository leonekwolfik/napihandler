"""
Tests for napihandler — replicating the scenarios from the GHA workflow.

GHA steps covered:
- "Test binary (hash only)"          → test_download_hash_only
- "Check SRT file"                   → assertion inside each download test
- "Test binary (napiprojekt:hash)"   → test_download_napiprojekt_prefix
- "Test protocol registration"       → test_register_dry_run

Unit tests for parse_id are also included.
"""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SRC = Path(__file__).parent.parent / "src" / "napihandler.py"

# MD5 hash used in the GHA workflow
TEST_HASH = "07a1046ccddd59c0ffc7932331a16d63"


def _load_module():
    """Import napihandler as a module without executing main()."""
    spec = importlib.util.spec_from_file_location("napihandler", SRC)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run(*args, cwd=None):
    """Run napihandler.py with *args and return the CompletedProcess."""
    return subprocess.run(
        [sys.executable, str(SRC), *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


# ---------------------------------------------------------------------------
# Unit tests — parse_id
# ---------------------------------------------------------------------------


class TestParseId:
    """Unit tests for the parse_id helper function."""

    def setup_method(self):
        self.module = _load_module()

    def test_hash_only(self):
        """Plain MD5 hash is accepted and returned as-is (lowercased)."""
        assert self.module.parse_id(TEST_HASH) == TEST_HASH

    def test_napiprojekt_prefix(self):
        """napiprojekt:HASH format is accepted."""
        assert self.module.parse_id(f"napiprojekt:{TEST_HASH}") == TEST_HASH

    def test_napiprojekt_url_format(self):
        """napiprojekt://HASH format is accepted."""
        assert self.module.parse_id(f"napiprojekt://{TEST_HASH}") == TEST_HASH

    def test_uppercase_normalized_to_lowercase(self):
        """Hash is normalised to lowercase regardless of input case."""
        assert self.module.parse_id(TEST_HASH.upper()) == TEST_HASH

    def test_invalid_format_exits(self):
        """Invalid value causes SystemExit with code 1."""
        with pytest.raises(SystemExit) as exc_info:
            self.module.parse_id("not_a_valid_hash")
        assert exc_info.value.code == 1

    def test_too_short_hash_exits(self):
        """Hash that is too short causes SystemExit with code 1."""
        with pytest.raises(SystemExit) as exc_info:
            self.module.parse_id("07a1046c")
        assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# Integration tests — CLI (replicating GHA workflow)
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_download_hash_only(tmp_path):
    """
    Replicates GHA steps 'Test binary (hash only)' + 'Check SRT file'.

    Passes an MD5 hash directly and verifies that an SRT file is created.
    Requires network access to napiprojekt.pl.
    """
    result = _run(TEST_HASH, cwd=str(tmp_path))
    assert result.returncode == 0, (
        f"napihandler exited with code {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    srt_files = list(tmp_path.glob("*.srt"))
    assert len(srt_files) > 0, "Expected at least one SRT file to be created"


@pytest.mark.integration
def test_download_napiprojekt_prefix(tmp_path):
    """
    Replicates GHA steps 'Test binary (napiprojekt:hash)' + 'Check SRT file'.

    Passes the URI in 'napiprojekt:HASH' format and verifies an SRT file is
    created.
    Requires network access to napiprojekt.pl.
    """
    result = _run(f"napiprojekt:{TEST_HASH}", cwd=str(tmp_path))
    assert result.returncode == 0, (
        f"napihandler exited with code {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    srt_files = list(tmp_path.glob("*.srt"))
    assert len(srt_files) > 0, "Expected at least one SRT file to be created"


@pytest.mark.integration
def test_register_dry_run():
    """
    Replicates GHA step 'Test protocol registration'.

    Uses --dry-run so that no system changes are made during the test run.
    """
    result = _run("--register", "--dry-run")
    assert result.returncode == 0, (
        f"napihandler --register --dry-run exited with code {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "OK" in result.stdout, (
        f"Expected 'OK' in output, got:\n{result.stdout}"
    )
