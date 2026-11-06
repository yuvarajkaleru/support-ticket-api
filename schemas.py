from pydantic import BaseModel,ConfigDict
from typing import Literal,Optional
from datetime import datetime
from enum import Enum

class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class TicketCreate(BaseModel):
    title: str
    description: str
    priority: Literal['low','medium','high'] = 'medium'

class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[Literal['low', 'medium', 'high']] = None
    status: Optional[TicketStatus] = None

class TicketResponse(TicketCreate):
    id: int
    status: str = "open"
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserCreate(BaseModel):
    username : str
    password : str

class UserLogin(BaseModel):
    username : str
    password : str

class CommentCreate(BaseModel):
    content: str


class CommentResponse(BaseModel):
    id: int
    content: str
    ticket_id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)