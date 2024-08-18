"""
Functions to convert data returned from the Scribe-Data CLI to other file types.

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

import csv
import json
from pathlib import Path
from typing import Optional

from scribe_data.cli.cli_utils import language_map
from scribe_data.load.data_to_sqlite import data_to_sqlite
from scribe_data.utils import (
    DEFAULT_CSV_EXPORT_DIR,
    DEFAULT_JSON_EXPORT_DIR,
    DEFAULT_SQLITE_EXPORT_DIR,
    DEFAULT_TSV_EXPORT_DIR,
    get_language_iso,
)

DATA_DIR = Path(DEFAULT_JSON_EXPORT_DIR)


def export_json(
    language: str, data_type: str, output_dir: Path, overwrite: bool
) -> None:
    normalized_language = language_map.get(language.lower())
    language_capitalized = language.capitalize()
    if not normalized_language:
        raise ValueError(f"Language '{language_capitalized}' is not recognized.")

    data_file = (
        DATA_DIR / normalized_language["language"].capitalize() / f"{data_type}.json"
    )

    if not data_file.exists():
        print(
            f"No data found for language '{normalized_language['language']}' and data type '{data_type}'."
        )
        return

    try:
        with data_file.open("r") as file:
            data = json.load(file)

    except (IOError, json.JSONDecodeError) as e:
        print(f"Error reading '{data_file}': {e}")
        return

    # Adjust the output directory for JSON exports.
    json_output_dir = (
        output_dir
        / DEFAULT_JSON_EXPORT_DIR
        / normalized_language["language"].capitalize()
    )
    json_output_dir.mkdir(parents=True, exist_ok=True)

    output_file = json_output_dir / f"{data_type}.json"
    if output_file.exists() and not overwrite:
        user_input = input(f"File '{output_file}' already exists. Overwrite? (y/n): ")
        if user_input.lower() != "y":
            print(f"Skipping {normalized_language['language']} - {data_type}")
            return

    try:
        with output_file.open("w") as file:
            json.dump(data, file, indent=2)
    except IOError as e:
        raise IOError(f"Error writing to '{output_file}': {e}") from e

    print(
        f"Data for language '{normalized_language['language']}' and data type '{data_type}' written to '{output_file}'"
    )


def convert_to_csv_or_tsv(
    file: Path,
    output_dir: Path,
    output_type: str,
    overwrite: bool,
) -> None:
    if not file.exists():
        print(f"No data found for {output_type} conversion.")
        return

    try:
        with file.open("r") as f:
            data = json.load(f)

    except (IOError, json.JSONDecodeError) as e:
        print(f"Error reading '{file}': {e}")
        return

    if output_type == "csv":
        delimiter = ","
        file_extension = "csv"
        output_subdirectory = DEFAULT_CSV_EXPORT_DIR

    elif output_type == "tsv":
        delimiter = "\t"
        file_extension = "tsv"
        output_subdirectory = DEFAULT_TSV_EXPORT_DIR

    else:
        print(f"Unsupported output type '{output_type}'.")
        return

    # Adjust the output directory for CSV exports.
    final_output_dir = (
        output_dir / output_subdirectory / file.split("/")[-2].capitalize()
    )
    final_output_dir.mkdir(parents=True, exist_ok=True)

    output_file = final_output_dir / f"{file.split('/')[-2]}.{file_extension}"
    if output_file.exists() and not overwrite:
        user_input = input(f"File '{output_file}' already exists. Overwrite? (y/n): ")
        if user_input.lower() != "y":
            print(f"Skipping {file}")
            return

    try:
        with output_file.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file, delimiter=delimiter)
            if isinstance(data, dict):
                for key, value in data.items():
                    writer.writerow([key, value])

            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        writer.writerow(item.values())

                    else:
                        writer.writerow([item])

            else:
                print(f"Unsupported data format for {output_type} export.")

    except IOError as e:
        print(f"Error writing to '{output_file}': {e}")
        return

    print(f"Data for '{file}' written to '{output_file}'")


def convert_to_sqlite(
    language: Optional[str] = None,
    data_type: Optional[str] = None,
    output_dir: Optional[str] = None,
    overwrite: bool = False,
) -> None:
    if not language:
        raise ValueError("Language must be specified for SQLite conversion.")

    languages = [language]
    specific_tables = [data_type] if data_type else None

    if output_dir:
        output_dir = Path(output_dir)
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Converting data for language: {language}, data type: {data_type} to SQLite")
    data_to_sqlite(languages, specific_tables)

    if output_dir:
        source_file = f"{get_language_iso(language).upper()}LanguageData.sqlite"
        source_path = Path(DEFAULT_SQLITE_EXPORT_DIR) / source_file
        target_path = output_dir / source_file
        if source_path.exists():
            if target_path.exists() and not overwrite:
                print(f"File {target_path} already exists. Use --overwrite to replace.")
            else:
                import shutil

                shutil.copy(source_path, target_path)
                print(f"SQLite database copied to: {target_path}")
        else:
            print(f"Warning: SQLite file not found at {source_path}")
    else:
        print("No output directory specified. SQLite file remains in default location.")
