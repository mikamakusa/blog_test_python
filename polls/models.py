from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class AnswerBase(BaseModel):
    text: str = Field(..., min_length=1, max_length=200)
    votes: int = 0

class AnswerCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=200)

class Answer(AnswerBase):
    id: str

class PollBase(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    is_active: bool = True

class PollCreate(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    answers: List[AnswerCreate] = Field(..., min_items=2)
    is_active: bool = True

class PollUpdate(BaseModel):
    question: Optional[str] = Field(None, min_length=1, max_length=500)
    is_active: Optional[bool] = None

class Poll(PollBase):
    id: str
    answers: List[Answer]
    total_votes: int = 0
    created_at: datetime
    updated_at: datetime

class PollList(BaseModel):
    polls: List[Poll]
    total: int

class VoteRequest(BaseModel):
    answer_id: str 