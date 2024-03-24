"""
Utility functions for the machine translation process.

Contents:
    translation_interrupt_handler,
    translate_to_other_languages
"""

import json
import os
import signal
import sys

from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer

PATH_TO_SCRIBE_ORG = os.path.dirname(sys.path[0]).split("Scribe-Data")[0]
PATH_TO_SCRIBE_DATA_SRC = f"{PATH_TO_SCRIBE_ORG}Scribe-Data/src"
sys.path.insert(0, PATH_TO_SCRIBE_DATA_SRC)

from scribe_data.utils import (  # noqa: E402
    get_language_dir_path,
    get_language_iso,
    get_target_langcodes,
)


def translation_interrupt_handler(source_language, translations):
    """
    Handles interrupt signals and saves the current translation progress.

    Parameters
    ----------
        source_language : str
            The source language being translated from.

        translations : list[dict]
            The current list of translations.
    """
    print(
        "\nThe interrupt signal has been caught and the current progress is being saved..."
    )

    with open(
        f"{get_language_dir_path(source_language)}/formatted_data/translated_words.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(translations, file, ensure_ascii=False, indent=4)

    print("The current progress is saved to the translated_words.json file.")
    exit()


def translate_to_other_languages(source_language, word_list, translations, batch_size):
    """
    Translates a list of words from the source language to other target languages using batch processing.

    Parameters
    ----------
        source_language : str
            The source language being translated from.

        word_list : list[str]
            The list of words to translate.

        translations : dict
            The current dictionary of translations.

        batch_size : int
            The number of words to translate in each batch.
    """
    model = M2M100ForConditionalGeneration.from_pretrained("facebook/m2m100_418M")
    tokenizer = M2M100Tokenizer.from_pretrained("facebook/m2m100_418M")

    signal.signal(
        signal.SIGINT,
        lambda sig, frame: translation_interrupt_handler(source_language, translations),
    )

    for i in range(0, len(word_list), batch_size):
        batch_words = word_list[i : i + batch_size]
        print(f"Translating batch {i//batch_size + 1}: {batch_words}")

        for lang_code in get_target_langcodes(source_language):
            tokenizer.src_lang = get_language_iso(source_language)
            encoded_words = tokenizer(batch_words, return_tensors="pt", padding=True)
            generated_tokens = model.generate(
                **encoded_words, forced_bos_token_id=tokenizer.get_lang_id(lang_code)
            )
            translated_words = tokenizer.batch_decode(
                generated_tokens, skip_special_tokens=True
            )

            for word, translation in zip(batch_words, translated_words):
                if word not in translations:
                    translations[word] = {}

                translations[word][lang_code] = translation

        print(f"Batch {i//batch_size + 1} translation completed.")

        with open(
            f"{get_language_dir_path(source_language)}/formatted_data/translated_words.json",
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(translations, file, ensure_ascii=False, indent=4)

    print(
        "Translation results for all words are saved to the translated_words.json file."
    )
