"""
Converts all or desired JSON data generated by Scribe-Data into SQLite databases.

# SPDX-License-Identifier: AGPL-3.0-or-later
"""

import ast
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import List, Optional

from tqdm.auto import tqdm

from scribe_data.utils import (
    DEFAULT_JSON_EXPORT_DIR,
    DEFAULT_SQLITE_EXPORT_DIR,
    camel_to_snake,
    get_language_iso,
    list_all_languages,
)


def data_to_sqlite(
    languages: Optional[List[str]] = None,
    specific_tables: Optional[List[str]] = None,
    identifier_case: str = "camel",
) -> None:
    PATH_TO_SCRIBE_DATA = Path(__file__).parent.parent

    with (
        open(
            PATH_TO_SCRIBE_DATA / "resources" / "language_metadata.json",
            encoding="utf-8",
        ) as f_languages,
        open(
            PATH_TO_SCRIBE_DATA / "resources" / "data_type_metadata.json",
            encoding="utf-8",
        ) as f_data_types,
    ):
        current_language_data = json.load(f_languages)
        data_types = json.load(f_data_types).keys()

    # TODO: Switch to all languages.
    current_languages = list_all_languages(current_language_data)
    current_languages = [
        "english",
        "french",
        "german",
        "italian",
        "portuguese",
        "russian",
        "spanish",
        "swedish",
    ]

    if not languages:
        languages = current_languages

    elif isinstance(languages, str):
        languages = languages.lower()

    elif isinstance(languages, list):
        languages = [lang.lower() for lang in languages]

    if not set(languages).issubset(current_languages):
        raise ValueError(
            f"Invalid language(s) specified. Available languages are: {', '.join(current_languages)}"
        )

    # Prepare data types to process.
    language_data_type_dict = {
        lang: [
            f.split(".json")[0]
            for f in os.listdir(Path(DEFAULT_JSON_EXPORT_DIR) / lang)
            if f.split(".json")[0] in (specific_tables or data_types)
        ]
        for lang in languages
    }

    if specific_tables and "autocomplete_lexicon" in specific_tables:
        for lang in language_data_type_dict:
            if "autocomplete_lexicon" not in language_data_type_dict[lang]:
                language_data_type_dict[lang].append("autocomplete_lexicon")

    languages_capitalized = [lang.capitalize() for lang in languages]
    print(
        f"Creating/Updating SQLite databases for the following languages: {', '.join(languages_capitalized)}"
    )
    if specific_tables:
        print(f"Updating only the following tables: {', '.join(specific_tables)}")

    def create_table(data_type, cols):
        """
        Create a table in the language database.

        Parameters
        ----------
        data_type : str
            The name of the table to be created.

        cols : list of str
            The names of columns for the new table.
        """
        # Convert column names to snake_case if requested.
        cols = [
            camel_to_snake(col) if identifier_case == "snake" else col for col in cols
        ]

        cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {data_type} ({' Text, '.join(cols)} Text, unique({cols[0]}))"
        )

    def table_insert(data_type, keys):
        """
        Insert a row into a language database table.

        Parameters
        ----------
        data_type : str
            The name of the table to be inserted into.

        keys : list of str
            The values to be inserted into the table row.
        """
        insert_question_marks = ", ".join(["?"] * len(keys))
        cursor.execute(
            f"INSERT OR IGNORE INTO {data_type} values({insert_question_marks})",
            keys,
        )

    maybe_over = ""  # output string formatting variable (see below)
    if (Path(DEFAULT_SQLITE_EXPORT_DIR) / "TranslationData.sqlite").exists():
        os.remove(Path(DEFAULT_SQLITE_EXPORT_DIR) / "TranslationData.sqlite")
        maybe_over = "over"

    connection = sqlite3.connect(
        Path(DEFAULT_SQLITE_EXPORT_DIR) / "TranslationData.sqlite"
    )
    cursor = connection.cursor()

    print(f"Database for translations {maybe_over}written and connection made.")

    for lang in tqdm(
        language_data_type_dict,
        desc="Tables added",
        unit="tables",
    ):
        print(f"Creating/Updating {lang} translations table...")
        json_file_path = Path(DEFAULT_JSON_EXPORT_DIR) / lang / "translations.json"

        if not json_file_path.exists():
            print(
                f"Skipping {lang} translations table creation as JSON file not found."
            )
            continue

        with open(json_file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        target_cols = [
            get_language_iso(language)
            for language in current_languages
            if language != lang
        ]
        cols = ["word"] + target_cols
        create_table(data_type=lang, cols=cols)
        cursor.execute(f"DELETE FROM {lang}")  # clear existing data
        for row in json_data:
            keys = [row]
            keys += [json_data[row][col_name] for col_name in cols[1:]]
            table_insert(data_type=lang, keys=keys)

        try:
            connection.commit()
            print(f"{lang} translations table created/updated successfully.\n")

        except sqlite3.Error as e:
            print(f"Error creating/updating {lang} translations table: {e}")

    connection.close()
    print("Translations database processing completed.\n")

    for lang in tqdm(
        language_data_type_dict,
        desc="Databases created",
        unit="dbs",
    ):
        if language_data_type_dict[lang] != []:
            maybe_over = ""  # output string formatting variable (see below)
            if (
                Path(DEFAULT_SQLITE_EXPORT_DIR)
                / f"{get_language_iso(lang).upper()}LanguageData.sqlite"
            ).exists():
                os.remove(
                    Path(DEFAULT_SQLITE_EXPORT_DIR)
                    / f"{get_language_iso(lang).upper()}LanguageData.sqlite"
                )
                maybe_over = "over"

            connection = sqlite3.connect(
                Path(DEFAULT_SQLITE_EXPORT_DIR)
                / f"{get_language_iso(lang).upper()}LanguageData.sqlite"
            )
            cursor = connection.cursor()
            print(f"Database for {lang} {maybe_over}written and connection made.")

            for dt in language_data_type_dict[lang]:
                if dt == "autocomplete_lexicon":
                    continue  # handled separately

                print(f"Creating/Updating {lang} {dt} table...")
                json_file_path = Path(DEFAULT_JSON_EXPORT_DIR) / lang / f"{dt}.json"

                if not json_file_path.exists():
                    print(
                        f"Skipping {lang} {dt} table creation as JSON file not found."
                    )
                    continue

                with open(json_file_path, "r", encoding="utf-8") as f:
                    json_data = json.load(f)

                if dt in ["nouns", "verbs", "prepositions"]:
                    cols = ["wdLexemeId"]

                    all_elem_keys = [
                        json_data[k].keys() for k in list(json_data.keys())
                    ]
                    all_keys_flat = list({k for ks in all_elem_keys for k in ks})

                    cols += all_keys_flat
                    create_table(data_type=dt, cols=cols)
                    cursor.execute(f"DELETE FROM {dt}")  # clear existing data

                    for row in json_data:
                        keys = [row]
                        keys += [
                            json_data[row][col_name]
                            if col_name in json_data[row]
                            else None
                            for col_name in cols[1:]
                        ]
                        table_insert(data_type=dt, keys=keys)

                    if dt == "nouns" and lang != "Russian":
                        table_insert(
                            data_type=dt, keys=["L0", "Scribe"] + [""] * (len(cols) - 2)
                        )

                    connection.commit()

                elif dt in ["autosuggestions", "emoji_keywords"]:
                    cols = ["word"] + [f"{dt[:-1]}_{i}" for i in range(3)]
                    create_table(data_type=dt, cols=cols)
                    cursor.execute(f"DELETE FROM {dt}")  # clear existing data
                    for row in json_data:
                        keys = [row]
                        if dt == "autosuggestions":
                            keys += [
                                json_data[row][i] for i in range(len(json_data[row]))
                            ]
                        else:  # emoji_keywords
                            keys += [
                                json_data[row][i]["emoji"]
                                for i in range(len(json_data[row]))
                            ]
                        keys += [""] * (len(cols) - len(keys))
                        table_insert(data_type=dt, keys=keys)

                connection.commit()

            # Handle autocomplete_lexicon separately.
            if (not specific_tables or "autocomplete_lexicon" in specific_tables) and {
                "nouns",
                "prepositions",
                "autosuggestions",
                "emoji_keywords",
            }.issubset(set(language_data_type_dict[lang] + (specific_tables or []))):
                print(f"Creating/Updating {lang} autocomplete_lexicon table...")
                cols = ["word"]
                create_table(data_type="autocomplete_lexicon", cols=cols)
                cursor.execute(
                    "DELETE FROM autocomplete_lexicon"
                )  # clear existing data

                sql_query = """
                INSERT INTO
                    autocomplete_lexicon (word)

                WITH full_lexicon AS (
                    SELECT
                        noun AS word

                    FROM
                        nouns

                    WHERE
                        LENGTH(noun) > 2

                    UNION

                    SELECT
                        preposition AS word

                    FROM
                        prepositions

                    WHERE
                        LENGTH(preposition) > 2

                    UNION

                    SELECT DISTINCT
                        -- For autosuggestion keys we want lower case versions.
                        -- The SELECT DISTINCT cases later will make sure that nouns are appropriately selected.
                        LOWER(word) AS word

                    FROM
                        autosuggestions

                    WHERE
                        LENGTH(word) > 2

                    UNION

                    SELECT
                        word AS word

                    FROM
                        emoji_keywords
                )

                SELECT DISTINCT
                    -- Select an upper case noun if it's available.
                    CASE
                        WHEN
                            UPPER(SUBSTR(lex.word, 1, 1)) || SUBSTR(lex.word, 2) = nouns_cap.noun

                        THEN
                            nouns_cap.noun

                        WHEN
                            UPPER(lex.word) = nouns_upper.noun

                        THEN
                            nouns_upper.noun

                        ELSE
                            lex.word

                    END

                FROM
                    full_lexicon AS lex

                LEFT JOIN
                    nouns AS nouns_cap

                ON
                    UPPER(SUBSTR(lex.word, 1, 1)) || SUBSTR(lex.word, 2) = nouns_cap.noun

                LEFT JOIN
                    nouns AS nouns_upper

                ON
                    UPPER(lex.word) = nouns_upper.noun

                WHERE
                    LENGTH(lex.word) > 1
                    AND lex.word NOT LIKE '%-%'
                    AND lex.word NOT LIKE '%/%'
                    AND lex.word NOT LIKE '%(%'
                    AND lex.word NOT LIKE '%)%'
                    AND lex.word NOT LIKE '%"%'
                    AND lex.word NOT LIKE '%“%'
                    AND lex.word NOT LIKE '%„%'
                    AND lex.word NOT LIKE '%”%'
                    AND lex.word NOT LIKE "%'%"
                """

                try:
                    cursor.execute(sql_query)
                    connection.commit()
                    print(
                        f"{lang} autocomplete_lexicon table created/updated successfully."
                    )

                except sqlite3.Error as e:
                    print(f"Error creating/updating autocomplete_lexicon table: {e}")

            connection.close()
            print(f"{lang.capitalize()} database processing completed.")

        else:
            print(
                f"Skipping {lang.capitalize()} database creation/update as no related JSON data files were found."
            )

    print("Database creation/update process completed.\n")


if __name__ == "__main__":
    languages = ast.literal_eval(sys.argv[1]) if len(sys.argv) >= 2 else None
    specific_tables = ast.literal_eval(sys.argv[2]) if len(sys.argv) == 3 else None

    data_to_sqlite(languages, specific_tables)
