import asyncio
import aiofiles
from typing import Optional


async def read_file_content(file_path: str, encoding: str = "utf-8") -> Optional[str]:
    """Read file content asynchronously"""
    try:
        async with aiofiles.open(file_path, "r", encoding=encoding) as f:
            return await f.read()
    except Exception:
        return None


def detect_encoding(file_path: str) -> str:
    """Detect file encoding (simplified)"""
    # Try common encodings
    for enc in ["utf-8", "gbk", "gb2312", "latin-1"]:
        try:
            with open(file_path, "r", encoding=enc) as f:
                f.read()
                return enc
        except (UnicodeDecodeError, LookupError):
            continue
    return "utf-8"
