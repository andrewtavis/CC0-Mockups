"""
Check the queries within Scribe-Data to make sure the accessed forms are correct.

Example
-------
    python3 src/scribe_data/check/check_query_forms.py

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

import re
from pathlib import Path

from scribe_data.utils import (
    LANGUAGE_DATA_EXTRACTION_DIR,
    data_type_metadata,
    lexeme_form_metadata,
)

lexeme_form_qid_order = []
lexeme_form_labels_order = []
for key, value in lexeme_form_metadata.items():
    lexeme_form_qid_order.extend(
        sub_value["qid"] for sub_key, sub_value in value.items() if "qid" in sub_value
    )
    lexeme_form_labels_order.extend(
        sub_value["label"]
        for sub_key, sub_value in value.items()
        if "label" in sub_value
    )

qid_label_dict = dict(zip(lexeme_form_labels_order, lexeme_form_qid_order))


# MARK: Extract Forms


def extract_forms_from_sparql(file_path: Path) -> str:
    """
    Extracts the QID from a SPARQL query file based on the provided pattern.

    Parameters
    ----------
    file_path : Path
        The path to the SPARQL query file from which to extract forms.

    Returns
    -------
    query_form_dict : dict
        The file path with form labels of the query and their respective QIDs.

    Raises
    ------
    FileNotFoundError
        If the specified file does not exist.
    """
    optional_pattern = r"\s\sOPTIONAL\s*\{([^}]*)\}"
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            query_text = file.read()

            return [
                match[1]
                for match in re.finditer(pattern=optional_pattern, string=query_text)
            ]

    except Exception as e:
        print(f"Error reading {file_path}: {e}")

    return None


# MARK: Extract Label


def extract_form_rep_label(form_text: str):
    """
    Extracts the representation label from an optional query form.

    Parameters
    ----------
    form_text : str
        The text that defines the form within the query.

    Returns
    -------
    str
        The label of the form representation.
    """
    onto_rep_pattern = r"ontolex:representation .* ;"
    if line_match := re.search(pattern=onto_rep_pattern, string=form_text):
        rep_label_pattern = r".*\?(.*);"
        if label_match := re.search(pattern=rep_label_pattern, string=line_match[0]):
            return label_match[1].strip()


# MARK: Decompose Label


def decompose_label_features(label):
    """
    Decomposes a concatenated grammatical label into a list of individual features.

    Parameters
    ----------
    label : str
        The concatenated label string composed of several grammatical features.

    Returns
    -------
    list
        A list of grammatical features extracted from the label in their original order.
    """
    components = re.findall(r"[A-Za-z][^A-Z]*", label)
    valid_components = []
    temp_component = ""

    for index, component in enumerate(components):
        temp_component += component.capitalize()

        # Append valid components in lexeme_form_labels_order.
        if index + 1 != len(components) and (
            temp_component.lower() in map(str.lower, lexeme_form_labels_order)
            and temp_component + components[index + 1] not in lexeme_form_labels_order
        ):
            valid_components.append(temp_component)
            temp_component = ""

    if temp_component:
        valid_components.append(temp_component)

    return valid_components


# MARK: Extract QIDs


def extract_form_qids(form_text: str):
    """
    Extracts all QIDs from an optional query form.

    Parameters
    ----------
    form_text : str
        The text that defines the form within the query.

    Returns
    -------
    list[str]
        All QIDS that make up the form.
    """
    qids_pattern = r"wikibase:grammaticalFeature .+ \."
    if match := re.search(pattern=qids_pattern, string=form_text):
        return [q.split("wd:")[1].split(" .")[0] for q in match[0].split(", ")]


# MARK: Check Label


def check_form_label(form_text: str):
    """
    Checks that the label of the form matches the representation label.

    Parameters
    ----------
    form_text : str
        The text that defines the form within the query.

    Returns
    -------
    bool
        Whether the form and its current representation label match (repForm and rep).
    """
    form_label_line_pattern = r"\?lexeme ontolex:lexicalForm .* \."

    if line_match := re.search(pattern=form_label_line_pattern, string=form_text):
        form_label_pattern = r".*\?(.*)\."
        if label_match := re.search(pattern=form_label_pattern, string=line_match[0]):
            form_label = label_match[1].strip()
            current_form_rep_label = form_label.split("Form")[0]

    if not line_match:
        return False

    onto_rep_pattern = r"{form_label} ontolex:representation .* ;".format(
        form_label=form_label
    )

    if not (line_match := re.search(pattern=onto_rep_pattern, string=form_text)):
        return False

    rep_label_pattern = r".*\?(.*);"
    if label_match := re.search(pattern=rep_label_pattern, string=line_match[0]):
        form_rep_label = label_match[1].strip()

    return form_rep_label == current_form_rep_label


# MARK: Check Format


def check_query_formatting(form_text: str):
    """
    Checks the formatting of the given SPARQL query text for common formatting issues.

    Parameters
    ----------
    query_text : str
        The SPARQL query text to check.

    Returns
    -------
    bool
        Whether there are formatting errors with the query.
    """
    # Check for spaces before commas that should not exist.
    if re.search(r"\s,", form_text):
        return False

    # Check for non space characters before periods and semicolons that should not exist.
    if re.search(r"\S[.;]", form_text):
        return False

    return True


# MARK: Correct Label


def return_correct_form_label(qids: list):
    """
    Returns the correct label for a lexeme form representation given the QIDs that compose it.

    Parameters
    ----------
    qids : list[str]
        All QIDS that make up the form.

    Returns
    -------
    correct_label : str
        The label for the representation given the QIDs.
    """
    if not qids:
        return "Invalid query formatting found"

    if not set(qids) <= set(lexeme_form_qid_order):
        not_included_qids = sorted(set(qids) - set(lexeme_form_qid_order))
        qid_label = "QIDs" if len(not_included_qids) > 1 else "QID"
        return f"{qid_label} {', '.join(not_included_qids)} not included in lexeme_form.metadata.json"

    qids_ordered = [q for q in lexeme_form_qid_order if q in qids]
    correct_label = ""
    for q in qids_ordered:
        for category_vals in lexeme_form_metadata.values():
            for qid_label in category_vals.values():
                if q == qid_label["qid"]:
                    correct_label += qid_label["label"]

    return correct_label[:1].lower() + correct_label[1:]


# MARK: Validate Forms


def validate_forms(query_text: str) -> str:
    """
    Validates the SPARQL query by checking:
        1. Order of variables in SELECT and WHERE clauses
        2. Presence and correct definition of forms
        3. Form labels and representations
        4. Query formatting

    Parameters
    ----------
    query_file : str
        The SPARQL query text as a string.

    Returns
    -------
    str
        Error message if there are any issues with the order of variables or forms,
        otherwise an empty string.
    """
    select_pattern = r"SELECT\s+(.*?)\s+WHERE"

    # Extracting the variables from the SELECT statement.
    if select_match := re.search(select_pattern, query_text, flags=re.DOTALL):
        select_vars = re.findall(r"\?(\w+)", select_match[1])

    else:
        return "Invalid query format: no SELECT match"

    error_messages = []
    # Exclude the first two variables from select_vars.
    select_vars = select_vars[2:]
    # Regex pattern to capture the variables in the WHERE clause.
    dt_pattern = r"WHERE\s*\{[^}]*?wikibase:lemma\s*\?\s*(\w+)\s*[;.]\s*"
    potential_prep_case_pattern = r"caseForm rdfs:label.*[.]"
    forms_pattern = r"ontolex:representation \?([^ ;]+)"
    where_vars = []

    # Extracting variables from the WHERE clause.
    dt_match = re.findall(dt_pattern, query_text)
    if dt_match == ["lemma"]:
        where_vars.append("preposition")

    elif dt_match:
        where_vars.append(dt_match[0])

    potential_prep_case_match = re.findall(potential_prep_case_pattern, query_text)
    if potential_prep_case_match and "grammaticalCase" in potential_prep_case_match[0]:
        where_vars.append("grammaticalCase")

    where_vars += re.findall(forms_pattern, query_text)

    # Handling labels provided by the labeling service  like 'case' and 'gender' in the same order as in select_vars.
    for var in ["case", "gender", "auxiliaryVerb"]:
        if var in select_vars:
            # Insert in the corresponding index of where_vars.
            index = select_vars.index(var)
            where_vars.insert(index, var)

    uniqueness_forms_check = len(select_vars) != len(set(select_vars))
    undefined_forms = set(select_vars) - set(where_vars)
    unreturned_forms = set(where_vars) - set(select_vars)
    select_vars = [var for var in select_vars if var not in ["lexeme", "lexemeID"]]
    where_vars = [var for var in where_vars if var not in ["lexeme", "lexemeID"]]

    # Check for uniqueness of forms in SELECT.
    if uniqueness_forms_check:
        duplicates = [var for var in select_vars if select_vars.count(var) > 1]
        error_messages.append(
            f"Duplicate forms found in SELECT: {', '.join(set(duplicates))}"
        )

    # Check for undefined forms in SELECT.
    elif undefined_forms:
        error_messages.append(
            f"Undefined forms found in SELECT: {', '.join(sorted(undefined_forms))}"
        )

    # Check for unreturned forms in WHERE.
    elif unreturned_forms:
        error_messages.append(
            f"Defined but unreturned forms found: {', '.join(sorted(unreturned_forms))}"
        )

    # Check if the order of variables matches, excluding lexeme and lexemeID.
    elif select_vars != where_vars:
        # print('select vars is ',select_vars, '\n where vars is \n', where_vars)
        error_messages.append(
            "The order of variables in the SELECT statement does not match their order in the WHERE clause."
        )

    return "\n".join(error_messages) if error_messages else ""


# MARK: Docstring Format


def check_docstring(query_text: str) -> bool:
    """
    Checks the docstring of a SPARQL query text to ensure it follows the standard format.

    Parameters
    ----------
    query_text : str
        The SPARQL query's text to be checked.

    Returns
    -------
    bool
        True if the docstring is correctly formatted.
    """
    # Split the text into lines.
    query_lines = query_text.splitlines(keepends=True)

    # Regex patterns for each line in the docstring and corresponding error messages.
    patterns = [
        (r"^# tool: scribe-data\n", "Error in line 1:"),
        (
            r"^# All (.+?) \(Q\d+\) .+ \(Q\d+\) and the given forms\.\n",
            "Error in line 2:",
        ),
        (
            r"^# Enter this query at https://query\.wikidata\.org/\.\n",
            "Error in line 3:",
        ),
    ]
    return next(
        (
            (False, f"{error_line_number} {query_lines[i].strip()}")
            for i, (pattern, error_line_number) in enumerate(patterns)
            if not re.match(pattern, query_lines[i])
        ),
        True,
    )


# MARK: Variable Order


def check_forms_order(query_text):
    """
    Parses and orders variable names from a SPARQL query text based on a lexeme_form_metadata.json.

    Parameters
    ----------
    query_text : str
        The SPARQL query text containing the SELECT statement with variables.

    Returns
    -------
    list or bool
        A sorted list of variables if the ordering differs from the original,
        otherwise a boolean indicating that the order matches.
    """
    select_pattern = r"SELECT\s+(.*?)\s+WHERE"

    # Extracting the variables from the SELECT statement.
    if select_match := re.search(select_pattern, query_text, flags=re.DOTALL):
        select_vars = re.findall(r"\?(\w+)", select_match[1])

    # Hardcoded labels provided by the labeling service.
    labeling_service_cols = ["case", "gender", "auxiliaryVerb"]
    select_vars = select_vars[2:]

    # Split each column label into components.
    split_vars = []
    for col in set(select_vars) - set(labeling_service_cols):
        valid_components = decompose_label_features(col)
        split_vars.append(valid_components)

    # Create a map for fast component position lookup.
    order_map = {item: index for index, item in enumerate(lexeme_form_labels_order)}

    # Group columns by component length for sorting.
    grouped_columns = {}
    for col in split_vars:
        grouped_columns.setdefault(len(col), []).append(col)

    # Sorting function for multi-level component-based sorting.
    def compare_key(components):
        return [order_map.get(comp, float("inf")) for comp in components]

    # Sort and reassemble columns.
    sorted_columns = []
    for length in sorted(grouped_columns.keys()):
        sorted_group = sorted(grouped_columns[length], key=compare_key)
        sorted_columns.extend("".join(col) for col in sorted_group)

    # Append labeling service columns to the end.
    sorted_columns.extend(
        col.lower() for col in labeling_service_cols if col in select_vars
    )

    # Ensure specific types appear at the start if in select_vars.
    data_types = [
        re.sub(r"[^a-zA-Z]", "", key).lower() for key in data_type_metadata.keys()
    ]
    for dt in data_types:
        base_dt = dt[:-1]
        if base_dt in select_vars:
            sorted_columns.remove(base_dt.capitalize())
            sorted_columns.insert(0, base_dt)

    # Return sorted columns or validate if it matches select_vars.
    sorted_lower = [i.lower() for i in sorted_columns]
    select_lower = [i.lower() for i in select_vars]

    if select_lower != sorted_lower:
        return "  ?" + "\n  ?".join([i[0].lower() + i[1:] for i in sorted_columns])

    return sorted_lower == select_lower


# MARK: Optional Validation


def check_optional_qid_order(query_file: str) -> str:
    """
    Checks the order of QIDs in optional statements within a SPARQL query file to ensure they
    align with the expected sequence based on label features.

    Parameters
    ----------
    query_file : str
        The path to the SPARQL query file to be checked.

    Returns
    -------
    str
        A formatted string with details on any order mismatches in the QIDs, or an empty
        string if all QIDs are correctly ordered.
    """
    forms = extract_forms_from_sparql(query_file)
    error_messages = []
    for form_text in forms:
        if "ontolex:lexicalForm" in form_text and "ontolex:representation" in form_text:
            # Extract the actual QIDs and label for the current form.
            actual_qids = extract_form_qids(form_text=form_text)
            form_label = extract_form_rep_label(form_text)
            label_components = decompose_label_features(form_label)
            expected_qids = [qid_label_dict[key] for key in label_components]

            # Keep PastParticiple and imperfective QIDs as is in the query since we have duplicate qids for it.
            for i in ["Q12717679", "Q1230649", "Q2898727", "Q54556033"]:
                if i in actual_qids and i not in expected_qids:
                    expected_qids[actual_qids.index(i)] = i
            # Check if the actual QIDs match the expected order.
            if len(actual_qids) == len(expected_qids) and actual_qids != expected_qids:
                formatted_qids = ", ".join(f"wd:{qid}" for qid in expected_qids) + " ."
                error_messages.append(
                    f"\nThe QIDs in optional statement for {form_label} should be ordered:\n{formatted_qids}"
                )
    return "\n".join(error_messages) if error_messages else ""


# MARK: Main Validation


def check_query_forms() -> None:
    """
    Validates SPARQL queries in the language data directory to check for correct form QIDs and formatting.
    """
    error_output = ""
    index = 0
    for query_file in LANGUAGE_DATA_EXTRACTION_DIR.glob("**/*.sparql"):
        query_file_str = str(query_file)
        with open(query_file, "r", encoding="utf-8") as file:
            query_text = file.read()

        # Check the docstring format.
        docstring_check_result = check_docstring(query_text)
        if docstring_check_result is not True:
            error_output += (
                f"\n{index}. {query_file_str}:\n  - {docstring_check_result}\n"
            )
            index += 1
        # Check forms ordering.
        forms_order_result = check_forms_order(query_text)
        if forms_order_result is not True:
            error_output += f"\n{index}. {query_file_str}:\n  Form ordering for the above file should be:\n\n{forms_order_result}\n"
            index += 1

        # Check that all variables in the WHERE and SELECT clauses are ordered, defined and returned.
        if forms_order_and_definition_check := validate_forms(query_text):
            error_output += f"\n{index}. {query_file_str}:\n  - {forms_order_and_definition_check}\n"
            index += 1

        # Check that all variables in the OPTIONAL clauses have their QIDs in the correct order.
        if labels_qids_order_check := check_optional_qid_order(query_file_str):
            error_output += f"\n{index}. {query_file_str}:\n{labels_qids_order_check}\n"
            index += 1

        if extract_forms_from_sparql(query_file):
            query_form_check_dict = {}
            for form_text in extract_forms_from_sparql(query_file):
                if (
                    "ontolex:lexicalForm" in form_text
                    and "ontolex:representation" in form_text
                ):
                    correct_formatting = check_query_formatting(form_text=form_text)
                    form_rep_label = extract_form_rep_label(form_text=form_text)
                    check = check_form_label(form_text=form_text)
                    qids = extract_form_qids(form_text=form_text)
                    correct_form_rep_label = return_correct_form_label(qids=qids)

                    query_form_check_dict[form_rep_label] = {
                        "form_rep_match": check,
                        "correct_formatting": correct_formatting,
                        "qids": qids,
                        "correct_form_rep_label": correct_form_rep_label,
                    }

            if query_form_check_dict:
                incorrect_query_labels = []
                for k, v in query_form_check_dict.items():
                    if k != v["correct_formatting"] is False:
                        incorrect_query_labels.append(
                            (
                                k,
                                "Invalid query formatting found - please put spaces before all periods and semicolons and also remove spaces before commas.",
                            )
                        )

                    elif k != query_form_check_dict[k]["correct_form_rep_label"]:
                        incorrect_query_labels.append(
                            (k, query_form_check_dict[k]["correct_form_rep_label"])
                        )

                    elif query_form_check_dict[k]["form_rep_match"] is False:
                        incorrect_query_labels.append(
                            (k, "Form and representation labels don't match")
                        )

                if incorrect_query_labels:
                    current_rep_label_to_correct_label_str = [
                        f"{incorrect_query_labels[i][0]} : {incorrect_query_labels[i][1]}"
                        for i in range(len(incorrect_query_labels))
                    ]
                    incorrect_query_form_rep_labels_str = "\n  - ".join(
                        current_rep_label_to_correct_label_str
                    )

                    error_output += f"\n{index}. {query_file_str}:\n  - {incorrect_query_form_rep_labels_str}\n"
                    index += 1

    if error_output:
        print(
            "There are query forms that have invalid representation labels given their forms:"
        )
        print(error_output)
        print("Please correct the above lexeme form representation labels.")
        exit(1)

    else:
        print("All query forms are labeled and formatted correctly.")


if __name__ == "__main__":
    check_query_forms()
