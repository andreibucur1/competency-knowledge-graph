from typing import Optional
from pydantic import BaseModel, Field
from src.extract.schema.vocab import Kind, Relation, Section
#o bucata de info extrasa din fisa
#nu avem nevoie de constuctor explicit, pydantic se ocupa de asta
class Item(BaseModel):
    text_en: str = Field(min_length=1)#formulare ce se stocheaza in graf
    evidence: str = Field(min_length=1, max_length=300)  # fragmentul exact din fisa
    section: Section
    relation: Relation
    kind: Kind
    week: Optional[int] = None  # numarul cursului/seminarului, dacă exista