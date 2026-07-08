import json
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_async_db
from app.models.session import ChatSession, Message
from app.models.user import User
from app.core.deps import get_current_active_user
from app.schemas.chat import ChatRequest
from app.services.rag_service import RAGService
from typing import Annotated, AsyncGenerator
import asyncio

router = APIRouter(prefix="/api/chat", tags=["聊天"])


async def generate_stream(
    session_id: int,
    user_message: str,
    current_user: User,
    db: AsyncSession,
) -> AsyncGenerator[str, None]:
    """Generate SSE stream for chat response"""

    # Create user message record
    user_msg = Message(
        session_id=session_id,
        role="user",
        content=user_message,
    )
    db.add(user_msg)
    await db.commit()
    await db.refresh(user_msg)

    # Create RAG service
    rag = RAGService(user_id=current_user.id)

    # Get session history (last 10 messages for context)
    history_result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .where(Message.id != user_msg.id)
        .order_by(Message.created_at.desc())
        .limit(10)
    )
    history = [
        {"role": m.role, "content": m.content}
        for m in reversed(history_result.scalars().all())
    ]

    # Stream response
    assistant_content = ""
    citations = None
    model_used = None

    try:
        async for event in rag.chat_stream(query=user_message, history=history):
            event_type = event.get("type")
            data = event.get("data")

            if event_type == "citations":
                citations = data
                yield f"data: {json.dumps({'type': 'citations', 'data': data}, ensure_ascii=False)}\n\n"

            elif event_type == "model":
                model_used = data
                yield f"data: {json.dumps({'type': 'model', 'data': data}, ensure_ascii=False)}\n\n"

            elif event_type == "token":
                assistant_content += data
                yield f"data: {json.dumps({'type': 'token', 'data': data}, ensure_ascii=False)}\n\n"

            elif event_type == "error":
                yield f"data: {json.dumps({'type': 'error', 'data': data}, ensure_ascii=False)}\n\n"

            elif event_type == "done":
                # Save assistant message to database
                assistant_msg = Message(
                    session_id=session_id,
                    role="assistant",
                    content=assistant_content,
                    citations=citations,
                )
                db.add(assistant_msg)
                await db.commit()

                # Update session updated_at
                session_result = await db.execute(
                    select(ChatSession).where(ChatSession.id == session_id)
                )
                session = session_result.scalar_one_or_none()
                if session:
                    session.title = session.title or user_message[:20]
                    await db.commit()

                yield f"data: {json.dumps({'type': 'done', 'data': {'model': model_used}}, ensure_ascii=False)}\n\n"

            await asyncio.sleep(0)  # Yield control to event loop

    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'data': str(e)}, ensure_ascii=False)}\n\n"

    yield "data: [DONE]\n\n"


@router.post("/{session_id}")
async def chat(
    session_id: int,
    req: ChatRequest,
    request: Request,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_async_db)],
):
    """
    发送消息并获取流式响应（SSE）
    """
    # Verify session exists and belongs to user
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

    return StreamingResponse(
        generate_stream(session_id, req.message, current_user, db),
        media_type="text/event-stream",
    )
