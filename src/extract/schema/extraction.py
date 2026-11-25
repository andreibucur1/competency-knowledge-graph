from pydantic import BaseModel
from src.extract.schema.item import Item

class Extraction(BaseModel):
    items: list[Item]