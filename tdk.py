import sys, requests
from enum import Enum


class status(Enum):
    ok = 0
    connection_failed = 1
    not_found = 2   


def get_pronunciation_links(word):
    
    r = None
    try:
        r = requests.get('https://sozluk.gov.tr/yazim?ara=' + word)
    except:
        return status.connection_failed, []
    
    j = r.json()
    if type(j) == list:
        links = []
        for w in j:
            if 'seskod' in w.keys():
                links.append('https://sozluk.gov.tr/ses/' + w['seskod'] + '.wav')
        return status.ok, links
    else:
        return status.not_found, []

def download_pronuciations_from_links(dir, prefix, links):
    
    paths = []
    for i in range(len(links)):
        
        l = links[i]
        fpath = dir + '/' + prefix + '_' + str(i+1) + l[l.rfind('.'):]
        
        r = None
        try:
            r = requests.get(l)
        except:
            return status.connection_failed, paths
        
        f = open(fpath, 'wb')
        f.write(r.content)
        f.close()
        paths.append(fpath)
    
    return status.ok, paths

def download_pronuciations(dir, word):
    
    ret, links = get_pronunciation_links(word)
    if ret != status.ok:
        return ret, links
    return download_pronuciations_from_links(dir, word, links)

def get_word_data(word):
    
    url = 'https://sozluk.gov.tr/gts?ara={0}'
    r = None
    try:
        r = requests.get(url.format(word))
    except:
        return status.connection_failed, []
    j = r.json()
    if type(j) != list:
        return status.not_found, []
    return status.ok, j

def get_compound_nouns_from_data(data):
    
    nouns = []
    for entry in data:
        if 'birlesikler' in entry.keys() and entry['birlesikler']:
            entry_nouns = entry['birlesikler'].split(',')
            for n in entry_nouns:
                nouns.append(n.strip())       
    return nouns

def get_compound_nouns(word):
  
    ret, data = get_word_data(word)
    if ret != status.ok:
        return ret, data
    return status.ok, get_compound_nouns_from_data(data)

def get_expressions_from_data(data):
    
    expressions = []
    for entry in data:
        if 'atasozu' in entry.keys() and entry['atasozu']:
            for e in entry['atasozu']:
                if 'madde' in e.keys() and e['madde']:
                    expressions.append(e['madde'])
    return expressions

def get_expressions(word):
    
    ret, data = get_word_data(word)
    if ret != status.ok:
        return ret, data
    return status.ok, get_expressions_from_data(data)

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
    
    ret, data = get_word_data(word)
    if ret != status.ok:
        return ret, data
    return status.ok, get_meanings_from_data(data)

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
    
    ret, data = get_word_data(word)
    if ret != status.ok:
        return ret, data
    return status.ok, get_examples_from_data(data)


def print_from_data(data):
    
    entry_i = 1
    for entry in data:
        if 'anlamlarListe' in entry.keys() and entry['anlamlarListe']:
            
            print(f"- {entry['madde']} ", end='')
            if(len(data) > 1):
                print(f"({entry_i})")
            else:
                print("\n", end='')
            entry_i += 1
            
            k = 0
            meanings_list = entry['anlamlarListe']
            for m in meanings_list:
                
                k += 1
                print(f'{k:2}. ', end='')
                
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
    
    ret, data = get_word_data(word)
    if ret == status.connection_failed:
        print("connection failed")
        return
    elif ret == status.not_found:
        print(f"'{word}' were not found in the dictionary")
        return
    print_from_data(data)


def usage():
    print('- usage:\n  ' + sys.executable + ' ' + sys.argv[0] + ' [word] [-p]')


def main():
   
    if len(sys.argv) > 2:
        ret = ()
        word = ""
        if sys.argv[1].lower() == '-p':
            word = sys.argv[2]
            ret = download_pronuciations('.', word)
        elif sys.argv[2].lower() == '-p':
            word = sys.argv[1]
            ret = download_pronuciations('.', word)
        else:
            usage()
            return
        
        if ret[0] == status.connection_failed:
            print("connection failed")
            return
        elif ret[0] == status.not_found:
            print(f"no audio files for '{word}' were found")
            return
        
    elif len(sys.argv) == 2:
        print_word_data(sys.argv[1])
    else:
        usage()
    
if __name__ == "__main__":
    main()
    
