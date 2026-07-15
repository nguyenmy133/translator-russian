"""
Infrastructure: Fallback Translator — implements ITranslator
Tự động chuyển sang bộ dịch dự phòng khi bộ dịch chính gặp sự cố.
"""
import logging
from app.application.ports.translator_port import ITranslator

logger = logging.getLogger(__name__)


class FallbackTranslator(ITranslator):
    """
    Bọc hai bộ dịch: primary (Gemini) và fallback (Google Translate).
    Khi primary gặp lỗi (API key hết hạn, bị suspend, lỗi mạng...),
    tự động chuyển sang fallback để đảm bảo khách hàng luôn nhận được bản dịch.
    """

    def __init__(self, primary: ITranslator, fallback: ITranslator):
        self._primary = primary
        self._fallback = fallback
        # Flag đánh dấu khi primary đã fail liên tục, tránh retry vô ích
        self._primary_disabled = False

    @property
    def source_lang(self) -> str:
        return self._primary.source_lang

    @property
    def target_lang(self) -> str:
        return self._primary.target_lang

    def translate(self, text: str) -> str:
        """Dịch đơn lẻ — ưu tiên primary, fallback nếu lỗi."""
        if not text or not text.strip():
            return text

        if self._primary_disabled:
            return self._fallback.translate(text)

        try:
            return self._primary.translate(text)
        except Exception as e:
            logger.warning(
                f"⚠️ Bộ dịch chính (Gemini) gặp sự cố: {e}. "
                f"Tự động chuyển sang Google Translate..."
            )
            self._primary_disabled = True
            return self._fallback.translate(text)

    def translate_batch_xml(self, xml_payload: str) -> str:
        """
        Dịch theo lô XML — chỉ primary (Gemini) hỗ trợ.
        Nếu primary lỗi, ném NotImplementedError để DocxParser tự động
        fallback sang dịch từng đoạn đơn lẻ qua hàm translate().
        """
        if self._primary_disabled:
            raise NotImplementedError(
                "Google Translate (fallback) không hỗ trợ dịch theo lô XML"
            )

        try:
            return self._primary.translate_batch_xml(xml_payload)
        except Exception as e:
            logger.warning(
                f"⚠️ Dịch theo lô bằng Gemini thất bại: {e}. "
                f"DocxParser sẽ chuyển sang dịch từng đoạn qua Google Translate..."
            )
            self._primary_disabled = True
            raise NotImplementedError(
                "Gemini batch XML failed, falling back to single translation"
            )
