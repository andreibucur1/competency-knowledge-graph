import re
import sys
import unicodedata
from pathlib import Path

import pymupdf

RAW = Path("data/raw/fise")
OUT = Path("data/interim/fise_text")

#tabel pentru inlocuire caractere speciale din pdf
_TRANSLATE = str.maketrans({
    "\u2018": "'", "\u2019": "'","\u201c": '"', "\u201d": '"',"\u2013": "-", "\u2014": "-"
})

#normalizare texte
def normalize(s:str) -> str:
    #unificam caractere cu coduri diferite, dar care arata la fel
    s = unicodedata.normalize("NFKC", s)
    #aplicam tabelul _TRANSLATE
    s = s.translate(_TRANSLATE)
    # orice grup de spații, taburi sau rânduri noi devine un singur spațiu,
    #    apoi se taie spațiile de la început și de la sfârșit
    return re.sub(r"\s+", " ", s).strip()


def pdf_to_text(pdf_path: Path) -> str:
    with pymupdf.open(pdf_path) as doc:
        # extragem textul din pagini, dupa lipim paginile cu endl
        return "\n".join(page.get_text() for page in doc)

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for pdf in sorted(RAW.glob("*.pdf")):
        raw_text = pdf_to_text(pdf)
        (OUT / f"{pdf.stem}.txt").write_text(raw_text, encoding="utf-8")
        print(f"{pdf.stem}: {len(normalize(raw_text).split())} cuvinte")




if __name__ == "__main__":
    sys.exit(main())
