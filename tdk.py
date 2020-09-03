"""
Get Turkish words definitions, example sentences, pronunciations, etc.
from the TDK (Türk Dil Kurumu) dictionary.
"""

import os

import requests


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

    def __init__(self, word):
        """Construct a new TDK object with the given word."""
        self.word = word
        self.data = None
        self.links = None

    def semantic_data(self):
        """Return all raw data about the word in dictionary except audio."""
        if self.data:
            return self.data
        try:
            res = requests.get("https://sozluk.gov.tr/gts?ara=" + self.word)
        except requests.exceptions.RequestException:
            raise NetworkError(CONNECTION_FAILED_MSG)
        j = res.json()
        if not isinstance(j, list):
            raise WordNotFoundError(f"'{self.word}' is not found in the dictionary")
        self.data = j
        return self.data

    def audio_links(self):
        """Return a list of word pronunciation links."""
        if self.links:
            return self.links
        try:
            res = requests.get("https://sozluk.gov.tr/yazim?ara=" + self.word)
        except requests.exceptions.RequestException:
            raise NetworkError(CONNECTION_FAILED_MSG)
        j = res.json()
        if isinstance(j, list):
            self.links = []
            for word in j:
                if "seskod" in word.keys():
                    self.links.append(
                        "https://sozluk.gov.tr/ses/" + word["seskod"] + ".wav"
                    )
            return self.links
        raise NoAudioError(
            f"No audio files for '{self.word}' were found in the dictionary"
        )

    def download_audio(self, path=".", prefix=""):
        """Download word pronunciations to the given path
        with filenames in the form `{prefix}{word}_{i}.{ext}`."""
        links = self.audio_links()
        paths = []
        for i, link in enumerate(links):
            fpath = os.path.join(
                path, f"{prefix}{self.word}_{i+1}{link[link.rfind('.'):]}"
            )
            try:
                res = requests.get(link)
            except requests.exceptions.RequestException:
                raise NetworkError(CONNECTION_FAILED_MSG)
            with open(fpath, "wb") as buf:
                buf.write(res.content)
            paths.append(fpath)
        return paths

    def compound_nouns(self):
        """Return a list of compound nouns (birleşik kelimeler) associated with word."""
        data = self.semantic_data()
        nouns = []
        for entry in data:
            if "birlesikler" in entry.keys() and entry["birlesikler"]:
                entry_nouns = entry["birlesikler"].split(",")
                for noun in entry_nouns:
                    nouns.append(noun.strip())
        return nouns

    def expressions(self):
        """Return a list of expressions and idioms associated with word."""
        data = self.semantic_data()
        expressions = []
        for entry in data:
            for exp in entry.get("atasozu", []):
                if "madde" in exp.keys() and exp["madde"]:
                    expressions.append(exp["madde"])
        return expressions

    def meanings(self):
        """Return a list of meanings of word."""
        data = self.semantic_data()
        meanings = []
        for entry in data:
            entry_meanings = entry.get("anlamlarListe", [])
            for meaning in entry_meanings:
                if "anlam" in meaning.keys() and meaning["anlam"]:
                    meanings.append(meaning["anlam"])
        return meanings

    def examples(self):
        """Return a list of example sentences of word."""
        data = self.semantic_data()
        examples = []
        for entry in data:
            for meaning in entry.get("anlamlarListe", []):
                for example in meaning.get("orneklerListe", []):
                    if "ornek" in example.keys():
                        examples.append(example["ornek"])
        return examples

    def pprint(self):
        """Print word data like in a dictionary entry."""
        data = self.semantic_data()
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


def test():
    words = ["kaymak", "", "asdsfaf", "pehpehlemek"]
    for word in words:
        try:
            w = TDK(word)
            print(w.meanings())
            print(w.examples())
            print(w.compound_nouns())
            print(w.expressions())
            print(w.audio_links())
            print(w.download_audio())
            w.pprint()
        except TDKError as exc:
            print(exc)


if __name__ == "__main__":
    import sys
    import argparse

    main()
