from pydantic import BaseModel
from typing import Optional


class MessageCreate(BaseModel):
    text: str
    username: str = "API"
    reply_to_id: Optional[str] = None
    target: Optional[str] = None


class MessageReply(BaseModel):
    text: str
    username: str = "API"
    target: Optional[str] = None


class AdminRegister(BaseModel):
    username: str
    password: str


class AdminLogin(BaseModel):
    username: str
    password: str


class TokenCreate(BaseModel):
    name: str
    description: Optional[str] = None
    expires_in_days: Optional[int] = None


class TokenResponse(BaseModel):
    token: str
    name: str
    description: Optional[str]
    created_at: str
    expires_at: Optional[str]
    is_active: bool


