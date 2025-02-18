# SPDX-License-Identifier: GPL-3.0-or-later
"""
Setup and commands for the Scribe-Data command line interface.
"""

#!/usr/bin/env python3
import argparse
from pathlib import Path

from questionary import select
from rich import print as rprint

from scribe_data.cli.cli_utils import validate_language_and_data_type
from scribe_data.cli.convert import convert_wrapper
from scribe_data.cli.download import wd_lexeme_dump_download_wrapper
from scribe_data.cli.get import get_data
from scribe_data.cli.interactive import start_interactive_mode
from scribe_data.cli.list import list_wrapper
from scribe_data.cli.total import total_wrapper
from scribe_data.cli.upgrade import upgrade_cli
from scribe_data.cli.version import get_version_message
from scribe_data.utils import (
    DEFAULT_CSV_EXPORT_DIR,
    DEFAULT_DUMP_EXPORT_DIR,
    DEFAULT_JSON_EXPORT_DIR,
)
from scribe_data.wiktionary.parse_mediaWiki import parse_wiktionary_translations

LIST_DESCRIPTION = "List languages, data types and combinations of each that Scribe-Data can be used for."
GET_DESCRIPTION = (
    "Get data from Wikidata and other sources for the given languages and data types."
)
TOTAL_DESCRIPTION = "Check Wikidata for the total available data for the given languages and data types."
CONVERT_DESCRIPTION = "Convert data returned by Scribe-Data to different file types."
CLI_EPILOG = "Visit the codebase at https://github.com/scribe-org/Scribe-Data and documentation at https://scribe-data.readthedocs.io to learn more!"


