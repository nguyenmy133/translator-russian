"""
Infrastructure: Gemini API Adapter — implements ITranslator
Sử dụng urllib để gọi trực tiếp Gemini API (không cần cài thêm thư viện phụ thuộc).
"""
import json
import logging
import time
import urllib.request
import urllib.error
from app.application.ports.translator_port import ITranslator

logger = logging.getLogger(__name__)


class GeminiTranslatorAdapter(ITranslator):
    """
    Adapter sử dụng Gemini 2.5 Flash API để dịch thuật chất lượng cao.
    Có System Prompt giúp định hướng dịch thuật tài chính và bảo toàn thẻ HTML.
    """

    def __init__(self, api_key: str, source: str = "ru", target: str = "vi"):
        self._api_key = api_key
        self._source = source
        self._target = target
        self._model = "gemini-2.5-flash"

    @property
    def source_lang(self) -> str:
        return self._source

    @property
    def target_lang(self) -> str:
        return self._target

    def translate(self, text: str) -> str:
        """Dịch đơn lẻ một đoạn văn bản sử dụng Gemini API."""
        if not text or not text.strip():
            return text

        if not self._api_key:
            logger.error("❌ GEMINI_API_KEY chưa được cấu hình! Giữ nguyên bản gốc.")
            return text

        # Tạo prompt dịch thô cho 1 đoạn văn bản
        system_instruction = (
            f"Bạn là một biên dịch viên chuyên ngành tài chính và giao dịch ngoại hối (Forex).\n"
            f"Hãy dịch văn bản sau từ tiếng {self._source.upper()} sang tiếng {self._target.upper()}.\n"
            f"Đảm bảo dịch thuật tự nhiên, sử dụng thuật ngữ tài chính chuyên ngành chính xác.\n"
            f"TUYỆT ĐỐI không thay đổi, chỉnh sửa hay làm mất bất kỳ thẻ HTML nào (như <span>, <u>, <div>...) và giữ nguyên các thuộc tính của chúng."
        )

        return self._call_gemini_api_with_retry(text, system_instruction)

    def translate_batch_xml(self, xml_payload: str) -> str:
        """
        Dịch gộp cấu trúc XML/HTML chứa các đoạn văn.
        Được sử dụng bởi DocxParser để giảm số lượng API calls và tăng tốc độ.
        """
        if not self._api_key:
            logger.error("❌ GEMINI_API_KEY chưa được cấu hình! Giữ nguyên bản gốc.")
            return xml_payload

        system_instruction = (
            f"Bạn là một chuyên gia biên dịch tài liệu tài chính từ tiếng {self._source.upper()} sang tiếng {self._target.upper()}.\n"
            f"Văn bản đầu vào được đóng gói trong các thẻ XML/HTML.\n"
            f"Nhiệm vụ của bạn:\n"
            f"1. Dịch phần văn bản hiển thị bên trong các thẻ XML/HTML (như <u> và <span>).\n"
            f"2. TUYỆT ĐỐI GIỮ NGUYÊN cấu trúc XML/HTML, tên thẻ (u, span, div...), thuộc tính thẻ (như i, id...) và vị trí thẻ.\n"
            f"3. Chỉ trả về chuỗi XML kết quả được dịch, không kèm bất kỳ giải thích nào khác ngoài XML."
        )

        # Loại bỏ các ký tự bọc markdown codeblock nếu Gemini tự ý thêm vào
        raw_result = self._call_gemini_api_with_retry(xml_payload, system_instruction)
        clean_result = raw_result.strip()
        if clean_result.startswith("```"):
            # Bỏ dòng ```xml hoặc ```html
            lines = clean_result.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            clean_result = "\n".join(lines).strip()
            
        return clean_result

    def _call_gemini_api_with_retry(self, prompt: str, system_instruction: str, max_retries: int = 3) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self._model}:generateContent?key={self._api_key}"

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "safetySettings": [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]
        }
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        data = json.dumps(payload).encode("utf-8")

        for attempt in range(max_retries):
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            try:
                # Thiết lập timeout 45 giây cho tài liệu dài
                with urllib.request.urlopen(req, timeout=45) as response:
                    res_data = json.loads(response.read().decode("utf-8"))
                    text_out = res_data["candidates"][0]["content"]["parts"][0]["text"]
                    return text_out
            except urllib.error.HTTPError as e:
                status_code = e.code
                error_body = e.read().decode("utf-8", errors="ignore")
                logger.warning(
                    f"⚠️ Lỗi HTTP gọi Gemini API (Lần {attempt+1}/{max_retries}): "
                    f"Code {status_code}. Chi tiết: {error_body}"
                )
                
                # Lỗi xác thực/phân quyền/cấu hình → ném lỗi ngay, không retry
                if status_code in (400, 401, 403):
                    raise RuntimeError(
                        f"Gemini API lỗi xác thực/cấu hình (HTTP {status_code}): {error_body}"
                    )

                # Nếu bị rate limit (429), ngủ lâu hơn để hồi phục
                if status_code == 429:
                    sleep_time = 10 * (attempt + 1)
                    logger.info(f"⏳ Bị giới hạn tần suất (Rate Limit 429). Ngủ {sleep_time}s trước khi thử lại...")
                    time.sleep(sleep_time)
                else:
                    time.sleep(2 ** attempt)
            except RuntimeError:
                # Để RuntimeError từ khối trên đi qua, không bắt lại
                raise
            except Exception as e:
                logger.error(f"❌ Lỗi kết nối Gemini API (Lần {attempt+1}/{max_retries}): {e}")
                time.sleep(2 ** attempt)

        raise RuntimeError(
            f"Không thể kết nối Gemini API sau {max_retries} lần thử."
        )
