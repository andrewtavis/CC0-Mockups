# SPDX-License-Identifier: GPL-3.0-or-later
"""
Tests for the CLI get functionality.
"""

import unittest
from unittest.mock import patch

from scribe_data.cli.get import get_data


class TestGetData(unittest.TestCase):
    """
    Unit tests for the get_data function.

    These tests ensure the correct behavior of the get_data function.
    """

    # MARK: Subprocess Patching

    @patch("scribe_data.cli.get.generate_emoji")
    def test_get_emoji_keywords(self, generate_emoji):
        """
        Test the generation of emoji keywords.

        This test ensures that when the `data_type` is `emoji_keywords`, the `generate_emoji` function is called with the correct arguments.
        """
        get_data(
            language="English", data_type="emoji_keywords", output_dir="./test_output"
        )
        generate_emoji.assert_called_once_with(
            language="English",
            output_dir="./test_output",
        )

    # MARK: Invalid Arguments

    def test_invalid_arguments(self):
        """
        Test the behavior of the get_data function when invalid arguments are provided.
        """
        with self.assertRaises(ValueError):
            get_data(all_bool=False)

    # MARK: All Data

    @patch("scribe_data.cli.get.query_data")
    @patch("scribe_data.cli.get.parse_wd_lexeme_dump")
    @patch("scribe_data.cli.get.questionary.confirm")
    def test_get_all_data_types_for_language_user_says_no(
        self, mock_questionary_confirm, mock_parse, mock_query_data
    ):
        """
        Test the behavior when the user agrees to use Wikidata lexeme dumps.

        This test checks that `parse_wd_lexeme_dump` is called with the correct parameters
        when the user confirms they don't want to query Wikidata.
        """
        mock_questionary_confirm.return_value.ask.return_value = False

        get_data(all_bool=True, language="English")

        mock_parse.assert_called_once_with(
            language="English",
            wikidata_dump_type=["form"],
            data_types="all",  # because if only language given, data_types is None
            type_output_dir="scribe_data_json_export",  # default for JSON
            wikidata_dump_path=None,  # explicitly set to None
            overwrite_all=False,
        )
        mock_query_data.assert_not_called()

    @patch("scribe_data.cli.get.parse_wd_lexeme_dump")
    def test_get_all_languages_and_data_types(self, mock_parse):
        """
        Test retrieving all languages for a specific data type.

        Ensures that `query_data` is called properly when `--all` flag is used with a data type.
        """
        get_data(all_bool=True)

        mock_parse.assert_called_once_with(
            language="all",
            wikidata_dump_type=["form", "translations"],
            data_types="all",
            type_output_dir="scribe_data_json_export",
            wikidata_dump_path=None,
            overwrite_all=False,
        )

    # MARK: Language and Data Type

    @patch("scribe_data.cli.get.query_data")
    @patch("scribe_data.cli.get.check_index_exists")
    def test_get_specific_language_and_data_type(
        self, mock_check_index, mock_query_data
    ):
        """
        Test retrieving a specific language and data type.

        Ensures that `query_data` is called properly when a specific language and data type are provided.
        """
        mock_check_index.return_value = {"proceed": True}
        get_data(language="german", data_type="nouns", output_dir="./test_output")
        mock_query_data.assert_called_once_with(
            languages=["german"],
            data_type=["nouns"],
            output_dir="./test_output",
            overwrite=False,
            interactive=False,
        )

    # MARK: Capitalized Language

    @patch("scribe_data.cli.get.query_data")
    @patch("scribe_data.cli.get.check_index_exists")
    def test_get_data_with_capitalized_language(
        self, mock_check_index, mock_query_data
    ):
        """
        Test retrieving data with a capitalized language.

        Ensures that `query_data` is called properly when a capitalized language is provided.
        """
        mock_check_index.return_value = {"proceed": True}
        get_data(language="German", data_type="nouns")
        mock_query_data.assert_called_once_with(
            languages=["German"],
            data_type=["nouns"],
            output_dir="scribe_data_json_export",
            overwrite=False,
            interactive=False,
        )

    # MARK: Lowercase Language

    @patch("scribe_data.cli.get.query_data")
    @patch("scribe_data.cli.get.check_index_exists")
    def test_get_data_with_lowercase_language(self, mock_check_index, mock_query_data):
        """
        Test retrieving data with a lowercase language.

        Ensures that `query_data` is called properly when a lowercase language is provided.
        """
        mock_check_index.return_value = {"proceed": True}
        get_data(language="german", data_type="nouns")
        mock_query_data.assert_called_once_with(
            languages=["german"],
            data_type=["nouns"],
            output_dir="scribe_data_json_export",
            overwrite=False,
            interactive=False,
        )

    # MARK: Output Directory

    @patch("scribe_data.cli.get.query_data")
    @patch("scribe_data.cli.get.check_index_exists")
    def test_get_data_with_different_output_directory(
        self, mock_check_index, mock_query_data
    ):
        """
        Test retrieving data with a different output directory.

        Ensures that `query_data` is called properly when a different output directory is provided.
        """
        mock_check_index.return_value = {"proceed": True}
        get_data(
            language="german", data_type="nouns", output_dir="./custom_output_test"
        )
        mock_query_data.assert_called_once_with(
            languages=["german"],
            data_type=["nouns"],
            output_dir="./custom_output_test",
            overwrite=False,
            interactive=False,
        )

    # MARK: Overwrite is True

    @patch("scribe_data.cli.get.query_data")
    @patch("scribe_data.cli.get.check_index_exists")
    def test_get_data_with_overwrite_true(self, mock_check_index, mock_query_data):
        """
        Test retrieving data with the overwrite flag set to True.

        Ensures that `query_data` is called properly when the overwrite flag is set to True.
        """
        mock_check_index.return_value = {"proceed": True}
        get_data(language="English", data_type="verbs", overwrite=True)
        mock_query_data.assert_called_once_with(
            languages=["English"],
            data_type=["verbs"],
            output_dir="scribe_data_json_export",
            overwrite=True,
            interactive=False,
        )

    # MARK: Overwrite is False

    @patch("scribe_data.cli.get.query_data")
    @patch("scribe_data.cli.get.check_index_exists")
    def test_get_data_with_overwrite_false(self, mock_check_index, mock_query_data):
        mock_check_index.return_value = {"proceed": True}
        get_data(
            language="English",
            data_type="verbs",
            overwrite=False,
            output_dir="./custom_output_test",
            interactive=False,
        )
        mock_query_data.assert_called_once_with(
            languages=["English"],
            data_type=["verbs"],
            output_dir="./custom_output_test",
            overwrite=False,
            interactive=False,
        )

    # MARK: User Chooses Skip

    @patch("scribe_data.cli.get.check_index_exists")
    def test_user_skips_existing_file(self, mock_check_index):
        """
        Test the behavior when the user chooses to skip an existing file.
        """
        mock_check_index.return_value = {"proceed": False}
        get_data(language="English", data_type="nouns", output_dir="./test_output")
        mock_check_index.assert_called_once_with("./test_output", "English", "nouns")

    # MARK: Translations

    @patch("scribe_data.cli.get.parse_wd_lexeme_dump")
    def test_get_translations_no_language_specified(self, mock_parse):
        """
        Test behavior when no language is specified for 'translations'.
        Expect language="all".
        """
        get_data(data_type="translations")
        mock_parse.assert_called_once_with(
            language="all",
            wikidata_dump_type=["translations"],
            type_output_dir="scribe_data_json_export",
            wikidata_dump_path=None,
            overwrite_all=False,
        )

    @patch("scribe_data.cli.get.parse_wd_lexeme_dump")
    def test_get_translations_with_specific_language(self, mock_parse):
        """
        Test behavior when a specific language is provided for 'translations'.
        Expect parse_wd_lexeme_dump to be called with that language.
        """
        get_data(
            language="Spanish", data_type="translations", output_dir="./test_output"
        )
        mock_parse.assert_called_once_with(
            language="Spanish",
            wikidata_dump_type=["translations"],
            type_output_dir="./test_output",
            wikidata_dump_path=None,
            overwrite_all=False,
        )

    @patch("scribe_data.cli.get.parse_wd_lexeme_dump")
    def test_get_translations_with_dump(self, mock_parse):
        """
        Test behavior when a Wikidata dump path is specified for 'translations'.
        Even with a language, it should call parse_wd_lexeme_dump
        passing that dump path.
        """
        get_data(
            language="German", data_type="translations", wikidata_dump="./wikidump.json"
        )
        mock_parse.assert_called_once_with(
            language="German",
            wikidata_dump_type=["translations"],
            type_output_dir="scribe_data_json_export",
            wikidata_dump_path="./wikidump.json",
            overwrite_all=False,
        )

    # MARK: Use QID as language

    @patch("scribe_data.cli.get.parse_wd_lexeme_dump")
    @patch("scribe_data.cli.get.questionary.confirm")
    def test_get_data_with_wikidata_identifier(
        self, mock_questionary_confirm, mock_parse
    ):
        """
        Test retrieving data with a Wikidata identifier as language.

        Ensures that `parse_wd_lexeme_dump` is called with the correct parameters
        when a Wikidata identifier is used.
        """
        # Mock the user confirmation to return True (query Wikidata directly).
        mock_questionary_confirm.return_value.ask.return_value = False

        get_data(
            language="Q9217",
            wikidata_dump="scribe",
            output_dir="exported_json",
            all_bool=True,
        )
        mock_parse.assert_called_once_with(
            language="Q9217",
            wikidata_dump_type=["form"],
            data_types="all",
            type_output_dir="exported_json",
            wikidata_dump_path="scribe",
            overwrite_all=False,
        )

    @patch("scribe_data.cli.get.parse_wd_lexeme_dump")
    def test_get_data_with_wikidata_identifier_and_data_type(self, mock_parse):
        """
        Test retrieving a specific data type with a Wikidata identifier.

        Ensures that `parse_wd_lexeme_dump` is called with the correct parameters
        when a Wikidata identifier and specific data type are used.
        """
        get_data(
            language="Q9217",
            data_type="nouns",
            wikidata_dump="scribe",
            output_dir="exported_json",
        )
        mock_parse.assert_called_once_with(
            language="Q9217",
            wikidata_dump_type=["form"],
            data_types=["nouns"],
            type_output_dir="exported_json",
            wikidata_dump_testpath="scribe",
            overwrite_all=False,
        )


if __name__ == "__main__":
    unittest.main()
