"""
Functions for listing languages and data types for the Scribe-Data CLI.

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

from scribe_data.cli.cli_utils import (
    LANGUAGE_DATA_EXTRACTION_DIR,
    correct_data_type,
    language_map,
    language_metadata,
)
from scribe_data.utils import (
    format_sublanguage_name,
    get_language_iso,
    get_language_qid,
    list_all_languages,
)


def list_languages() -> None:
    """
    Generates a table of languages, their ISO-2 codes and their Wikidata QIDs.
    """
    languages = list_all_languages(language_metadata)

    language_col_width = max(len(lang) for lang in languages) + 2
    iso_col_width = max(len(get_language_iso(lang)) for lang in languages) + 2
    qid_col_width = max(len(get_language_qid(lang)) for lang in languages) + 2

    table_line_length = language_col_width + iso_col_width + qid_col_width

    print()
    print(
        f"{'Language':<{language_col_width}} {'ISO':<{iso_col_width}} {'QID':<{qid_col_width}}"
    )
    print("-" * table_line_length)

    for lang in languages:
        print(
            f"{lang.capitalize():<{language_col_width}} {get_language_iso(lang):<{iso_col_width}} {get_language_qid(lang):<{qid_col_width}}"
        )

    print("-" * table_line_length)
    print()


def list_data_types(language: str = None) -> None:
    """
    Lists all data types or those available for a given language.

    Parameters
    ----------
        language : str
            The language to potentially list data types for.
    """
    languages = list_all_languages(language_metadata)
    if language:
        language = format_sublanguage_name(language, language_metadata)
        language_data = language_map.get(language.lower())
        language_capitalized = language.capitalize()
        language_dir = LANGUAGE_DATA_EXTRACTION_DIR / language_capitalized

        if not language_data:
            raise ValueError(f"Language '{language}' is not recognized.")

        data_types = [f.name for f in language_dir.iterdir() if f.is_dir()]
        if not data_types:
            raise ValueError(
                f"No data types available for language '{language_capitalized}'."
            )

        table_header = f"Available data types: {language_capitalized}"

    else:
        data_types = set()
        for lang in languages:
            language_dir = (
                LANGUAGE_DATA_EXTRACTION_DIR
                / format_sublanguage_name(lang, language_metadata).capitalize()
            )
            if language_dir.is_dir():
                data_types.update(f.name for f in language_dir.iterdir() if f.is_dir())

        table_header = "Available data types: All languages"

    table_line_length = max(len(table_header), max(len(dt) for dt in data_types))

    print()
    print(table_header)
    print("-" * table_line_length)

    data_types = sorted(data_types)
    for dt in data_types:
        print(dt.replace("_", "-"))

    print("-" * table_line_length)
    print()


def list_all() -> None:
    """
    Lists all available languages and data types.
    """
    list_languages()
    list_data_types()


def list_languages_for_data_type(data_type: str) -> None:
    """
    Lists the available languages for a given data type.

    Parameters
    ----------
        data_type : str
            The data type to check for.
    """
    data_type = correct_data_type(data_type=data_type)
    all_languages = list_all_languages(language_metadata)
    available_languages = []
    for lang in all_languages:
        lang = format_sublanguage_name(lang, language_metadata)
        language_dir = LANGUAGE_DATA_EXTRACTION_DIR / lang
        if language_dir.is_dir():
            dt_path = language_dir / data_type
            if dt_path.exists():
                available_languages.append(lang)

    available_languages.sort()
    table_header = f"Available languages: {data_type}"
    table_line_length = max(
        len(table_header), max(len(lang) for lang in available_languages)
    )

    print()
    print(table_header)
    print("-" * table_line_length)

    for lang in available_languages:
        print(f"{lang}")

    print("-" * table_line_length)
    print()


def list_wrapper(
    language: str = None, data_type: str = None, all_bool: bool = False
) -> None:
    """
    Conditionally provides the full functionality of the list command.

    Parameters
    ----------
        language : str
            The language to potentially list data types for.

        data_type : str
            The data type to check for.

        all_bool : boolean
            Whether all languages and data types should be listed.
    """
    if (not language and not data_type) or all_bool:
        list_all()

    elif language is True and not data_type:
        list_languages()

    elif not language and data_type is True:
        list_data_types()

    elif language is True and data_type is True:
        print("Please specify either a language or a data type.")

    elif language is True and data_type is not None:
        list_languages_for_data_type(data_type)

    elif language is not None and data_type is True:
        list_data_types(language)
