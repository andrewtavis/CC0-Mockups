# SPDX-License-Identifier: GPL-3.0-or-later
import pytest
from unittest.mock import patch, mock_open
from scribe_data.wikidata.query_data import query_data
from scribe_data.utils import check_index_exists


@pytest.fixture
def mock_output_dir(tmp_path):
    """Creates a temporary directory for test outputs."""
    test_output = tmp_path / "test_output"
    test_output.mkdir(parents=True, exist_ok=True)
    return test_output


# Test check_index_exists function
@patch("builtins.input", return_value="o")  # Simulate user choosing 'overwrite'
@patch("scribe_data.utils.Path.unlink")  # Mock file deletion
def test_check_index_exists(mock_unlink, mock_input, tmp_path):
    """Test that check_index_exists deletes existing files when user overwrites."""
    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "english").mkdir(parents=True, exist_ok=True)
    (output_dir / "english/nouns.json").touch()

    result = check_index_exists(str(output_dir), "english", "nouns")
    assert result["proceed"] is True  # Ensure proceed is True
    mock_unlink.assert_called_once()  # Ensure file deletion was attempted


# Case 1: File exists, and user skips (overwrite=False)
@patch("scribe_data.wikidata.query_data.check_index_exists")
@patch("scribe_data.wikidata.query_data.sparql.query")
def test_query_data_skip_existing_file(mock_sparql, mock_check_index, mock_output_dir):
    """Test query_data when an existing file is skipped."""
    # Mock check_index_exists to simulate skipping
    mock_check_index.return_value = {
        "proceed": False,
        "skipped": True,
        "deleted_files": [],
    }

    query_data(
        languages=["english"],
        data_type=["nouns"],
        output_dir=str(mock_output_dir),
        overwrite=False,
    )

    # Ensure no API call was made
    mock_sparql.assert_not_called()


# Case 2: File does not exist, must create and fetch data
@patch("scribe_data.wikidata.query_data.sparql.query")
@patch("scribe_data.wikidata.query_data.check_index_exists")
@patch("builtins.open", new_callable=mock_open)
def test_query_data_fetch_data(
    mock_file_open, mock_check_index, mock_sparql, mock_output_dir
):
    """Test query_data when no file exists and data must be fetched."""
    # Mock check_index_exists to simulate proceeding
    mock_check_index.return_value = {
        "proceed": True,
        "skipped": False,
        "deleted_files": [],
    }

    # Ensure a valid SPARQL query result
    mock_sparql.return_value.convert.return_value = {
        "results": {"bindings": [{"key": {"value": "test_value"}}]}
    }
    mock_sparql.return_value.queryString = (
        "SELECT ?item WHERE { ?item wdt:P31 wd:Q5 }"  # Mock a valid query
    )

    query_data(
        languages=["english"],
        data_type=["nouns"],
        output_dir=str(mock_output_dir),
        overwrite=False,
    )

    # Ensure API was queried and file was written
    mock_sparql.assert_called_once()
    mock_file_open.assert_called()


# Case 3: SPARQL query fails
@patch("scribe_data.wikidata.query_data.sparql.query")
@patch("scribe_data.wikidata.query_data.check_index_exists")
def test_query_data_sparql_failure(mock_check_index, mock_sparql, mock_output_dir):
    """Test query_data when the SPARQL query fails."""
    # Mock check_index_exists to simulate proceeding
    mock_check_index.return_value = {
        "proceed": True,
        "skipped": False,
        "deleted_files": [],
    }

    # Simulate a SPARQL query failure
    mock_sparql.side_effect = Exception("SPARQL query failed")

    with pytest.raises(Exception, match="SPARQL query failed"):
        query_data(
            languages=["english"],
            data_type=["nouns"],
            output_dir=str(mock_output_dir),
            overwrite=False,
        )


# Case 4: Successful query and formatting
@patch("scribe_data.wikidata.query_data.sparql.query")
@patch("scribe_data.wikidata.query_data.check_index_exists")
@patch("scribe_data.wikidata.query_data.execute_formatting_script")
@patch("builtins.open", new_callable=mock_open)
def test_query_data_success(
    mock_file_open, mock_format, mock_check_index, mock_sparql, mock_output_dir
):
    """Test query_data successfully retrieves and formats data."""
    # Mock check_index_exists to simulate proceeding
    mock_check_index.return_value = {
        "proceed": True,
        "skipped": False,
        "deleted_files": [],
    }

    # Mock SPARQL query result
    mock_sparql.return_value.convert.return_value = {
        "results": {"bindings": [{"key": {"value": "test_value"}}]}
    }

    query_data(
        languages=["english"],
        data_type=["nouns"],
        output_dir=str(mock_output_dir),
        overwrite=True,
    )

    # Verify the format script was called
    mock_format.assert_called_with(
        output_dir=str(mock_output_dir), language="english", data_type="nouns"
    )