def main() -> None:
    # MARK: CLI Base

    parser = argparse.ArgumentParser(
        description="The Scribe-Data CLI is a tool for extracting language data from Wikidata and other sources.",
        epilog=CLI_EPILOG,
        formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=60),
    )
    subparsers = parser.add_subparsers(dest="command")

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=get_version_message(),
        help="Show the version of the Scribe-Data CLI.",
    )

    parser.add_argument(
        "-u",
        "--upgrade",
        action="store_true",
        help="Upgrade the Scribe-Data CLI to the latest version.",
    )

    # MARK: List

    list_parser = subparsers.add_parser(
        "list",
        aliases=["l"],
        help=LIST_DESCRIPTION,
        description=LIST_DESCRIPTION,
        epilog=CLI_EPILOG,
        formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=60),
    )
    list_parser._actions[0].help = "Show this help message and exit."
    list_parser.add_argument(
        "-lang",
        "--language",
        nargs="?",
        const=True,
        help="List options for all or given languages.",
    )
    list_parser.add_argument(
        "-dt",
        "--data-type",
        nargs="?",
        const=True,
        help="List options for all or given data types (e.g., nouns, verbs).",
    )
    list_parser.add_argument(
        "-a",
        "--all",
        action=argparse.BooleanOptionalAction,
        help="List all languages and data types.",
    )

    # MARK: Get

    get_parser = subparsers.add_parser(
        "get",
        aliases=["g"],
        help=GET_DESCRIPTION,
        description=GET_DESCRIPTION,
        epilog=CLI_EPILOG,
        formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=60),
    )
    get_parser._actions[0].help = "Show this help message and exit."
    get_parser.add_argument(
        "-lang", "--language", type=str, help="The language(s) to get data for."
    )
    get_parser.add_argument(
        "-dt",
        "--data-type",
        type=str,
        help="The data type(s) to get data for (e.g., nouns, verbs).",
    )
    get_parser.add_argument(
        "-ot",
        "--output-type",
        type=str,
        choices=["json", "csv", "tsv", "sqlite"],
        help="The output file type.",
    )
    get_parser.add_argument(
        "-od",
        "--output-dir",
        type=str,
        help=f"The output directory path for results (default: ./{DEFAULT_JSON_EXPORT_DIR} for JSON, ./{DEFAULT_CSV_EXPORT_DIR} for CSV, etc.).",
    )
    get_parser.add_argument(
        "-ope",
        "--outputs-per-entry",
        type=int,
        help="How many outputs should be generated per data entry.",
    )
    get_parser.add_argument(
        "-o",
        "--overwrite",
        action="store_true",
        help="Whether to overwrite existing files (default: False).",
    )
    get_parser.add_argument(
        "-a",
        "--all",
        action=argparse.BooleanOptionalAction,
        help="Get all languages and data types.",
    )
    get_parser.add_argument(
        "-i", "--interactive", action="store_true", help="Run in interactive mode"
    )
    get_parser.add_argument(
        "-ic",
        "--identifier-case",
        type=str,
        choices=["camel", "snake"],
        default="camel",
        help="The case format for identifiers in the output data (default: camel).",
    )
    get_parser.add_argument(
        "-wdp",
        "--wikidata-dump-path",
        nargs="?",
        const="",
        help=f"Path to a local Wikidata lexemes dump. Uses default directory (./{DEFAULT_DUMP_EXPORT_DIR}) if no path provided.",
    )
    get_parser.add_argument(
        "-t", "--translation", type=str, help="parse a single word using MediaWiki API"
    )

    # MARK: Total

    total_parser = subparsers.add_parser(
        "total",
        aliases=["t"],
        help=TOTAL_DESCRIPTION,
        description=TOTAL_DESCRIPTION,
        epilog=CLI_EPILOG,
        formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=60),
    )
    total_parser._actions[0].help = "Show this help message and exit."
    total_parser.add_argument(
        "-lang", "--language", type=str, help="The language(s) to check totals for."
    )
    total_parser.add_argument(
        "-dt",
        "--data-type",
        type=str,
        help="The data type(s) to check totals for (e.g., nouns, verbs).",
    )
    total_parser.add_argument(
        "-a",
        "--all",
        action=argparse.BooleanOptionalAction,
        help="Check for all languages and data types.",
    )
    total_parser.add_argument(
        "-i", "--interactive", action="store_true", help="Run in interactive mode"
    )
    total_parser.add_argument(
        "-wdp",
        "--wikidata-dump-path",
        nargs="?",
        const=True,
        help=f"Path to a local Wikidata lexemes dump for running with '--all' (default: ./{DEFAULT_DUMP_EXPORT_DIR}).",
    )

    # MARK: Convert

    convert_parser = subparsers.add_parser(
        "convert",
        aliases=["c"],
        help=CONVERT_DESCRIPTION,
        description=CONVERT_DESCRIPTION,
        epilog=CLI_EPILOG,
        formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=60),
    )

    convert_parser._actions[0].help = "Show this help message and exit."
    convert_parser.add_argument(
        "-lang",
        "--language",
        type=str,
        required=False,
        help="The language of the file to convert.",
    )
    convert_parser.add_argument(
        "-dt",
        "--data-type",
        type=str,
        required=False,
        help="The data type(s) of the file to convert (e.g., nouns, verbs).",
    )
    convert_parser.add_argument(
        "-if",
        "--input-file",
        type=Path,
        required=False,
        help="The path to the input file to convert.",
    )
    convert_parser.add_argument(
        "-ot",
        "--output-type",
        type=str,
        choices=["json", "csv", "tsv", "sqlite"],
        required=True,
        help="The output file type.",
    )
    convert_parser.add_argument(
        "-od",
        "--output-dir",
        type=str,
        help="The directory where the output file will be saved.",
    )
    convert_parser.add_argument(
        "-o",
        "--overwrite",
        action="store_true",
        help="Whether to overwrite existing files (default: False).",
    )
    convert_parser.add_argument(
        "-ko",
        "--keep-original",
        action="store_true",
        default=True,
        help="Whether to keep the original file to be converted (default: True).",
    )
    convert_parser.add_argument(
        "-ic",
        "--identifier-case",
        type=str,
        choices=["camel", "snake"],
        default="camel",
        help="The case format for identifiers in the output data (default: camel).",
    )
    convert_parser.add_argument(
        "-a",
        "--all",
        action=argparse.BooleanOptionalAction,
        help="Convert all languages and data types.",
    )

    # MARK: Download

    download_parser = subparsers.add_parser(
        "download",
        aliases=["d"],
        help="Download Wikidata lexeme dumps.",
        description="Download Wikidata lexeme dumps from dumps.wikimedia.org.",
        epilog=CLI_EPILOG,
        formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=60),
    )
    download_parser._actions[0].help = "Show this help message and exit."
    download_parser.add_argument(
        "-wdv",
        "--wikidata-dump-version",
        nargs="?",
        const="latest",
        help="Download Wikidata lexeme dump. Optionally specify date in YYYYMMDD format.",
    )
    download_parser.add_argument(
        "-wdp",
        "--wikidata-dump-path",
        type=str,
        help=f"The output directory path for the downloaded dump (default: ./{DEFAULT_DUMP_EXPORT_DIR}).",
    )

    # MARK: Interactive

    interactive_parser = subparsers.add_parser(
        "interactive",
        aliases=["i"],
        help="Run in interactive mode.",
        description="Run in interactive mode.",
    )
    interactive_parser._actions[0].help = "Show this help message and exit."

    # MARK: Setup CLI

    args = parser.parse_args()

    if args.upgrade:
        upgrade_cli()
        return

    if not args.command:
        parser.print_help()
        return

    try:
        # Only validate language and data_type for relevant commands.
        if args.command in ["list", "l", "get", "g", "total", "t", "convert", "c"]:
            if (
                hasattr(args, "data_type")
                and args.data_type
                and isinstance(args.data_type, str)
            ):
                args.data_type = args.data_type.replace("-", "_")

            if hasattr(args, "language") or hasattr(args, "data_type"):
                try:
                    validate_language_and_data_type(
                        language=args.language if hasattr(args, "language") else None,
                        data_type=args.data_type
                        if hasattr(args, "data_type")
                        else None,
                    )

                except ValueError as e:
                    print(f"Input validation failed with error: {e}")
                    return

        if args.command in ["list", "l"]:
            list_wrapper(
                language=args.language, data_type=args.data_type, all_bool=args.all
            )

        elif args.command in ["get", "g"]:
            if args.interactive:
                start_interactive_mode(operation="get")

            if args.translation:
                parse_wiktionary_translations(args.translation, args.output_dir)

            else:
                get_data(
                    language=args.language.lower()
                    if args.language is not None
                    else None,
                    data_type=args.data_type.lower()
                    if args.data_type is not None
                    else None,
                    output_type=args.output_type,
                    output_dir=args.output_dir,
                    outputs_per_entry=args.outputs_per_entry,
                    overwrite=args.overwrite,
                    all_bool=args.all,
                    identifier_case=args.identifier_case,
                    wikidata_dump=args.wikidata_dump_path,
                )

        elif args.command in ["total", "t"]:
            if args.interactive:
                start_interactive_mode(operation="total")

            else:
                total_wrapper(
                    language=args.language.lower()
                    if args.language is not None
                    else None,
                    data_type=args.data_type.lower()
                    if args.data_type is not None
                    else None,
                    all_bool=args.all,
                    wikidata_dump=args.wikidata_dump_path,
                )

        elif args.command in ["convert", "c"]:
            convert_wrapper(
                languages=args.language.lower() if args.language is not None else None,
                data_types=args.data_type.lower()
                if args.data_type is not None
                else None,
                output_type=args.output_type,
                input_files=args.input_file,
                output_dir=args.output_dir,
                overwrite=args.overwrite,
                identifier_case=args.identifier_case,
                all=args.all,
            )

        elif args.command in ["download", "d"]:
            wd_lexeme_dump_download_wrapper(
                wikidata_dump=args.wikidata_dump_version
                if args.wikidata_dump_version != "latest"
                else None,
                output_dir=args.wikidata_dump_path,
            )

        elif args.command in ["interactive", "i"]:
            rprint(
                f"[bold cyan]Welcome to {get_version_message()} interactive mode![/bold cyan]"
            )
            action = select(
                "What would you like to do?",
                choices=[
                    "Download a Wikidata lexemes dump",
                    "Check for totals",
                    "Get data",
                    "Get translations",
                    "Convert JSON",
                    "Exit",
                ],
            ).ask()

            if action == "Download a Wikidata lexemes dump":
                wd_lexeme_dump_download_wrapper()

            elif action == "Check for totals":
                start_interactive_mode(operation="total")

            elif action == "Get data":
                start_interactive_mode(operation="get")

            elif action == "Get translations":
                start_interactive_mode(operation="translations")

            elif action == "Convert JSON":
                start_interactive_mode(operation="convert")

            else:
                print("Skipping action")

        else:
            parser.print_help()

    except KeyboardInterrupt:
        rprint("[bold red]Execution was interrupted by the user.[/bold red]")


if __name__ == "__main__":
    main()
