from typing import List, Optional

from pydantic import BaseModel


class ChatMessage(BaseModel):
    """Chat message model for API responses"""
    id: str
    user_message: str
    assistant_message: str
    timestamp: str
    chat_id: str
    user_id: str
    title: Optional[str] = None


class ChatHistoryResponse(BaseModel):
    """Response model for chat history endpoints"""
    messages: List[ChatMessage]
    total: int