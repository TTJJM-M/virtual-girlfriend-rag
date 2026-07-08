from pydantic_settings import BaseSettings
from typing import Optional, List
from dataclasses import dataclass, field
import threading


@dataclass
class ModelQuota:
    """Model quota tracking"""
    model: str
    priority: int  # lower = higher priority
    free_quota_remaining: int = 1000000  # assume plenty initially
    is_exhausted: bool = False
    error_count: int = 0
    last_error_at: float = 0
    requests_today: int = 0


@dataclass
class ModelPool:
    """Thread-safe model pool with automatic failover"""
    embedding_models: List[ModelQuota] = field(default_factory=list)
    llm_models: List[ModelQuota] = field(default_factory=list)
    _lock = threading.Lock()

    def __post_init__(self):
        # Embedding models - text-embedding-v3 is primary
        self.embedding_models = [
            ModelQuota(model="text-embedding-v3", priority=1),
            ModelQuota(model="text-embedding-v2", priority=2),
        ]
        # LLM models - qwen-max as primary with fallback
        self.llm_models = [
            ModelQuota(model="qwen-max", priority=1),
            ModelQuota(model="qwen-plus", priority=2),
            ModelQuota(model="qwen-turbo", priority=3),
        ]

    def get_available_embedding_model(self) -> str:
        """Get next available embedding model"""
        with self._lock:
            for mq in self.embedding_models:
                if not mq.is_exhausted:
                    return mq.model
            # All exhausted, return highest priority anyway
            return self.embedding_models[0].model

    def get_available_llm_model(self) -> str:
        """Get next available LLM model"""
        with self._lock:
            for mq in self.llm_models:
                if not mq.is_exhausted:
                    return mq.model
            # All exhausted, return highest priority anyway
            return self.llm_models[0].model

    def mark_error(self, model: str, error_type: str = "unknown"):
        """Mark model error, potentially exhausting quota"""
        with self._lock:
            for mq in self.embedding_models + self.llm_models:
                if mq.model == model:
                    mq.error_count += 1
                    mq.last_error_at = threading.Event().wait
                    # Insufficient quota or rate limit errors
                    if "quota" in error_type.lower() or "rate" in error_type.lower() or "429" in error_type:
                        mq.is_exhausted = True
                        print(f"⚠️  Model {model} marked as exhausted (error: {error_type})")
                    break

    def reset_model(self, model: str):
        """Manually reset a model's exhausted status"""
        with self._lock:
            for mq in self.embedding_models + self.llm_models:
                if mq.model == model:
                    mq.is_exhausted = False
                    mq.error_count = 0
                    mq.free_quota_remaining = 1000000
                    print(f"✓ Model {model} reset")
                    break

    def get_status(self) -> dict:
        """Get pool status"""
        with self._lock:
            return {
                "embedding": [
                    {"model": mq.model, "priority": mq.priority, "exhausted": mq.is_exhausted, "errors": mq.error_count}
                    for mq in self.embedding_models
                ],
                "llm": [
                    {"model": mq.model, "priority": mq.priority, "exhausted": mq.is_exhausted, "errors": mq.error_count}
                    for mq in self.llm_models
                ],
            }


class Settings(BaseSettings):
    # App
    APP_NAME: str = "虚拟女友 RAG 知识库"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""  # Set in .env
    DB_NAME: str = "virtual_girlfriend"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # DashScope API
    DASHSCOPE_API_KEY: str = ""  # Set in .env
    DASHSCOPE_EMBEDDING_MODEL: str = "text-embedding-v3"
    DASHSCOPE_LLM_MODEL: str = "qwen-max"
    DASHSCOPE_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # JWT
    SECRET_KEY: str = "change-me-in-production"  # Set in .env
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # File Upload
    MAX_UPLOAD_SIZE: int = 20 * 1024 * 1024  # 20MB
    UPLOAD_DIR: str = "data/uploads"
    VECTOR_STORE_DIR: str = "data/vector_store"

    # RAG
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    TOP_K: int = 3

    # Rate Limit
    RATE_LIMIT_USER: int = 30  # per minute
    RATE_LIMIT_ADMIN: int = 100  # per minute

    # Admin
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "123456"

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
model_pool = ModelPool()
