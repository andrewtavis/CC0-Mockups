# SPDX-License-Identifier: GPL-3.0-or-later
"""
Functions for downloading Wikidata lexeme dumps.
"""

import contextlib
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import questionary
import requests
from rich import print as rprint
from tqdm import tqdm

from scribe_data.utils import DEFAULT_DUMP_EXPORT_DIR, check_lexeme_dump_prompt_download


def parse_date(date_string):
    """
    Parse a date string into a datetime.date object (formats: YYYYMMDD, YYYY/MM/DD, YYYY-MM-DD).

    Parameters
    ----------
    date_string : str
        The date string to be parsed.

    Returns
    -------
    datetime.date
        Parsed date object if the format is valid.
    None
        If the date format is invalid.
    """
    formats = ["%Y%m%d", "%Y/%m/%d", "%Y-%m-%d"]
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt).date()

        except ValueError:
            continue

    print(
        f"Invalid date format: {date_string}. Expected formats: YYYYMMDD, YYYY/MM/DD, or YYYY-MM-DD."
    )
    return None


def available_closest_lexeme_dumpfile(
    target_entity: str, other_old_dumps: str, check_wd_dump_exists
):
    """
    Find the closest available dump file based on the target date.

    Parameters
    ----------
    target_entity : str
        The target date for which the dump is requested (format: YYYY/MM/DD or similar).

    other_old_dumps : list
        List of available dump folders as strings.

    check_wd_dump_exists : function
        A function to validate if the dump file exists.

    Returns
    -------
    str
        The closest available dump file date (as a string).
    None
        If no suitable dump is found.
    """
    target_date = parse_date(target_entity)
    closest_date = None
    closest_diff = None

    if target_date:
        available_dates = []
        for i in other_old_dumps:
            if i == "..":
                continue

            with contextlib.suppress(requests.exceptions.HTTPError):
                if check_wd_dump_exists(i):
                    available_dates.append(i)
                    current_date = parse_date(i)
                    diff = abs((current_date - target_date).days)

                    if closest_diff is None or diff < closest_diff:
                        closest_date = i
                        closest_diff = diff

                    if current_date >= target_date:
                        break

        return closest_date


def download_wd_lexeme_dump(target_entity: str = "latest-lexemes"):
    """
    Download a Wikimedia lexeme dump based on the specified target entity or date.

    Parameters
    ----------
    target_entity : str, optional
        The target dump to download. Defaults to "latest-lexemes".
        - If "latest-lexemes", downloads the latest dump.
        - If a valid date (e.g., YYYYMMDD), attempts to download the dump for that date.

    Returns
    -------
    str
        The URL of the requested or closest available dump.
    None
        If no suitable dump is found or the request fails.
    """
    base_url = "https://dumps.wikimedia.org/wikidatawiki/entities"

    def check_wd_dump_exists(target_entity):
        """
        Check if the specified dump file exists for a target entity.

        Parameters
        ----------
        target_entity : str
            The target entity or date folder to check.

        Returns
        -------
        str
            The URL of the dump file if it exists.

        None
            If the dump file does not exist.
        """
        entity_url = f"{base_url}/{target_entity}/"
        entity_response = requests.get(entity_url, timeout=30)
        entity_response.raise_for_status()
        dump_filenames = re.findall(r'href="([^"]+)"', entity_response.text)

        file_url = f"wikidata-{target_entity}-lexemes.json.bz2"

        if file_url in dump_filenames:
            return f"{base_url}/{target_entity}/{file_url}"

    if target_entity != "latest-lexemes":
        try:
            if parse_date(target_entity):
                target_entity = target_entity.replace("/", "").replace("-", "")
                return check_wd_dump_exists(target_entity)

        except requests.exceptions.HTTPError as http_err:
            print(
                f"HTTP error occurred: {http_err} Status code: {http_err.response.status_code}"
            )
            print("We could not find your requested Wikidata lexeme dump.")

            response = requests.get(base_url, timeout=30)
            other_old_dumps = re.findall(r'href="([^"]+)/"', response.text)

            user_response = questionary.confirm(
                "Do you want to see the closest available older dumps?", default=True
            ).ask()

            if not user_response:
                return

            if other_old_dumps:
                closest_date = available_closest_lexeme_dumpfile(
                    target_entity, other_old_dumps, check_wd_dump_exists
                )
                print(
                    f"\nClosest available older dumps(YYYYMMDD): {parse_date(closest_date)}"
                )
                fileurl = f"{closest_date}/wikidata-{closest_date}-lexemes.json.bz2"

                if closest_date:
                    return f"{base_url}/{fileurl}"

                else:
                    return

            return other_old_dumps

    try:
        response = requests.get(base_url, timeout=30)
        response.raise_for_status()
        latest_dump = re.findall(r'href="([^"]+)"', response.text)
        if "latest-all.json.bz2" in latest_dump:
            latest_dump_link = f"{base_url}/latest-lexemes.json.bz2"
            return latest_dump_link

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")


def wd_lexeme_dump_download_wrapper(
    wikidata_dump: Optional[str] = None,
    output_dir: Optional[str] = None,
    default: bool = False,
) -> None:
    """
    Download Wikidata lexeme dumps given user preferences.

    Parameters
    ----------
    wikidata_dump : str
        Optional date string in YYYYMMDD format for specific dumps.

    output_dir : str
        Optional directory path for the downloaded file.
        Defaults to 'scribe_data_wikidata_dumps_export' directory.

    default : bool, optional
        If True, skips the user confirmation prompt.
        Defaults to False.

    Returns
    -------
    str or None
        - If successful and a dump is downloaded, returns the file path to the downloaded dump.
        - If an existing usable dump is detected, returns the path to the existing dump.
        - Returns None if the user chooses not to proceed with the download or no valid dump URL is found.
    """
    try:
        output_dir = output_dir or DEFAULT_DUMP_EXPORT_DIR

        os.makedirs(output_dir, exist_ok=True)

        # Don't check for lexeme if date given.
        if not wikidata_dump:
            if useable_file_dir := check_lexeme_dump_prompt_download(output_dir):
                return useable_file_dir

        dump_url = download_wd_lexeme_dump(wikidata_dump or "latest-lexemes")

        if not dump_url:
            rprint("[bold red]No dump URL found.[/bold red]")
            return False

        filename = dump_url.split("/")[-1]
        output_path = str(Path(output_dir) / filename)

        # Use default parameter to bypass user confirmation.
        user_response = (
            default
            or questionary.confirm(
                "We'll be using the Wikidata lexeme dump from dumps.wikimedia.org/wikidatawiki/entities. Do you want to proceed?",
                default=True,
            ).ask()
        )

        if user_response:
            rprint(f"[bold blue]Downloading dump to {output_path}...[/bold blue]")

            response = requests.get(dump_url, stream=True, timeout=30)
            total_size = int(response.headers.get("content-length", 0))

            with open(output_path, "wb") as f:
                with tqdm(
                    total=total_size, unit="iB", unit_scale=True, desc=output_path
                ) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))

            rprint("[bold green]Download completed successfully![/bold green]")

            return output_path

        else:
            return

    except requests.exceptions.RequestException as e:
        rprint(f"[bold red]Error downloading dump: {e}[/bold red]")

    except Exception as e:
        rprint(f"[bold red]An error occurred: {e}[/bold red]")
