from pydantic import BaseModel
from typing import Dict

class ProfileCreateRequestData(BaseModel):
    selected_object:str
    img:str
    ai:str


class ProgressCreateRequestData(BaseModel):
    type:str
    topic:str
    participants:Dict[str, dict]

