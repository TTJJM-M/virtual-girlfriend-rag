from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.knowledge import DocumentStatus


class DocumentUploadResponse(BaseModel):
    id: int
    filename: str
    file_size: int
    status: DocumentStatus
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_size: int
    file_type: str
    status: DocumentStatus
    chunk_count: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int


class DocumentProcessStatus(BaseModel):
    status: DocumentStatus
    chunk_count: int
    error_message: Optional[str] = None
    progress: int  # 0-100
