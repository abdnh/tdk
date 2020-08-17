import sys, os

import requests


class TDKError(Exception):
    pass

class TDKConnectionError(TDKError):
    pass

class TDKWordNotFound(TDKError):
    pass


class TDK():

    def __init__(self, word):
        self.word = word
        self.data = None
        self.links = None

    def semantic_data(self):
        if self.data:
            return self.data
        try:
            r = requests.get('https://sozluk.gov.tr/gts?ara=' + self.word)
        except requests.exceptions.RequestException:
            raise TDKConnectionError("connection failed")
        j = r.json()
        if type(j) != list:
           raise TDKWordNotFound(f"'{self.word}' is not found in the dictionary")
        self.data = j
        return self.data

    def audio_links(self):
        if self.links:
            return self.links
        try:
            r = requests.get("https://sozluk.gov.tr/yazim?ara=" + self.word)
        except requests.exceptions.RequestException:
            raise TDKConnectionError("connection failed")
        j = r.json()
        if type(j) == list:
            self.links = []
            for w in j:
                if "seskod" in w.keys():
                    self.links.append("https://sozluk.gov.tr/ses/" + w["seskod"] + ".wav")
            return self.links
        else:
            raise TDKWordNotFound(f"'{self.word}' is not found in the dictionary")

    def download_audio(self, dir='.', prefix=''):
        links = self.audio_links()
        paths = []
        for i in range(len(links)):
            l = links[i]
            fpath = os.path.join(dir, f"{prefix}{self.word}_{i+1}{l[l.rfind('.'):]}")
            try:
                r = requests.get(l)
            except requests.exceptions.RequestException:
                raise TDKConnectionError("connection failed")
            f = open(fpath, 'wb')
            f.write(r.content)
            f.close()
            paths.append(fpath)
        return paths

    def compound_nouns(self):
        data = self.semantic_data()
        nouns = []
        for entry in data:
            if 'birlesikler' in entry.keys() and entry['birlesikler']:
                entry_nouns = entry['birlesikler'].split(',')
                for n in entry_nouns:
                    nouns.append(n.strip())
        return nouns

    def expressions(self):
        data = self.semantic_data()
        expressions = []
        for entry in data:
            for e in entry.get('atasozu', []):
                if 'madde' in e.keys() and e['madde']:
                    expressions.append(e['madde'])
        return expressions

    def meanings(self):
        data = self.semantic_data()
        meanings = []
        for entry in data:
            entry_meanings = entry.get('anlamlarListe', [])
            for m in entry_meanings:
                if 'anlam' in m.keys() and m['anlam']:
                    meanings.append(m['anlam'])
        return meanings

    def examples(self):
        data = self.semantic_data()
        examples = []
        for entry in data:
            for m in entry.get('anlamlarListe', []):
                for e in m.get('orneklerListe', []):
                    if 'ornek' in e.keys():
                        examples.append(e['ornek'])
        return examples

    def pprint(self):
        data = self.semantic_data()
        for i, entry in enumerate(data):
            if 'anlamlarListe' in entry.keys() and entry['anlamlarListe']:
                print(f"- {entry['madde']} ", end='')
                if(len(data) > 1):
                    print(f"({i+1})")
                else:
                    print("\n", end='')
                meanings_list = entry['anlamlarListe']

                for k, m in enumerate(meanings_list):
                    print(f'{k+1:2}. ', end='')

                    # print properties
                    if 'ozelliklerListe' in m.keys() and m['ozelliklerListe']:
                        properties = m['ozelliklerListe']
                        print("[", end='')
                        for i in range(len(properties)):
                            if 'tam_adi' in properties[i].keys():
                                print(properties[i]['tam_adi'], end='')
                                if i < len(properties) - 1:
                                    print(", ", end='')
                        print("] ", end='')

                    # print definition
                    if 'anlam' in m.keys() and m['anlam']:
                        print(m['anlam'])

                    # print examples
                    for e in m.get('orneklerListe', []):
                        if 'ornek' in e.keys() and e['ornek']:
                            print('\t"' + e['ornek'] + '"')


def usage():
    print('- usage:\n  ' + sys.executable + ' ' + sys.argv[0] + ' [word] [-p]')

def main():
    if len(sys.argv) > 2:
        word = ""
        try:
            if sys.argv[1].lower() == '-p':
                word = sys.argv[2]
                TDK(word).download_audio()
            elif sys.argv[2].lower() == '-p':
                word = sys.argv[1]
                TDK(word).download_audio()
            else:
                usage()
        except TDKConnectionError as e:
            print(e)
            sys.exit(1)
        except TDKWordNotFound as e:
            print(f"no audio files for '{word}' were found in the dictionary")
            sys.exit(1)
    elif len(sys.argv) == 2:
        try:
            TDK(sys.argv[1]).pprint()
        except TDKError as e:
            print(e)
            sys.exit(1)
    else:
        usage()

def test():
    words = ['kaymak', '', 'asdsfaf', 'pehpehlemek']
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
        except Exception as e:
            print(e)

if __name__ == "__main__":
    main()
