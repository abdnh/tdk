import sys

import requests


class TDKError(Exception):
    pass

class TDKConnectionError(TDKError):
    pass

class TDKWordNotFound(TDKError):
    pass

def get_pronunciation_links(word):

    r = None
    try:
        r = requests.get("https://sozluk.gov.tr/yazim?ara=" + word)
    except requests.exceptions.RequestException:
        raise TDKConnectionError("connection failed")

    j = r.json()
    if type(j) == list:
        links = []
        for w in j:
            if "seskod" in w.keys():
                links.append("https://sozluk.gov.tr/ses/" + w["seskod"] + ".wav")
        return links
    else:
        raise TDKWordNotFound(f"'{word}' not found in the dictionary")

def download_pronunciations_from_links(dir, prefix, links):

    paths = []
    for i in range(len(links)):

        l = links[i]
        fpath = dir + '/' + prefix + '_' + str(i+1) + l[l.rfind('.'):]

        r = None
        try:
            r = requests.get(l)
        except requests.exceptions.RequestException:
            raise TDKConnectionError("connection failed")

        f = open(fpath, 'wb')
        f.write(r.content)
        f.close()
        paths.append(fpath)

    return paths

def download_pronunciations(dir, word):

    links = get_pronunciation_links(word)
    return download_pronunciations_from_links(dir, word, links)

def get_word_data(word):

    url = 'https://sozluk.gov.tr/gts?ara={0}'
    r = None
    try:
        r = requests.get(url.format(word))
    except requests.exceptions.RequestException:
        raise TDKConnectionError("connection failed")
    j = r.json()
    if type(j) != list:
       raise TDKWordNotFound(f"'{word}' not found in the dictionary")
    return j

def get_compound_nouns_from_data(data):

    nouns = []
    for entry in data:
        if 'birlesikler' in entry.keys() and entry['birlesikler']:
            entry_nouns = entry['birlesikler'].split(',')
            for n in entry_nouns:
                nouns.append(n.strip())
    return nouns

def get_compound_nouns(word):

    data = get_word_data(word)
    return get_compound_nouns_from_data(data)

def get_expressions_from_data(data):

    expressions = []
    for entry in data:
        if 'atasozu' in entry.keys() and entry['atasozu']:
            for e in entry['atasozu']:
                if 'madde' in e.keys() and e['madde']:
                    expressions.append(e['madde'])
    return expressions

def get_expressions(word):

    data = get_word_data(word)
    return get_expressions_from_data(data)

def get_meanings_from_data(data):

    meanings = []
    for entry in data:
        if 'anlamlarListe' in entry.keys() and entry['anlamlarListe']:
            entry_meanings = entry['anlamlarListe']
            for m in entry_meanings:
                if 'anlam' in m.keys() and m['anlam']:
                    meanings.append(m['anlam'])
    return meanings

def get_meanings(word):

    data = get_word_data(word)
    return get_meanings_from_data(data)

def get_examples_from_data(data):

    examples = []
    for entry in data:
        if 'anlamlarListe' in entry.keys() and entry['anlamlarListe']:
            entry_meanings = entry['anlamlarListe']
            for m in entry_meanings:
                if 'orneklerListe' in m.keys() and m['orneklerListe']:
                    for e in m['orneklerListe']:
                        if 'ornek' in e.keys():
                            examples.append(e['ornek']);
    return examples

def get_examples(word):

    data = get_word_data(word)
    return get_examples_from_data(data)

def print_from_data(data):

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
                if 'orneklerListe' in m.keys() and m['orneklerListe']:
                    for e in m['orneklerListe']:
                        if 'ornek' in e.keys() and e['ornek']:
                            print('\t"' + e['ornek'] + '"')

def print_word_data(word):

    data = get_word_data(word)
    print_from_data(data)

def usage():
    print('- usage:\n  ' + sys.executable + ' ' + sys.argv[0] + ' [word] [-p]')

def main():

    if len(sys.argv) > 2:
        word = ""
        try:
            if sys.argv[1].lower() == '-p':
                word = sys.argv[2]
                download_pronunciations('.', word)
            elif sys.argv[2].lower() == '-p':
                word = sys.argv[1]
                download_pronunciations('.', word)
            else:
                usage()
        except TDKConnectionError as e:
            print(e)
        except TDKWordNotFound as e:
            print(f"no audio files for '{word}' were found in the dictionary")

    elif len(sys.argv) == 2:
        try:
            print_word_data(sys.argv[1])
        except TDKError as e:
            print(e)
    else:
        usage()

if __name__ == "__main__":
    main()
