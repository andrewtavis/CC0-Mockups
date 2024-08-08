# Scribe-Data CLI Usage

Scribe-Data provides a command-line interface (CLI) for efficient interaction with its language data functionality.

## Basic Usage

To utilize the Scribe-Data CLI, you can execute the following command in your terminal:

```bash
scribe-data [command] [options]
```

## Available Commands

- `list` (`l`): Enumerate available languages, data types and their combinations.
- `query` (`q`): Retrieve data from Wikidata for specified languages and data types.
- `total` (`t`): Display the total available data for given languages and data types.
- `convert` (`c`): Transform data returned by Scribe-Data into different file formats.

## Command Examples

### List Command

1. Display all available options:

   ```bash
   scribe-data list
   ```

2. Display available languages:

   ```bash
   scribe-data list -lang # --language
   ```

3. Display available data types:

   ```bash
   scribe-data list -dt # --data-type
   ```

### Total Command

1. Display total available data for a specific data type (e.g. nouns):

   ```bash
   scribe-data total -dt nouns
   ```

2. Display total available data for a specific language (e.g. English):

   ```bash
   scribe-data total -l English
   ```

3. Display total available data for both language and data type (e.g. English nouns):

   ```bash
   scribe-data total -l English -dt nouns
   ```

### Query Command

1. Query all available languages and data types:

   ```bash
   scribe-data query -a # --all
   ```

2. Query specific language and data type (e.g. German nouns):

   ```bash
   scribe-data query -lang German -dt nouns
   ```

### Convert Command

1. Retrieve data for both language and data type (e.g. English nouns) in CSV format:

   ```bash
   scribe-data query -l english --data-type verbs --output-dir ./output_data --output-type csv
   ```

2. Retrieve data for both language and data type (e.g. English nouns) in TSV format:

   ```bash
   scribe-data query -l english --data-type verbs --output-dir ./output_data --output-type tsv
   ```

### Interactive Query Mode

The CLI also offers an interactive query mode, which can be initiated with the following command:

```bash
scribe-data query -i
```

This mode guides users through the data retrieval process with a series of prompts:

1. Language selection: Users can choose from a list of available languages or select all.
2. Data type selection: Users can specify which types of data to query.
3. Output configuration: Users can set the file format, export directory, and overwrite preferences.

The interactive mode is particularly useful for users who prefer a guided approach or are exploring the available data options.

## Additional Assistance

For more detailed information on each command and its options, append the `--help` flag:

```bash
scribe-data --help # -h
scribe-data [command] --help
```

For comprehensive usage instructions and examples, please refer to the [official documentation](https://scribe-data.readthedocs.io/).

```

```
