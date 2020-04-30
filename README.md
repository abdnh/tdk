A python script & library to get Turkish words definitions, example sentences, pronunciations, etc. from the [TDK](https://sozluk.gov.tr/) dictionary.

## Usage:
The script can be used either as a library or a command line program.

To use from the command line, run the script with the word you want to look up as an argument:

    > py tdk.py söz
    - söz
     1. [isim] Bir düşünceyi eksiksiz olarak anlatan kelime dizisi, lakırtı, kelam, laf, kavil
     2. Bir veya birkaç heceden oluşan ve anlamı olan ses birliği, kelime, sözcük
     3. Bir konuyu yazılı veya sözlü olarak açıklamaya yarayan kelime dizisi
            "Yer yer birçok türküde rastladığımız beylik sözler de vardı içinde."
     4. Kesinlik kazanmayan haber, söylenti
            "Ortalıkta bir söz dolaşıyor."
     5. Bir işi yapacağını kesin olarak vadetme
            "O, sözünde duran bir adamdır."
     6. Müzik parçalarının yazılı metni, güfte
            "Şarkının sözleri çok anlamlı."
			
To get pronunciations, run with the `-p` flag:

    > py tdk.py söz -p

pronunciations files will be saved in the current working directory under the names `söz_1.wav`, `söz_2.wav`, etc. (depending on how many entries for the word there are).

## TODO:
* docs (for now, browse the source for available functions)
* make "idiomatic"
* better error handling
