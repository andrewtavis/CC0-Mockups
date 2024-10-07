cli/
====

`View code on Github <https://github.com/scribe-org/Scribe-Data/tree/main/src/scribe_data/cli>`_

Scribe-Data provides a command-line interface (CLI) for efficient interaction with its language data functionality.

Usage
-----

The basic syntax for using the Scribe-Data CLI is:

.. code-block:: bash

    scribe-data [global_options] command [command_options]

Global Options
--------------

- ``-h, --help``: Show this help message and exit.
- ``-v, --version``: Show the version of Scribe-Data.
- ``-u, --upgrade``: Upgrade the Scribe-Data CLI.

Commands
--------

The Scribe-Data CLI supports the following commands:

1. ``list`` (alias: ``l``)
2. ``get`` (alias: ``g``)
3. ``total`` (alias: ``t``)
4. ``convert`` (alias: ``c``)

List Command
~~~~~~~~~~~~

Description: List languages, data types and combinations of each that Scribe-Data can be used for.

Usage:

.. code-block:: bash

    scribe-data list [options]

Options:
^^^^^^^^

- ``-lang, --language [LANGUAGE]``: List options for all or given languages.
- ``-dt, --data-type [DATA_TYPE]``: List options for all or given data types.
- ``-a, --all ALL``: List all languages and data types.

Example output:

.. code-block:: text

    $ scribe-data list
    Language     ISO  QID
    -----------------------
    English      en   Q1860
    French       fr   Q150
    German       de   Q188
    ...
    -----------------------

    Available data types: All languages
    -----------------------------------
    nouns
    prepositions
    translations
    verbs
    -----------------------------------

Get Command
~~~~~~~~~~~

Description: Get data from Wikidata for the given languages and data types.

Usage:

.. code-block:: bash

    scribe-data get [options]

Options:
^^^^^^^^

- ``-lang, --language LANGUAGE``: The language(s) to get.
- ``-dt, --data-type DATA_TYPE``: The data type(s) to get.
- ``-od, --output-dir OUTPUT_DIR``: The output directory path for results.
- ``-ot, --output-type {json,csv,tsv}``: The output file type.
- ``-o, --overwrite``: Whether to overwrite existing files (default: False).
- ``-a, --all ALL``: Get all languages and data types.
- ``-i, --interactive``: Run in interactive mode.

Example:

.. code-block:: bash

    $ scribe-data get -l English --data-type verbs -od ~/path/for/output

Behavior and Output:
^^^^^^^^^^^^^^^^^^^^

1. The command will first check for existing data:

    .. code-block:: text

        Updating data for language(s): English; data type(s): verbs
        Data updated:   0%|

2. If existing files are found, you'll be prompted to choose an option:

    .. code-block:: text

        Existing file(s) found for English verbs:

        1. verbs.json

        Choose an option:
        1. Overwrite existing data (press 'o')
        2. Skip process (press anything else)
        Enter your choice:

3. After making a selection, the get process begins:

    .. code-block:: text

        Getting and formatting English verbs
        Data updated: 100%|████████████████████████| 1/1 [00:29<00:00, 29.73s/process]

4. If no data is found, you'll see a warning:

    .. code-block:: text

        No data found for language 'english' and data type '['verbs']'.
        Warning: No data file found for 'English' ['verbs']. The command must not have worked.

Notes:
^^^^^^

1. The data type can be specified with ``--data-type`` or ``-dt``.
2. The command creates timestamped JSON files by default, even if no data is found.
3. If multiple files exist, you'll be given options to manage them (keep existing, overwrite, keep both, or cancel).
4. The process may take some time, especially for large datasets.

Troubleshooting:
^^^^^^^^^^^^^^^^

- If you receive a "No data found" warning, check your internet connection and verify that the language and data type are correctly specified.
- If you're having issues with file paths, remember to use quotes around paths with spaces.
- If the command seems to hang at 0% or 100%, be patient as the process can take several minutes depending on the dataset size and your internet connection.

Interactive Mode
----------------

.. code-block:: text

    $ scribe-data get -i
    Welcome to Scribe-Data interactive mode!
    Language options:
    1. English
    2. French
    3. German
    ...

    Please enter the languages to get data for, their numbers or (a) for all languages: 1

    Data type options:
    1. autosuggestions
    2. emoji_keywords
    3. nouns
    4. prepositions
    5. translations
    6. verbs

    ...

Total Command
~~~~~~~~~~~~~

Description: Check Wikidata for the total available data for the given languages and data types.

Usage:

.. code-block:: bash

    scribe-data total [options]

Options:
^^^^^^^^

- ``-lang, --language LANGUAGE``: The language(s) to check totals for.
- ``-dt, --data-type DATA_TYPE``: The data type(s) to check totals for.
- ``-a, --all ALL``: Get totals for all languages and data types.

Examples:

.. code-block:: text

    $ scribe-data total -dt nouns
    Data type: nouns
    Total number of lexemes: <NUMBER />

    $ scribe-data total -lang eng -dt nouns
    Language: eng
    Data type: nouns
    Total number of lexemes: <NUMBER />

Convert Command
~~~~~~~~~~~~~~~

Description: Convert data returned by Scribe-Data to different file types.

Usage:

.. code-block:: bash

    scribe-data convert [options]

Options:
^^^^^^^^

- ``-f, --file FILE``: The file to convert to a new type.
- ``-ko, --keep-original``: Whether to keep the file to be converted (default: True).
- ``-json, --to-json TO_JSON``: Convert the file to JSON format.
- ``-csv, --to-csv TO_CSV``: Convert the file to CSV format.
- ``-tsv, --to-tsv TO_TSV``: Convert the file to TSV format.
- ``-sqlite, --to-sqlite TO_SQLITE``: Convert the file to SQLite format.
