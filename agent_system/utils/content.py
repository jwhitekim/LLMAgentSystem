"""
Claude Messages API content 블록 생성 헬퍼.
API 포맷이 바뀌면 여기만 수정한다.
"""


def text_block(text: str) -> dict:
    return {"type": "text", "text": text}


def image_block(data: str, media_type: str = "image/jpeg") -> dict:
    return {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": data}}
