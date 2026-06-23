"""
Infrastructure: python-docx Adapter — implements IDocumentParser
Dịch file Word giữ nguyên format (bold, italic, font size, color, tables)
"""
import logging
from docx import Document
from app.application.ports.document_port import IDocumentParser, DocumentStats
from typing import Callable

logger = logging.getLogger(__name__)


class DocxParser(IDocumentParser):
    """
    Đọc .docx, dịch từng paragraph và cell trong table,
    giữ nguyên style của run đầu tiên.
    """

    def translate_and_save(
        self,
        input_path: str,
        output_path: str,
        translate_fn: Callable[[str], str],
    ) -> DocumentStats:
        doc = Document(input_path)
        total_paragraphs = 0
        total_chars = 0

        # ── Dịch body paragraphs ──
        for para in doc.paragraphs:
            stats = self._translate_paragraph(para, translate_fn)
            total_paragraphs += stats[0]
            total_chars += stats[1]

        # ── Dịch tables ──
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        stats = self._translate_paragraph(para, translate_fn)
                        total_paragraphs += stats[0]
                        total_chars += stats[1]

        doc.save(output_path)
        logger.info(
            f"✅ Đã lưu: {output_path} "
            f"({total_paragraphs} đoạn, {total_chars:,} ký tự)"
        )
        return DocumentStats(
            paragraph_count=total_paragraphs,
            char_count=total_chars,
        )

    @staticmethod
    def _translate_paragraph(para, translate_fn: Callable[[str], str]) -> tuple[int, int]:
        """Dịch một paragraph. Trả về (số đoạn đã dịch, số ký tự)."""
        original = para.text.strip()
        if not original:
            return 0, 0

        try:
            translated = translate_fn(original)
        except Exception as e:
            logger.warning(f"Lỗi dịch đoạn: {e}")
            return 1, len(original)

        # Ghi lại nội dung, giữ style của run đầu tiên
        if para.runs:
            # Lưu style
            first_run = para.runs[0]
            bold = first_run.bold
            italic = first_run.italic
            underline = first_run.underline
            font_name = first_run.font.name
            font_size = first_run.font.size

            # Lấy màu an toàn
            font_color = None
            try:
                if first_run.font.color and first_run.font.color.type:
                    font_color = first_run.font.color.rgb
            except Exception:
                pass

            # Xóa tất cả runs
            for run in para.runs:
                run.text = ""

            # Ghi nội dung dịch vào run đầu tiên
            first_run.text = translated
            first_run.bold = bold
            first_run.italic = italic
            first_run.underline = underline
            if font_name:
                first_run.font.name = font_name
            if font_size:
                first_run.font.size = font_size
            if font_color:
                try:
                    first_run.font.color.rgb = font_color
                except Exception:
                    pass
        else:
            para.text = translated

        return 1, len(original)
