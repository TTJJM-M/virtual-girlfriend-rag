from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.database import get_async_db
from app.models.session import ChatSession, Message
from app.models.user import User
from app.core.deps import get_current_active_user
from app.schemas.chat import ChatSessionCreate, ChatSessionResponse, ChatMessageResponse, ChatRequest
from typing import Annotated, List

router = APIRouter(prefix="/api/sessions", tags=["会话管理"])


@router.get("", response_model=List[ChatSessionResponse])
async def get_sessions(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_async_db)],
):
    """获取当前用户的所有会话"""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .where(ChatSession.is_deleted == False)
        .order_by(ChatSession.updated_at.desc())
    )
    sessions = result.scalars().all()

    # Get message counts
    response = []
    for session in sessions:
        msg_result = await db.execute(
            select(func.count(Message.id)).where(Message.session_id == session.id)
        )
        count = msg_result.scalar() or 0
        resp = ChatSessionResponse(
            id=session.id,
            user_id=session.user_id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=count,
        )
        response.append(resp)

    return response


@router.post("", response_model=ChatSessionResponse)
async def create_session(
    req: ChatSessionCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_async_db)],
):
    """创建新会话"""
    session = ChatSession(
        user_id=current_user.id,
        title=req.title or "新对话",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return ChatSessionResponse(
        id=session.id,
        user_id=session.user_id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=0,
    )


@router.delete("/{session_id}")
async def delete_session(
    session_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_async_db)],
):
    """删除会话（软删除）"""
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    session.is_deleted = True
    await db.commit()

    return {"message": "会话已删除"}


@router.get("/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_messages(
    session_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_async_db)],
):
    """获取会话消息历史"""
    # Verify session belongs to user
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id,
            ChatSession.is_deleted == False,
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    # Get messages
    msg_result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
    )
    messages = msg_result.scalars().all()

    return [
        ChatMessageResponse(
            id=m.id,
            session_id=m.session_id,
            role=m.role,
            content=m.content,
            citations=m.citations,
            created_at=m.created_at,
        )
        for m in messages
    ]
