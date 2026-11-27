import json
import os
from pathlib import Path
from pydantic import ValidationError
from src.extract.schema import Extraction
from src.extract.verify import check_items


TEXT_DIR = Path("data/interim/fise_text")      # intrare: textele din pdf_text.py
OUT_DIR = Path("data/interim/extractions")     # ieșire: rezultatele pe fișă

MODEL = os.environ.get("LLM_MODEL", "")

SYSTEM_PROMPT = """You extract structured items from a university course syllabus.

Use ONLY these sections: 4.1, 4.2, 5, 7.2, 8.1, 8.2, 10.3, 10.5.
Ignore: section 6 (program-level codes like CC1, CP1, CT2, C1, A1, RA1), hours,
section 9, percentages, bibliography, instructor names and emails.

Relation by section:
  7.2, 8.1, 8.2 -> TEACHES
  10.3, 10.5    -> ASSESSES
  5             -> USES_TOOL
  4.1, 4.2      -> PREREQUISITE

Rules:
- "evidence" must be copied character for character from the syllabus (max 300 chars).
- "text_en" is the item in English; translate if the source is Romanian.
- "kind" is one of: skill, knowledge, tool, course.
- "week" is the week number if the text gives one, otherwise null.
- Do not infer anything that is not written in the text.

Return ONLY a JSON object, no other text:
{"items": [{"text_en": "...", "evidence": "...", "section": "7.2",
            "relation": "TEACHES", "kind": "skill", "week": null}]}
"""

def call_llm(system: str, user: str) -> str:
    """SINGURA funcție care depinde de furnizorul de model.
    Primește promptul de sistem și mesajul utilizatorului, întoarce
    textul răspunsului (un șir). O completăm după ce verificăm
    documentația oficială Ollama (URL, antet de autentificare, cerere)."""
    raise NotImplementedError("completăm după verificarea documentației Ollama")


def parse_response(raw: str) -> Extraction:
    """Șirul de la LLM -> obiect Extraction. Aici lucrează pydantic."""
    raw = raw.strip()

    if raw.startswith("```"):
        raw = raw.strip("`")                # scoate backtick-urile de la capete
        raw = raw.removeprefix("json").strip()

    return Extraction.model_validate_json(raw)


def extract(text: str) -> tuple[Extraction, str]:

    user = f"SYLLABUS TEXT:\n\n{text}"
    raw = call_llm(SYSTEM_PROMPT, user)
    try:
        return parse_response(raw), raw
    except ValidationError as err:
        # Mesajul erorii spune exact ce câmp e greșit; îl trimitem înapoi.
        retry_user = (
            f"{user}\n\nYour previous answer was invalid: {err}\n"
            "Return ONLY valid JSON in the required format."
        )
        raw = call_llm(SYSTEM_PROMPT, retry_user)

        return parse_response(raw), raw


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)


    for txt in sorted(TEXT_DIR.glob("*.txt")):
        text = txt.read_text(encoding="utf-8")

        # Pasul LLM + verificarea formei
        extraction, raw = extract(text)

        # Verificarea adevarului: evidența e în sursa? relația e corecta?
        kept, rejected = check_items(extraction.items, text)

        result = {
            "source": txt.stem,                   # ex. "java_an2"
            "model": MODEL,
            "counts": {"kept": len(kept), "rejected": len(rejected)},
            # model_dump(): obiect pydantic -> dicționar, ca să-l scriem în JSON
            "kept": [item.model_dump() for item in kept],
            "rejected": [
                {"item": r["item"].model_dump(), "reason": r["reason"]}
                for r in rejected
            ],
            "raw_response": raw,                  # răspunsul brut, pentru depanare
        }

        # ensure_ascii=False păstrează diacriticele; indent=2 face fișierul lizibil.
        (OUT_DIR / f"{txt.stem}.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"{txt.stem}: kept={len(kept)} rejected={len(rejected)}")


if __name__ == "__main__":
    main()