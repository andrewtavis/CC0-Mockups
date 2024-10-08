"""
Tests for the CLI get functionality.

.. raw:: html
    <!--
    * Copyright (C) 2024 Scribe
    *
    * This program is free software: you can redistribute it and/or modify
    * it under the terms of the GNU General Public License as published by
    * the Free Software Foundation, either version 3 of the License, or
    * (at your option) any later version.
    *
    * This program is distributed in the hope that it will be useful,
    * but WITHOUT ANY WARRANTY; without even the implied warranty of
    * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    * GNU General Public License for more details.
    *
    * You should have received a copy of the GNU General Public License
    * along with this program.  If not, see <https://www.gnu.org/licenses/>.
    -->
"""

import unittest
from unittest.mock import patch

from scribe_data.cli.get import get_data


class TestGetData(unittest.TestCase):
    # MARK: Subprocess Patching

    @patch("subprocess.run")
    def test_get_emoji_keywords(self, mock_subprocess_run):
        get_data(language="English", data_type="emoji-keywords")
        self.assertTrue(mock_subprocess_run.called)

    # MARK: Invalid Arguments

    def test_invalid_arguments(self):
        with self.assertRaises(ValueError):
            get_data()

    # MARK: All Data

    @patch("scribe_data.cli.get.query_data")
    def test_get_all_data(self, mock_query_data):
        get_data(all=True)
        mock_query_data.assert_called_once_with(None, None, None, False)

    # MARK: Language and Data Type

    @patch("scribe_data.cli.get.query_data")
    def test_get_specific_language_and_data_type(self, mock_query_data):
        get_data(language="german", data_type="nouns", output_dir="./test_output")
        mock_query_data.assert_called_once_with(
            languages=["german"],
            data_type=["nouns"],
            output_dir="./test_output",
            overwrite=False,
        )

    # MARK: Capitalized Language

    @patch("scribe_data.cli.get.query_data")
    def test_get_data_with_capitalized_language(self, mock_query_data):
        get_data(language="German", data_type="nouns")
        mock_query_data.assert_called_once_with(
            languages=["German"],
            data_type=["nouns"],
            output_dir="scribe_data_json_export",
            overwrite=False,
        )

    # MARK: Lowercase Language

    @patch("scribe_data.cli.get.query_data")
    def test_get_data_with_lowercase_language(self, mock_query_data):
        get_data(language="german", data_type="nouns")
        mock_query_data.assert_called_once_with(
            languages=["german"],
            data_type=["nouns"],
            output_dir="scribe_data_json_export",
            overwrite=False,
        )

    # MARK: Output Directory

    @patch("scribe_data.cli.get.query_data")
    def test_get_data_with_different_output_directory(self, mock_query_data):
        get_data(
            language="german", data_type="nouns", output_dir="./custom_output_test"
        )
        mock_query_data.assert_called_once_with(
            languages=["german"],
            data_type=["nouns"],
            output_dir="./custom_output_test",
            overwrite=False,
        )

    # MARK: Overwrite is True

    @patch("scribe_data.cli.get.query_data")
    def test_get_data_with_overwrite_true(self, mock_query_data):
        get_data(language="English", data_type="verbs", overwrite=True)
        mock_query_data.assert_called_once_with(
            languages=["English"],
            data_type=["verbs"],
            output_dir="scribe_data_json_export",
            overwrite=True,
        )

    # MARK: Overwrite is False

    @patch("scribe_data.cli.get.query_data")
    def test_get_data_with_overwrite_false(self, mock_query_data):
        get_data(
            language="English",
            data_type="verbs",
            overwrite=False,
            output_dir="./custom_output_test",
        )
        mock_query_data.assert_called_once_with(
            languages=["English"],
            data_type=["verbs"],
            output_dir="./custom_output_test",
            overwrite=False,
        )
