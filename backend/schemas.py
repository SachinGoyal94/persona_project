from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class PersonaCreate(BaseModel):
    user_id: int
    character_name: str
    mode: str
    tone: Optional[str] = None
    summary: Optional[str] = None

class PersonaOut(BaseModel):
    id: int
    user_id: int
    character_name: str
    mode: str
    tone: Optional[str]
    summary: Optional[str]
    created_at: datetime

class MessageCreate(BaseModel):
    persona_id: int
    sender: str
    message: str
