from typing import Literal, Optional

Section = Literal["4.1", "4.2", "5", "7.2", "8.1", "8.2", "10.3", "10.5"]

Relation = Literal["TEACHES", "ASSESSES", "USES_TOOL", "PREREQUISITE"]

Kind = Literal["skill", "knowledge", "tool", "course"]

SECTION_RELATION = {
    "7.2": "TEACHES",
    "8.1": "TEACHES",
    "8.2": "TEACHES",
    "10.3": "ASSESSES",
    "10.5": "ASSESSES",
    "5": "USES_TOOL",
    "4.1": "PREREQUISITE",
    "4.2": "PREREQUISITE",
}