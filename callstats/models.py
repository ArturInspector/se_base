from pydantic import BaseModel
from typing import Union, Any, Dict
import datetime


class UniqueCalls(BaseModel):
    beeline_calls: int
    bitrix_calls: int


class SourceSite(BaseModel):
    seo: int
    context: int


class SourceLeadBack(BaseModel):
    seo: int
    context: int


class SourceAvito(BaseModel):
    calls: int
    chats: int


class SourceYandex(BaseModel):
    true_calls: int = 0
    false_calls: int = 0


class RecallModel(BaseModel):
    phone: str
    call_time: datetime.datetime
    recall_time: Union[datetime.datetime, None] = None
    recall_minutes: Union[int, None] = None
    is_success: bool = False
    bitrix_deal: Union[Dict[str, Any], None] = None