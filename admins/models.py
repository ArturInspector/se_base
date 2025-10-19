from pydantic import BaseModel
import datetime


class MessageModel(BaseModel):
    text: str
    date: datetime.datetime
    chat_name: str
    chat_id: int
    fias_id: str
    is_selfemployers: bool = False