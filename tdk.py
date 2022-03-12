"""
Get Turkish words definitions, example sentences, pronunciations, etc.
from the TDK (Türk Dil Kurumu) dictionary.
"""

import json
import os
import urllib
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, List, Optional


__all__ = [
    "TDK",
    "TDKError",
    "NetworkError",
    "WordNotFoundError",
    "NoAudioError",
]


class TDKError(Exception):
    pass


class NetworkError(TDKError):
    pass


class WordNotFoundError(TDKError):
    pass


class NoAudioError(TDKError):
    pass


CONNECTION_FAILED_MSG = "Connection failed"


class TDK:
    """A class representing a dictionary query for a single word."""

    "User-Agent string used to make the requests"
    user_agent: Optional[str] = "Mozilla/5.0"

    def __init__(self, word: str) -> None:
        """Construct a new TDK object with the given word."""
        self.word = word
        self.word_quoted = urllib.parse.quote(word)
        self.data: Optional[List[Dict]] = None
        self.links: List[str] = []
        self.similar: Optional[List[str]] = None

    def _get_request(self, url: str) -> urllib.request.Request:
        return urllib.request.Request(
            url,
            None,
            {"User-Agent": self.user_agent},
        )

    @property
    def semantic_data(self) -> List[Dict]:
        """All raw data about the word in the dictionary except audio."""
        if self.data is not None:
            return self.data
        try:
            req = self._get_request("https://sozluk.gov.tr/gts?ara=" + self.word_quoted)
            with urllib.request.urlopen(req) as res:
                self.data = []
                j = json.loads(res.read())
                if not isinstance(j, list):
                    raise WordNotFoundError(
                        f"'{self.word}' is not found in the dictionary"
                    )
                self.data = j
        except urllib.error.URLError as exc:
            raise NetworkError(CONNECTION_FAILED_MSG) from exc

        return self.data

    @property
    def audio_links(self) -> List[str]:
        """A list of pronunciation links."""
        if self.links:
            return self.links
        try:
            req = self._get_request(
                "https://sozluk.gov.tr/yazim?ara=" + self.word_quoted
            )
            with urllib.request.urlopen(req) as res:
                j = json.loads(res.read())
                if isinstance(j, list):
                    for word in j:
                        if "seskod" in word.keys() and word["seskod"]:
                            self.links.append(
                                "https://sozluk.gov.tr/ses/" + word["seskod"] + ".wav"
                            )
                    return self.links
        except urllib.error.URLError as exc:
            raise NetworkError(CONNECTION_FAILED_MSG) from exc

        raise NoAudioError(
            f"No audio files for '{self.word}' were found in the dictionary"
        )

    def download_audio(self, path: str = ".", prefix: str = "") -> List[str]:
        """
        Download pronunciations to the given path
        with filenames in the form `{prefix}{word}_{i}.{ext}`.
        """
        paths = []
        for i, link in enumerate(self.audio_links):
            fpath = os.path.join(
                path, f"{prefix}{self.word}_{i+1}{link[link.rfind('.'):]}"
            )
            try:
                req = self._get_request(link)
                with urllib.request.urlopen(req) as res:
                    with open(fpath, "wb") as buf:
                        buf.write(res.read())
                    paths.append(fpath)
            except urllib.error.URLError as exc:
                raise NetworkError(CONNECTION_FAILED_MSG) from exc

        return paths

    @property
    def similar_words(self) -> List[str]:
        """
        Return similar words according to the TDK dictionary.
        Useful to offer suggestions if the word queried does not exist in the dictionary.
        """
        if self.similar is not None:
            return self.similar
        try:
            req = self._get_request(
                "https://sozluk.gov.tr/oneri?soz=" + self.word_quoted
            )
            with urllib.request.urlopen(req) as res:
                j = json.loads(res.read())
                self.similar = list(map(lambda e: e["madde"], j))
        except urllib.error.URLError as exc:
            raise NetworkError(CONNECTION_FAILED_MSG) from exc

        return self.similar

    @property
    def compound_nouns(self) -> List[str]:
        """A list of compound nouns (birleşik kelimeler) associated with word."""
        nouns = []
        for entry in self.semantic_data:
            if "birlesikler" in entry.keys() and entry["birlesikler"]:
                entry_nouns = entry["birlesikler"].split(",")
                for noun in entry_nouns:
                    nouns.append(noun.strip())
        return nouns

    @property
    def expressions(self) -> List[str]:
        """A list of expressions and idioms associated with word."""
        expressions = []
        for entry in self.semantic_data:
            for exp in entry.get("atasozu", []):
                if "madde" in exp.keys() and exp["madde"]:
                    expressions.append(exp["madde"])
        return expressions

    @property
    def meanings(self) -> List[str]:
        """A list of meanings of word."""
        meanings = []
        for entry in self.semantic_data:
            entry_meanings = entry.get("anlamlarListe", [])
            for meaning in entry_meanings:
                if "anlam" in meaning.keys() and meaning["anlam"]:
                    meanings.append(meaning["anlam"])
        return meanings

    @property
    def examples(self) -> List[str]:
        """A list of example sentences of word."""
        examples = []
        for entry in self.semantic_data:
            for meaning in entry.get("anlamlarListe", []):
                for example in meaning.get("orneklerListe", []):
                    if "ornek" in example.keys():
                        examples.append(example["ornek"])
        return examples

    def pprint(self) -> None:
        """Print word data like in a dictionary entry."""
        data = self.semantic_data
        for i, entry in enumerate(data):
            if "anlamlarListe" in entry.keys() and entry["anlamlarListe"]:
                print(f"- {entry['madde']} ", end="")
                if len(data) > 1:
                    print(f"({i+1})")
                else:
                    print("\n", end="")
                meanings_list = entry["anlamlarListe"]

                for k, meaning in enumerate(meanings_list):
                    print(f"{k+1:2}. ", end="")

                    # print properties
                    if (
                        "ozelliklerListe" in meaning.keys()
                        and meaning["ozelliklerListe"]
                    ):
                        properties = meaning["ozelliklerListe"]
                        print("[", end="")
                        for j, prop in enumerate(properties):
                            if "tam_adi" in prop.keys():
                                print(prop["tam_adi"], end="")
                                if j < len(properties) - 1:
                                    print(", ", end="")
                        print("] ", end="")

                    # print definition
                    if "anlam" in meaning.keys() and meaning["anlam"]:
                        print(meaning["anlam"])

                    # print examples
                    for example in meaning.get("orneklerListe", []):
                        if "ornek" in example.keys() and example["ornek"]:
                            print('\t"' + example["ornek"] + '"')


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("word", help="the word you want to query")
    parser.add_argument("-p", help="download pronunciations", action="store_true")
    args = parser.parse_args()

    if args.p:
        try:
            TDK(args.word).download_audio()
        except TDKError as exc:
            print(exc)
            sys.exit(1)
    else:
        try:
            TDK(args.word).pprint()
        except TDKError as exc:
            print(exc)
            sys.exit(1)


def demo():
    from random import shuffle

    words = ["kaymak", "", "asdsfaf", "pehpehlemek", "yapmak", "demek"]
    methods = [
        ("tdk.meanings", lambda self: self.meanings),
        ("tdk.examples", lambda self: self.examples),
        ("tdk.compound_nouns", lambda self: self.compound_nouns),
        ("tdk.expressions", lambda self: self.expressions),
        ("tdk.audio_links", lambda self: self.audio_links),
        ("tdk.download_audio", lambda self: self.download_audio()),
        ("tdk.similar_words", lambda self: self.similar_words),
        ("tdk.pprint", lambda self: self.pprint()),
    ]
    for word in words:
        try:
            print(f'--- "{word}" ---')
            tdk = TDK(word)
            shuffle(methods)
            for mth in methods:
                print(mth[0] + ": ", end="")
                print(mth[1](tdk))
                print("\n", end="")
        except TDKError as exc:
            print(exc)


if __name__ == "__main__":
    import sys
    import argparse

    main()
