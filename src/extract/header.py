import json
import re

from src.extract.pdf_text import OUT, normalize

PATTERNS = {
    "name": r"2\.1\. Name (.+?) 2\.2\. Code",
    "code": r"2\.2\. Code (\S+) 2\.3\.",
    "year": r"2\.3\. Year of study (\d+) 2\.4\.",
    "semester": r"2\.4\. Semester (\d+) 2\.5\.",
    "assessment": r"2\.5\. Type of assessment (\w+) 2\.6\.",
    "ects": r"2\.7\. Number of ECTS credits (\d+)",
    "academic_year": r"1\.9\. Academic year (\d{4}-\d{4})",
}

#campurile care trebuie să fie numere
INT_FIELDS = {"year", "semester", "ects"}

def parse_header(text):
    flat = normalize(text)
    header = {}
    for field, pattern in PATTERNS.items():
        m = re.search(pattern, flat)
        if m:
            value = m.group(1).strip()
        else:
            value = None
        if value is not None and field in INT_FIELDS:
            value = int(value)
        header[field] = value
    return header

def main():
    for txt in sorted(OUT.glob("*.txt")):
        header = parse_header(txt.read_text(encoding="utf-8"))
        print(txt.stem, json.dumps(header, ensure_ascii=False))


if __name__ == "__main__":
    main()