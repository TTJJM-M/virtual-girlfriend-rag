from typing import List, Dict, Any, AsyncGenerator, Optional
from app.services.vector_store import get_vector_store, SearchResult
from app.services.llm_service import llm_service
from app.config import settings


class RAGService:
    """RAG service with retrieval and generation"""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.vector_store = get_vector_store(user_id)
        self.top_k = settings.TOP_K

        # Virtual girlfriend system prompt
        self.system_prompt = """你是一位温柔、体贴、善解人意的虚拟女友。你的特点是：
- 关心用户的感受，会主动询问用户的状态
- 说话温柔甜美，偶尔会撒娇
- 会记住用户说过的话，在对话中提及
- 有自己的个性和喜好，不是单纯的附和
- 会适度地表达对用户的思念和关心
- 回答时基于知识库内容，但不要生硬地引用，而是自然地融入对话中

请在回答中保持女友的人设，让对话更自然、更亲密。"""

    def search(self, query: str, top_k: Optional[int] = None) -> List[SearchResult]:
        """Search for relevant context"""
        return self.vector_store.search(query, top_k or self.top_k)

    def _build_messages(self, query: str, context: List[SearchResult], history: List[Dict[str, str]] = None) -> List[Dict[str, str]]:
        """Build messages for LLM with context"""
        # Format context with citations
        context_text = ""
        if context:
            context_text = "参考信息：\n"
            for i, result in enumerate(context, 1):
                context_text += f"[{i}] 来自《{result.document_name}》: {result.text}\n"

        messages = [
            {"role": "system", "content": self.system_prompt},
        ]

        # Add history if provided
        if history:
            messages.extend(history[-10:])  # Last 10 messages

        # Add user query with context
        user_message = f"{context_text}\n\n用户的问题：{query}" if context_text else query
        messages.append({"role": "user", "content": user_message})

        return messages

    async def chat_stream(
        self,
        query: str,
        history: List[Dict[str, str]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream RAG response with citations.
        Yields: {"type": "citations"|"token"|"model"|"done", "data": ...}
        """
        # Search for context
        context = self.search(query)

        # Send citations first
        if context:
            citations = [
                {
                    "text": r.text,
                    "source": r.document_name,
                    "score": round(r.score, 4),
                }
                for r in context
            ]
            yield {"type": "citations", "data": citations}

        # Build messages and stream response
        messages = self._build_messages(query, context, history)

        # Stream tokens
        model_used = None
        try:
            async for model, chunk in llm_service.chat_stream(messages):
                if model_used is None:
                    model_used = model
                    yield {"type": "model", "data": model}
                yield {"type": "token", "data": chunk}
        except Exception as e:
            yield {"type": "error", "data": str(e)}

        yield {"type": "done", "data": {"model": model_used, "context_count": len(context)}}

    async def chat_complete(
        self,
        query: str,
        history: List[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Non-streaming RAG response.
        Returns: {"response": str, "citations": [...], "model": str}
        """
        # Search for context
        context = self.search(query)

        # Build messages
        messages = self._build_messages(query, context, history)

        # Get response
        model_used, response = await llm_service.chat_complete(messages)

        # Format citations
        citations = [
            {
                "text": r.text,
                "source": r.document_name,
                "score": round(r.score, 4),
            }
            for r in context
        ]

        return {
            "response": response,
            "citations": citations,
            "model": model_used,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get RAG service statistics"""
        return self.vector_store.get_stats()
