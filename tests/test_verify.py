from src.extract.schema import Item
from src.extract.verify import check_items


SOURCE = "7.2 Seminar: Dijkstra algorithm and Kruskal. Student’s project. CT2"

def make_item(evidence, section = "7.2", relation = "TEACHES"):
    return Item(text_en="x", evidence=evidence, section=section,
                relation=relation, kind="skill")

def test_exact_evidence_kept():
    # Caz bun: evidența apare exact în sursA -> item pAstrat, nimic respins
    kept, rejected = check_items([make_item("Dijkstra algorithm")], SOURCE)
    assert len(kept) == 1 and rejected == []

def test_curly_apostrophe_is_normalized():
    # Sursa are ’ (curbat), evidența ' (drept). normalize() le face la fel,
    # deci itemul trebuie păstrat. Testul apără exact acest comportament.
    kept, _ = check_items([make_item("Student's project")], SOURCE)
    assert len(kept) == 1

def test_invented_evidence_rejected():
    # "Floyd-Warshall" nu apare în sursă -> LLM-ul a inventat.
    _, rejected = check_items([make_item("Floyd-Warshall")], SOURCE)
    assert rejected[0]["reason"] == "evidence_not_in_source"

def test_wrong_relation_rejected():
    # Secțiunea 7.2 înseamnă TEACHES; ASSESSES e greșit pentru ea.
    _, rejected = check_items([make_item("Kruskal", relation="ASSESSES")], SOURCE)
    assert rejected[0]["reason"] == "relation_mismatch"


def test_competence_code_only_rejected():
    # "CT2" e în sursă și relația e bună, dar e doar un cod -> respins.
    _, rejected = check_items([make_item("CT2")], SOURCE)
    assert rejected[0]["reason"] == "competence_code_only"