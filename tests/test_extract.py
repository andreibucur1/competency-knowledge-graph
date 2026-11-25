import pytest

from src.extract.header import parse_header
from src.extract.pdf_text import OUT, normalize

FIXTURES = {
    "bco_an1": ("26.0233IF1.1-0006", "Basics of Operational Research", "2026-2027", 1, 1, 5),
    "statistica_an1": ("26.0233IF1.1-0003", "Statistics", "2026-2027", 1, 1, 5),
    "baze_de_date_an2": ("27.0233IF2.1-0002", "Databases", "2027-2028", 2, 1, 5),
    "java_an2": ("27.0233IF2.2-0005", "Multiparadigm Programming - Java", "2027-2028", 2, 2, 4),
    "data_analysis_an3": ("28.0233IF3.1-0005", "Software Development for Data Analysis", "2028-2029", 3, 1, 4),
}

#functie de citire a textului dupa prelucrare dar inainte de normalizare
def _text(stem):
    return (OUT / f"{stem}.txt").read_text(encoding="utf-8")

@pytest.mark.parametrize("stem", FIXTURES)#rulez pt fiecare test ca sa nu scriu 5 teste separate
def test_has_enough_words(stem):
    #cea mai scurta fisa are 843 cuv
    assert len(normalize(_text(stem)).split()) >= 500

@pytest.mark.parametrize("stem", FIXTURES)
def test_header_matches_fixture(stem):
    #testez parse_header, indirect normalize
    code, name, acad, year, sem, ects = FIXTURES[stem]
    h = parse_header(_text(stem))
    # verificam separat daca headerul respecta structura
    assert h["code"] == code
    assert h["name"] == name
    assert h["academic_year"] == acad
    assert h["year"] == year
    assert h["semester"] == sem
    assert h["ects"] == ects