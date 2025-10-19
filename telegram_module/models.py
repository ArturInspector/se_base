from pydantic import BaseModel
from typing import List


class CityModel(BaseModel):
    group_id: int
    users_ids: List[int]
    deleted_users: int
    offline_users: int
    users_count: int