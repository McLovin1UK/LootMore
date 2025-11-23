from pydantic import BaseModel
from typing import Optional

class CalloutRequest(BaseModel):
    image_b64: str
    game: Optional[str] = "arc_raiders"
    client_version: Optional[str] = "lootmore-alpha"
    timestamp: Optional[int] = None

class CalloutResponse(BaseModel):
    text: str
    audio_b64: Optional[str] = None
    audio_url: Optional[str] = None

class AdminBanRequest(BaseModel):
    token: str
    reason: Optional[str] = None

class AdminRotateRequest(BaseModel):
    token: str
