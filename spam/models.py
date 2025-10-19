from pydantic import BaseModel
from typing import List


class SpamFilterModel(BaseModel):
    status: bool = False
    words: List[str] = []