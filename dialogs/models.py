from pydantic import BaseModel
from typing import Union


class CreateDialogModel(BaseModel):
    source_id: Union[int, None] = None
    source_ident: Union[str, None] = None
    utm_source: Union[str, None] = None
    utm_medium: Union[str, None] = None
    utm_campaign: Union[str, None] = None
    utm_content: Union[str, None] = None
    utm_term: Union[str, None] = None