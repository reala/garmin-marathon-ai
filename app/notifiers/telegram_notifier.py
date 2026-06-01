import asyncio
import requests
from app.config import get

_MAX_CHARS = 4096


def _chunk(text: str) -> list[str]:
    """줄바꿈 기준으로 4096자 이하 청크로 분할."""
    if len(text) <= _MAX_CHARS:
        return [text]

    chunks, current = [], []
    current_len = 0

    for line in text.split("\n"):
        line_len = len(line) + 1  # +1 for \n
        if current_len + line_len > _MAX_CHARS and current:
            chunks.append("\n".join(current))
            current, current_len = [], 0
        # 단일 라인이 한도 초과 시 강제 슬라이싱
        if line_len > _MAX_CHARS:
            for i in range(0, len(line), _MAX_CHARS):
                chunks.append(line[i : i + _MAX_CHARS])
        else:
            current.append(line)
            current_len += line_len

    if current:
        chunks.append("\n".join(current))

    return chunks


def send_message(text: str, parse_mode: str = "Markdown") -> None:
    """텔레그램으로 메시지 발송. 4096자 초과 시 자동 분할 발송."""
    token = get("TELEGRAM_BOT_TOKEN")
    chat_id = get("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    for chunk in _chunk(text):
        resp = requests.post(
            url,
            json={"chat_id": chat_id, "text": chunk, "parse_mode": parse_mode},
            timeout=10,
        )
        resp.raise_for_status()


async def send_message_async(text: str, parse_mode: str = "Markdown") -> None:
    """비동기 컨텍스트에서 사용하는 래퍼."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: send_message(text, parse_mode))
