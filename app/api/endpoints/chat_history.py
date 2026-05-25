from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
import json

from app.schemas.chat import ChatHistoryResponse, ChatMessage
from app.services.vector_store import MultiTenantVectorStore
from app.api.deps import get_current_user, get_vector_store
from app.utils.logger import setup_logger
from app.core.redis import redis_client

logger = setup_logger(__name__)
router = APIRouter()


class RenameChatRequest(BaseModel):
    title: str


def invalidate_user_chats_cache(user_id: str):
    """Utility to invalidate all chat history cache keys for a given user"""
    if redis_client:
        try:
            keys = redis_client.keys(f"chats:{user_id}:*")
            if keys:
                redis_client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} Redis cache keys for user {user_id}")
        except Exception as e:
            logger.warning(f"Failed to invalidate Redis cache for user {user_id}: {e}")



@router.get("/chats", response_model=ChatHistoryResponse)
async def get_user_chats(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    vector_store: MultiTenantVectorStore = Depends(get_vector_store),
    current_user = Depends(get_current_user)
):
    cache_key = f"chats:{current_user.id}:{limit}:{offset}"
    
    if redis_client:
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                logger.info(f"Cache hit for key {cache_key}")
                return ChatHistoryResponse(**json.loads(cached_data))
        except Exception as e:
            logger.warning(f"Failed to read from Redis cache for key {cache_key}: {e}")

    try:
        chats = vector_store.get_chats_by_user_id(
            user_id=str(current_user.id),
            tenant_id=current_user.tenant_id,
            limit=limit,
            offset=offset
        )

        messages = [ChatMessage(**chat) for chat in chats]
        response = ChatHistoryResponse(
            messages=messages,
            total=len(messages)
        )
        
        if redis_client:
            try:
                # Cache for 5 minutes (300 seconds)
                redis_client.set(cache_key, json.dumps(response.model_dump()), ex=300)
                logger.info(f"Cached chats results in Redis for key {cache_key}")
            except Exception as e:
                logger.warning(f"Failed to write to Redis cache for key {cache_key}: {e}")
                
        return response
    except Exception as e:
        logger.error(f"Error retrieving chat history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat history")


@router.get("/chats/{chat_id}", response_model=ChatHistoryResponse)
async def get_chat_by_id(
    chat_id: str,
    current_user = Depends(get_current_user),
    vector_store: MultiTenantVectorStore = Depends(get_vector_store),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)

):
    """Get all messages for a specific chat ID"""
    try:
        chat_messages = vector_store.get_chat_by_id(
            chat_id=chat_id,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            limit=limit,
            offset=offset
        )

        messages = [ChatMessage(**msg) for msg in chat_messages]
        
        return ChatHistoryResponse(
            messages=messages,
            total=len(messages)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving chat: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat")


@router.delete("/chats/{chat_id}")
async def delete_chat_by_id(
    chat_id: str,
    current_user = Depends(get_current_user),
    vector_store: MultiTenantVectorStore = Depends(get_vector_store)
):
    """Delete a specific chat history by ID"""
    try:
        vector_store.delete_chat(
            chat_id=chat_id,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id
        )
        invalidate_user_chats_cache(str(current_user.id))
        return {"detail": "Chat deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting chat {chat_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete chat")


@router.put("/chats/{chat_id}")
async def rename_chat_by_id(
    chat_id: str,
    request: RenameChatRequest,
    current_user = Depends(get_current_user),
    vector_store: MultiTenantVectorStore = Depends(get_vector_store)
):
    """Rename a specific chat history by ID"""
    try:
        vector_store.rename_chat(
            chat_id=chat_id,
            title=request.title,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id
        )
        invalidate_user_chats_cache(str(current_user.id))
        return {"detail": "Chat renamed successfully"}
    except Exception as e:
        logger.error(f"Error renaming chat {chat_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to rename chat")
