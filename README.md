# Competency Knowledge Graph

**An intelligent knowledge-graph-based system for linking competencies, occupations and educational programs.**
Bachelor's thesis, Faculty of Cybernetics, Statistics and Economic Informatics (CSIE), Bucharest University of Economic Studies.

> **Status: work in progress.** This README describes the system as it is planned. The [Roadmap](#roadmap) shows what already works.

## The idea

Universities describe what they teach in **course syllabi**. The labour market describes what jobs need in **ESCO**, the European classification of occupations and skills. The two use different words, so it is hard to answer a simple question: *does this study program prepare students for this job?*

This project connects both sides in **one knowledge graph**, so that questions like these can be answered:

- Which **essential skills of a data engineer** does the program cover, and in which courses?
- Which courses **teach** SQL, and in which courses is it **assessed**?
- What does program P **not yet cover** for occupation O?

Every answer is **traceable to the exact sentence in a syllabus** that supports it.

**Research question:** on the same set of questions, does a knowledge graph (**GraphRAG**) give more accurate, more consistent and more verifiable answers than **vector RAG**, **hybrid RAG**, or a **large-context LLM** that receives the documents directly?

## How it will work

```
                    ESCO v1.2.1 (occupations, skills, ISCO groups)
                                  │ import
                                  ▼
Syllabus (PDF) ──► text + header ──► LLM extraction ──► automatic checks ──► ESCO matching
                   (course, code,     (what is taught,    (evidence really     (link each item to
                    year, ECTS)        assessed, used)     in the text? right   an ESCO skill, or keep
                                                           relation?)           it as a local term)
                                                                  │
                                                                  ▼
                                                         Human reviewer
                                                       approves / rejects
                                                                  │ only approved claims
                                                                  ▼
                                  ┌──────────────── Neo4j knowledge graph ─────────────────┐
                                  │ Course ─TEACHES/ASSESSES─► Skill ◄─REQUIRES─ Occupation │
                                  └─────────────────────────────────────────────────────────┘
                                                                  │
User question ──► graph traversal + text/vector search ──► LLM answer ──► citation check ──► answer with sources
                                                                                              (or an explicit "not enough evidence")
```

## Design principles

1. **Every link is a claim with evidence.** "Course X teaches skill Y" is stored as a *claim* object, not just a graph edge. The claim keeps:
   - the exact evidence fragment;
   - its source document and document version;
   - the reviewer's decision.

   The graph edges are only a view of the **approved** claims.
2. **Nothing enters the graph unchecked.** The LLM only *proposes*. A claim must pass two gates:
   - the automatic checks: the evidence must appear verbatim in the syllabus, and its relation must match the syllabus section;
   - a human reviewer's approval.
3. **Full traceability.** Every relation leads back to: fragment → document → version + file hash. Archiving a document withdraws its relations from current results but deletes nothing.
4. **"No evidence" is not "not taught".** Missing evidence is reported as *unconfirmed coverage*, never as absence. A service error is reported separately.
5. **Answers come only from evidence.** Claims that the cited sources don't support are removed. The system may give a partial answer or explicitly abstain.
6. **English inside, Romanian at the edge.** The system works internally in English: ESCO in English, English versions of the syllabi. Romanian is supported only in the interface, by translating the question and the answer.

## Data model

**Already in the graph (from ESCO):**

| Node | Count |
|---|---|
| `Occupation` | 3,039 |
| `Skill` | 13,939 |
| `ISCOGroup` | 619 |

| Relation | Count |
|---|---|
| `(:Occupation)-[:REQUIRES_ESSENTIAL]->(:Skill)` | 67,600 |
| `(:Occupation)-[:REQUIRES_OPTIONAL]->(:Skill)` | 58,451 |
| `(:Occupation)-[:IN_ISCO_GROUP]->(:ISCOGroup)` | 3,039 |

**Planned (from syllabi):**

| Relation | Comes from syllabus section | Meaning |
|---|---|---|
| `TEACHES` | 7.2, 8.1, 8.2 (objectives, course and seminar content) | the course teaches this skill or knowledge |
| `ASSESSES` | 10.3, 10.5 (evaluation) | the course evaluates it |
| `USES_TOOL` | 5 (conditions, tools) | the course uses this tool or technology |
| `PREREQUISITE` | 4.1, 4.2 (prerequisites) | the course requires it beforehand |

Each extracted item is one of: `skill`, `knowledge`, `tool`, `course`.

**Lifecycles:**

| Object | States |
|---|---|
| Document | Uploaded → Processing → Processed / Failed (retry) → Archived. "Processed" does not mean "approved". |
| Claim | Proposed → In review → Approved / Rejected → Retracted |

## Evaluation plan

The same question set will go to four systems:

| System | What it does |
|---|---|
| Large-context LLM | receives the syllabi directly in the prompt |
| Vector RAG | semantic search over text fragments |
| Hybrid RAG | lexical + semantic search |
| **GraphRAG** | graph traversal + text search |

**What will be measured:**
- answer accuracy;
- citation correctness: does the cited fragment really support the answer?
- consistency of answers across repeated runs;
- response time;
- cost as the number of questions grows;
- update cost when one syllabus changes.

No target numbers are fixed in advance. Thresholds will be set from measurements.

**Arguments the experiment is meant to test:**
- the graph scales beyond a model's context window;
- the graph answers aggregate questions precisely ("how many essential skills…");
- the same entity stays the same over time (canonical ESCO identifiers);
- every answer can be traced and verified in the graph;
- incremental updates are cheap;
- cost scales well at high question volume.

## Roadmap

| Status | Step |
|---|---|
| Done | ESCO v1.2.1 imported into Neo4j with constraints, indexes and check queries (`db/import_esco.cypher`) |
| Done | PDF → text, with Unicode/whitespace normalization (`src/extract/pdf_text.py`) |
| Done | Syllabus header parser: name, code, year, semester, assessment, ECTS, academic year. Tested on 5 CSIE syllabi. |
| Done | Extraction schema: `Item`, `Extraction` and the allowed sections, relations and kinds (pydantic) |
| Done | Evidence verification: rejects invented evidence, wrong relations and bare competence codes (unit tests) |
| In progress | LLM extraction pipeline: prompt, JSON validation and one retry are done; the model call is not wired yet |
| Planned | ESCO matching for extracted items: candidate search + semantic check; local terms when there is no ESCO match |
| Planned | Human review step and claim storage (revisions, decisions) |
| Planned | Graph builder: publish approved claims as `TEACHES` / `ASSESSES` / … edges |
| Planned | Question set for the evaluation |
| Planned | Vector RAG, hybrid RAG and GraphRAG pipelines + large-context baseline |
| Planned | Evaluation runs and result tables |
| Planned | API and UI for exploring the graph and asking questions |


## Tech stack

| | |
|---|---|
| **In use** | Python, Neo4j (Cypher), PyMuPDF, pydantic, pytest |
| **Planned** | LLM served through Ollama, starting with its cloud API and moving to an NVIDIA DGX Spark if available; FastAPI + Streamlit for the API and UI |
| **To be decided by measurement** | vector index, observability tooling, a multi-agent extraction pipeline (kept only if it improves results measurably) |

Every component has to earn its place. Nothing is added just to fill the stack.

## Repository structure

```
competency-knowledge-graph/
├── db/
│   └── import_esco.cypher      # ESCO import into Neo4j + verification queries
├── src/extract/
│   ├── pdf_text.py             # PDF → text, normalization
│   ├── header.py               # syllabus header parser
│   ├── extract_items.py        # LLM extraction pipeline (in progress)
│   ├── verify.py               # evidence verification
│   └── schema/                 # Item, Extraction, allowed values
├── tests/
│   ├── test_extract.py         # text extraction + header parsing (needs local syllabi)
│   └── test_verify.py          # evidence verification
└── data/                       # not tracked: raw syllabi, intermediate files, ESCO CSVs
```

## Getting started (current state)

**1. ESCO in Neo4j**
1. Download the **ESCO v1.2.1** classification in **English, CSV format**.
2. Copy `ISCOGroups_en.csv`, `occupations_en.csv`, `skills_en.csv` and `occupationSkillRelations_en.csv` into Neo4j's `import` folder.
3. Run `db/import_esco.cypher` in Neo4j Browser. The file uses `:auto` for the batched steps.
4. Run the check queries at the end of the file. They should return the counts from [Data model](#data-model).

**2. Syllabi**

Put the syllabus PDFs in `data/raw/fise/`, then run from the repository root:

```bash
pip install pymupdf pydantic pytest

python -m src.extract.pdf_text      # PDF → data/interim/fise_text/*.txt
python -m src.extract.header        # print the parsed header of each syllabus
python -m pytest                    # run the tests
```

`tests/test_extract.py` expects the five syllabi it was written for to be present locally.
