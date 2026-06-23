"""
Infrastructure: Google Translate Adapter — implements ITranslator
Dùng deep-translator (FREE, không cần API key)
"""
import time
import logging
from deep_translator import GoogleTranslator as _GoogleTranslator
from app.application.ports.translator_port import ITranslator

logger = logging.getLogger(__name__)

MAX_CHARS = 4500  # Giới hạn an toàn của Google Translate


class GoogleTranslatorAdapter(ITranslator):
    """FREE adapter — không cần API key, giới hạn ~500k ký tự/ngày."""

    def __init__(self, source: str = "ru", target: str = "vi"):
        self._source = source
        self._target = target

    @property
    def source_lang(self) -> str:
        return self._source

    @property
    def target_lang(self) -> str:
        return self._target

    def translate(self, text: str) -> str:
        if not text or not text.strip():
            return text
        text = text.strip()
        if len(text) <= MAX_CHARS:
            return self._translate_with_retry(text)
        return self._translate_chunked(text)

    def _translate_with_retry(self, text: str, max_retries: int = 3) -> str:
        for attempt in range(max_retries):
            try:
                translator = _GoogleTranslator(source=self._source, target=self._target)
                result = translator.translate(text)
                return result if result else text
            except Exception as e:
                logger.warning(f"Dịch thất bại (lần {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 1s, 2s, 4s
        logger.error("Không thể dịch sau nhiều lần thử. Giữ nguyên bản gốc.")
        return text

    def _translate_chunked(self, text: str) -> str:
        """Chia text dài thành chunks, dịch từng phần."""
        sentences = text.replace("!", ".").replace("?", ".").split(".")
        chunks, current = [], ""

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            if len(current) + len(sentence) + 2 < MAX_CHARS:
                current += sentence + ". "
            else:
                if current:
                    chunks.append(current.strip())
                current = sentence + ". "

        if current:
            chunks.append(current.strip())

        parts = []
        for chunk in chunks:
            parts.append(self._translate_with_retry(chunk))
            time.sleep(0.3)  # Tránh rate limit

        return " ".join(parts)
