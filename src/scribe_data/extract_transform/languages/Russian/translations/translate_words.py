"""
Translates the Russian words queried from Wikidata to all other Scribe languages.

Example
-------
    python3 src/scribe_data/extract_transform/languages/Russian/translations/translate_words.py
"""

import json
import os

from scribe_data.extract_transform.translation.translation_utils import (
    translate_to_other_languages,
)

SRC_LANG = "Russian"
translate_script_dir = os.path.dirname(os.path.abspath(__file__))
words_to_translate_path = os.path.join(translate_script_dir, "words_to_translate.json")

with open(words_to_translate_path, "r", encoding="utf-8") as file:
    json_data = json.load(file)

word_list = [item["word"] for item in json_data]

translations = {}
translated_words_path = os.path.join(
    translate_script_dir, "../formatted_data/translated_words.json"
)
if os.path.exists(translated_words_path):
    with open(translated_words_path, "r", encoding="utf-8") as file:
        translations = json.load(file)

translate_to_other_languages(
    source_language=SRC_LANG,
    word_list=word_list,
    translations=translations,
    batch_size=100,
)
