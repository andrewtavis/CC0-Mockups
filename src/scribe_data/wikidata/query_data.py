# SPDX-License-Identifier: GPL-3.0-or-later
"""
Updates data for Scribe by running all or desired WDQS queries and formatting scripts.
"""

import json
import os
import re
import subprocess
import sys
from http.client import IncompleteRead
from pathlib import Path
from urllib.error import HTTPError

from tqdm.auto import tqdm

from scribe_data.utils import (
    LANGUAGE_DATA_EXTRACTION_DIR,
    format_sublanguage_name,
    language_metadata,
    list_all_languages,
)
from scribe_data.wikidata.wikidata_utils import sparql

from scribe_data.utils import check_index_exists


def execute_formatting_script(output_dir: str, language: str, data_type: str):
    """
    Executes a formatting script given a filepath and output directory for the process.

    Parameters
    ----------
    output_dir : str
        The output directory path for results.

    language : str
        The language for which the data is being loaded.

    data_type : str
        The type of data being loaded (e.g. 'nouns', 'verbs').

    Returns
    -------
    The results of the formatting script are saved in the given output directory.
    """
    formatting_file_path = Path(__file__).parent / "format_data.py"

    # Determine the root directory of the project.
    project_root = Path(__file__).parent.parent.parent

    # Use sys.executable to get the Python executable path.
    python_executable = sys.executable

    # Set the PYTHONPATH environment variable.
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)

    subprocess_args = [
        "--dir-path",
        output_dir,
        "--language",
        language,
        "--data_type",
        data_type,
    ]

    try:
        subprocess.run(
            [
                python_executable,
                str(formatting_file_path),
                *subprocess_args,
            ],
            env=env,
            check=True,
        )

    except subprocess.CalledProcessError as e:
        print(f"Error: The formatting script failed with exit status {e.returncode}.")


def query_data(
    languages: str = None,
    data_type: str = None,
    output_dir: str = None,
    overwrite: bool = False,
    interactive: bool = False,
):
    """
    Queries language data from the Wikidata lexicographical data.

    Parameters
    ----------
    language : str
        The language(s) to get.

    data_type : str
        The data type(s) to get.

    output_dir : str
        The output directory path for results.

    overwrite : bool (default: False)
        Whether to overwrite existing files.

    Returns
    -------
    Formatted data from Wikidata saved in the output directory.
    """
    current_languages = list_all_languages(language_metadata)
    current_data_type = ["nouns", "verbs", "prepositions"]

    # Assign current_languages and current_data_type if no arguments have been passed.
    languages_update = current_languages if languages is None else languages
    languages_update = [lang for lang in languages_update]
    data_type_update = current_data_type if data_type is None else data_type

    all_language_data_extraction_files = [
        path for path in Path(LANGUAGE_DATA_EXTRACTION_DIR).rglob("*") if path.is_file()
    ]

    language_data_extraction_files_in_use = [
        path
        for path in all_language_data_extraction_files
        if path.parent.name in data_type_update
        and path.parent.parent.name in languages_update
        and path.name != "__init__.py"
    ]

    # Derive the maximum query interval for use in looping through all queries.
    query_intervals = []
    for f in language_data_extraction_files_in_use:
        if f.name[-len(".sparql") :] == ".sparql":
            if re.findall(r".+_\d+.sparql", str(f.name)):
                query_intervals.append(int(re.search(r"_(\d+)\.", f.name).group(1)))

    if query_intervals:
        max_query_interval = max(query_intervals)

    else:
        max_query_interval = None

    queries_to_run = {
        Path(re.sub(r"_\d+.sparql", ".sparql", str(f)))
        for f in language_data_extraction_files_in_use
        if f.name[-len(".sparql") :] == ".sparql"
    }
    queries_to_run = sorted(queries_to_run)

    # MARK: Run Queries

    for q in tqdm(
        queries_to_run,
        desc="Data updated",
        unit="process",
        disable=interactive,
    ):
        lang = format_sublanguage_name(q.parent.parent.name, language_metadata)
        target_type = q.parent.name

        updated_path = output_dir[2:] if output_dir.startswith("./") else output_dir
        export_dir = Path(updated_path) / lang.replace(" ", "_")
        export_dir.mkdir(parents=True, exist_ok=True)

        file_name = f"{target_type}.json"
        file_path = export_dir / file_name

        # using check_index_exists to check if the file exists
        try:
            check_result = check_index_exists(output_dir, lang, target_type)
            if not check_result["proceed"]:
                print(f"Skipping query for {lang.title()} {target_type}.")
                continue  # Skip this query if the user chooses not to overwrite
        except Exception as e:
            print(
                f"Error checking file existence for {lang.title()} {target_type}: {e}"
            )
            continue

        for attempt in range(3):
            try:
                with open(q, encoding="utf-8") as file:
                    sparql.setQuery(file.read())

                results = sparql.query().convert()
                if results:
                    break

            except (HTTPError, IncompleteRead) as e:
                print(f"Error: {e}")
                if attempt < 2:
                    print("Retrying...")
                    continue
                else:
                    print("Max retries reached. Skipping this query.")
                    continue

        query_results = results["results"]["bindings"]
        results_final = [{k: r[k]["value"] for k in r.keys()} for r in query_results]

        # Handle auxiliary verbs for German
        if lang == "German":
            for entry in results_final:
                entry.setdefault("auxiliaryVerb", "")

        queried_file_path = export_dir / f"{target_type}_queried.json"
        with open(queried_file_path, "w", encoding="utf-8") as f:
            json.dump(results_final, f, ensure_ascii=False, indent=0)

        # Handle additional interval-based queries (_2, _3, etc.)
        if "_1" in q.name:
            for i in range(2, max_query_interval + 1):
                additional_query = Path(str(q).replace("_1", f"_{i}"))
                if additional_query.exists():
                    try:
                        with open(additional_query, encoding="utf-8") as file:
                            sparql.setQuery(file.read())

                        results = sparql.query().convert()
                        if results:
                            query_results = results["results"]["bindings"]
                            results_final.extend(
                                {k: r[k]["value"] for k in r.keys()}
                                for r in query_results
                            )

                    except HTTPError as err:
                        print(f"HTTPError with {additional_query}: {err}")

        # Save final results
        with open(file_path, "w", encoding="utf-8") as json_file:
            json.dump(results_final, json_file, ensure_ascii=False, indent=0)

        execute_formatting_script(
            output_dir=output_dir, language=lang, data_type=target_type
        )
        print(
            f"Successfully queried and formatted data for {lang.title()} {target_type}."
        )
