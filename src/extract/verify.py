import re

from src.extract.pdf_text import normalize

from src.extract.schema import SECTION_RELATION

CODE_ONLY = re.compile(r"^(C[CPT]\d+|[CA]\d+|RA\d+)$")

def check_items(items, source_text):
    #primeste itemii de la llm si textul fisei
    #intoarce (kept, rejected) -> itemii valizi si cei respinsi

    flat = normalize(source_text)

    kept, rejected = [] , []
    for item in items:
        #normalizam si evidenta
        evidence = normalize(item.evidence)

        #1.daca evidenta nu e in fisa, inseamna ca llm-ul a halucinat
        if evidence not in flat:
            rejected.append({"item": item, "reason": "evidence_not_in_source"})
        #2. relatia trb sa corespunda sectiunii din care vine itemul
        #ex: un item din 7.2 trb sa fie TEACHES, nu ASSESSES
        elif SECTION_RELATION[item.section] != item.relation:
            rejected.append({"item": item, "reason": "relation_mismatch"})

        #evidenta nu e doar un cod de competenta
        elif CODE_ONLY.match(evidence):
            rejected.append({"item": item, "reason": "competence_code_only"})

        else:
            kept.append(item)

    return kept, rejected
