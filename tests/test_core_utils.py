# SPDX-License-Identifier: GPL-3.0-or-later
import pytest
from pathlib import Path
from scribe_data.utils import check_index_exists
import tempfile
import shutil


@pytest.fixture
def temp_dir():
    """Fixture to create a temporary directory for testing"""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp)


def test_check_index_exists_no_file(temp_dir, monkeypatch):
    """Test when a file exists and the user chooses NOT to overwrite"""
    output_dir = temp_dir
    language = "german"
    data_type = "prepositions"
    file_path = Path(output_dir) / f"{language}/{data_type}.json"

    # Create a mock file
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.touch()

    # Mock user input for "no"
    monkeypatch.setattr("builtins.input", lambda _: "n")

    result = check_index_exists(output_dir, language, data_type)
    assert (
        result["proceed"] is False
    )  # Should not proceed if user chooses not to overwrite
    assert file_path.exists()  # File should still exist


def test_check_index_exists_with_overwrite(temp_dir, monkeypatch):
    """Test when a file exists and the user chooses to overwrite."""
    output_dir = temp_dir
    language = "german"
    data_type = "prepositions"
    file_path = Path(output_dir) / f"{language}/{data_type}.json"

    # Create a mock file
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.touch()

    # Mock user input to simulate "o" (overwrite)
    monkeypatch.setattr("builtins.input", lambda _: "o")

    result = check_index_exists(output_dir, language, data_type)
    assert result["proceed"] is True  # Should proceed if user agrees to overwrite
    assert not file_path.exists()  # File should be deleted
