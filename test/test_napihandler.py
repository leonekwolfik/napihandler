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
import io
import subprocess
import sys
from pathlib import Path

import py7zr
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
        """Invalid value raises ValueError."""
        with pytest.raises(ValueError):
            self.module.parse_id("not_a_valid_hash")

    def test_too_short_hash_exits(self):
        """Hash that is too short raises ValueError."""
        with pytest.raises(ValueError):
            self.module.parse_id("07a1046c")


# ---------------------------------------------------------------------------
# Unit tests — extract_subtitles_from_archive
# ---------------------------------------------------------------------------

# Minimal valid SRT content used across extraction tests
_SAMPLE_SRT = (
    b"1\r\n"
    b"00:00:01,000 --> 00:00:03,000\r\n"
    b"Test subtitle line.\r\n"
    b"\r\n"
)


def _make_archive(filename: str, content: bytes) -> bytes:
    """Return bytes of a password-protected 7-zip archive containing a file
    named *filename* with the given *content*."""
    buf = io.BytesIO()
    with py7zr.SevenZipFile(
        buf, mode="w", password="iBlm8NTigvru0Jr0"
    ) as archive:
        archive.writestr(content, filename)
    buf.seek(0)
    return buf.read()


class TestExtractSubtitlesFromArchive:
    """Unit tests for extract_subtitles_from_archive."""

    def setup_method(self):
        self.module = _load_module()

    def test_srt_content_is_extracted_correctly(self):
        """Extracted bytes match the original SRT content placed in the archive."""
        archive_data = _make_archive("film.srt", _SAMPLE_SRT)
        result = self.module.extract_subtitles_from_archive(archive_data)
        assert result == _SAMPLE_SRT

    def test_extracted_content_is_readable_as_text(self):
        """Extracted bytes can be decoded as UTF-8 text and contain SRT markers."""
        archive_data = _make_archive("subtitle.srt", _SAMPLE_SRT)
        result = self.module.extract_subtitles_from_archive(archive_data)
        text = result.decode("utf-8")
        assert "-->" in text, "Expected SRT timestamp separator '-->' in output"

    def test_srt_file_selected_among_multiple_files(self):
        """When the archive contains a non-SRT file first, the .srt file is used."""
        srt_bytes = b"1\r\n00:00:00,000 --> 00:00:01,000\r\nHello\r\n\r\n"
        buf = io.BytesIO()
        with py7zr.SevenZipFile(
            buf, mode="w", password="iBlm8NTigvru0Jr0"
        ) as archive:
            archive.writestr(b"some metadata", "info.txt")
            archive.writestr(srt_bytes, "movie.srt")
        buf.seek(0)
        archive_data = buf.read()
        result = self.module.extract_subtitles_from_archive(archive_data)
        assert result == srt_bytes

    def test_archive_without_srt_exits(self):
        """Archive that contains no .srt file raises RuntimeError."""
        buf = io.BytesIO()
        with py7zr.SevenZipFile(
            buf, mode="w", password="iBlm8NTigvru0Jr0"
        ) as archive:
            archive.writestr(b"data", "nosubtitle.txt")
        buf.seek(0)
        archive_data = buf.read()
        with pytest.raises(RuntimeError):
            self.module.extract_subtitles_from_archive(archive_data)



# ---------------------------------------------------------------------------
# Unit tests — download_subtitle (module API)
# ---------------------------------------------------------------------------


class TestDownloadSubtitle:
    """Unit tests for the download_subtitle public API."""

    def setup_method(self):
        self.module = _load_module()

    def test_invalid_hash_raises_value_error(self, tmp_path):
        """Passing an invalid hash raises ValueError without writing any file."""
        with pytest.raises(ValueError):
            self.module.download_subtitle("not_a_valid_hash", tmp_path)
        assert list(tmp_path.glob("*.srt")) == []

    def test_default_filename_uses_hash_and_language(self, tmp_path, monkeypatch):
        """When filename is None, the output file is named '{hash}_{language}.srt'."""
        film_id = TEST_HASH
        fake_content = b"1\r\n00:00:01,000 --> 00:00:02,000\r\nTest\r\n\r\n"

        monkeypatch.setattr(
            self.module,
            "download_subtitles",
            lambda fid, lang: fake_content,
        )

        result = self.module.download_subtitle(film_id, tmp_path)
        expected = tmp_path / f"{film_id}_PL.srt"
        assert result == expected
        assert expected.read_bytes() == fake_content

    def test_custom_filename_is_used(self, tmp_path, monkeypatch):
        """When filename is provided, that name is used for the output file."""
        fake_content = b"1\r\n00:00:01,000 --> 00:00:02,000\r\nTest\r\n\r\n"

        monkeypatch.setattr(
            self.module,
            "download_subtitles",
            lambda fid, lang: fake_content,
        )

        result = self.module.download_subtitle(TEST_HASH, tmp_path, filename="film.srt")
        expected = tmp_path / "film.srt"
        assert result == expected
        assert expected.read_bytes() == fake_content

    def test_outputdir_is_created_if_missing(self, tmp_path, monkeypatch):
        """The output directory is created automatically when it does not exist."""
        fake_content = b"sub"
        monkeypatch.setattr(
            self.module,
            "download_subtitles",
            lambda fid, lang: fake_content,
        )

        new_dir = tmp_path / "nested" / "dir"
        assert not new_dir.exists()
        result = self.module.download_subtitle(TEST_HASH, new_dir)
        assert new_dir.exists()
        assert result.parent == new_dir

    def test_napiprojekt_uri_format_accepted(self, tmp_path, monkeypatch):
        """napiprojekt:HASH URI format is accepted by the public API."""
        fake_content = b"sub"
        monkeypatch.setattr(
            self.module,
            "download_subtitles",
            lambda fid, lang: fake_content,
        )

        result = self.module.download_subtitle(f"napiprojekt:{TEST_HASH}", tmp_path)
        assert result.name == f"{TEST_HASH}_PL.srt"

    def test_language_parameter_is_forwarded(self, tmp_path, monkeypatch):
        """The language parameter is forwarded to download_subtitles and used in the filename."""
        captured = {}
        fake_content = b"sub"

        def fake_download(fid, lang):
            captured["lang"] = lang
            return fake_content

        monkeypatch.setattr(self.module, "download_subtitles", fake_download)

        result = self.module.download_subtitle(TEST_HASH, tmp_path, language="EN")
        assert captured["lang"] == "EN"
        assert result.name == f"{TEST_HASH}_EN.srt"

    def test_returns_path_object(self, tmp_path, monkeypatch):
        """download_subtitle returns a pathlib.Path instance."""
        import pathlib as _pathlib

        monkeypatch.setattr(
            self.module,
            "download_subtitles",
            lambda fid, lang: b"sub",
        )

        result = self.module.download_subtitle(TEST_HASH, tmp_path)
        assert isinstance(result, _pathlib.Path)


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
